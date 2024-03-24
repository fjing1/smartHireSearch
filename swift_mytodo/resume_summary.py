# !pip install langchain
# !pip install PyPDFLoader
# !pip install langchainhub 
# ! pip install pypdf
# ! pip install langchain_community
# ! pip install langchain
# ! pip install langchain_openai
# ! pip install faiss-cpu
# ! pip install langchainhub
# ! pip install -U langchain-openai
#! pip install petl 
# ! pip install cdata
# ! pip install elasticsearch-dsl 
# ! pip install -r requirements.txt 
#! pip install sendgrid
# !pip install re


# # Summary [PART 1]: 
# 1. resume etl 
#     - get resume from S3
#     - processing resume as summary along with personal preference 
#     - processed resume to opensearch
# 2. matching etl
#     - get job and resume data from opensearch
#     - get job and resume match
#     - send job recommendations via email to job seeker  

# normal trigger: 
# - job scraping: every 24 hr.
# - resume preprocessing: when new resume add to s3, preprocess resume and save to ES. 
# - llm matching: every 24 hr.

# demo trigger:
# - resume preprocessing + llm matching:   when new resume add to s3. 


import pandas as pd
import re
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough 
from langchain_community.document_loaders.csv_loader import CSVLoader

import boto3
import os 
import petl as etl
import pandas as pd 

from opensearchpy import OpenSearch, helpers
from IPython.display import display

import glob  
import re 

import utils 


def save_data_to_opensearch(index_name, data_df):
    """ 
    index_name
    example: 
    - "swift_dev_felix_kelly" : job 
    - "swift_dev_felix_kelly_resume" : resume summary with personal preference data 

    data_df
    example:
    - processed resume data
    - processed job data 

    output: save the data_df into ES as index_name 
    """
    client = utils.create_opensearch_client()

    print(f'index_name: {index_name}') 
    
    if not client.indices.exists(index_name):
        print(f'Create index_name: {index_name}') 
        client.indices.create(index=index_name)
        
    def doc_generator(df):
        for i, row in df.iterrows():
            doc = {
                "_index": index_name,
                "_source": row.to_dict(),
            }
            yield doc
         
    helpers.bulk(client, doc_generator(data_df)) 
    
    print("Data Saved to ES. Done.") 



def resume_from_S3(bucket_name ='swift-hire-felix-kelly-us-west-2' , local_s3_resume_path='./data/s3_resumes/'):
    """
    input: specific S3 bucket_name that has resume pdf
    - bucket_name: 'swift-hire-kelly-liu'  
    - local_s3_resume_path: './data/s3_resumes/' ----> need to create s3_resumes folder

    output: save S3 resumes to local  
    """
    # Create an S3 client
    s3 = boto3.client('s3') 
    bucket_name = 'swift-hire-felix-kelly-us-west-2'   
    prefix = ''     
     
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)  
    
    if 'Contents' in response:
        for obj in response['Contents']:  
            if 'pdf' in obj['Key']:
                file_key = obj['Key']
                # Specify the local path to save the downloaded file
                local_file_name = os.path.join(local_s3_resume_path , file_key)  # Update this to where you want to save the file
                 
                s3.download_file(bucket_name, file_key, local_file_name)
                
                print(f"File {file_key} downloaded to {local_file_name}")
    print('Successfully downloaded S3 resume to local.')


def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)
    

def resume_summary(pdf): 
    """
    input: 
    pdf: resume path 

    create rag_invoke on pdf loader. 

    output:
    resume summary text by rag_chain.invoke
    
    """
    print(f'Summary Resume: {pdf}\n') 
    loader = PyPDFLoader(pdf) 
    rag_chain = utils.rag_invoke(loader) 
    
    summary = rag_chain.invoke("""  
    Structure background by filling in the section below from the Resume
    - Name (with first and last name):
    - Email (contact info): 
    - Best Matching Job Positions (for example "Data Engineer", "Product Manager", etc) rank from best fit to less fit:
    - Top Skills he/she has (tile to 20):
    - Industries (Like Retail, Tech, Consulting, Government, Finance, etc.):
    - Years of Experience (estimate if not specified. for example: don't print Internship experience since 2021, print 3 years. ):
    - Location (please be valid City, Country, if it is not valid one just don't included, for example: Meta (Ads Infra and Ranking) is not a location):
    - Full Experience (including everything):
        
    """
    )  
    # print('summary: ', s) 
    return summary
    

def extract_personal_preference(path):
    """ 
    input : path1 = './data/s3_resumes/FelixJing_sde_toronto_fjing007@gmail.com.pdf'
    output: Desired Position: sde, Desired Location: toronto
    """ 
    parts = path.split('/') 
    info_parts = parts[-1].split('_') 
    position = info_parts[1]
    location = info_parts[2]
    
    personal_preference = f",\n Desired Position: {position},\n Desired Location: {location}"
    # print(f'\npersonal_preference: {personal_preference}')
    return personal_preference


def resume_summary_to_df(summary, pdf):
    """
    input: 
    summary: summary of resume text 
    pdf: resume path that show file name, where we extra personal preference info

    output: df of resume summary  
    
    """ 
    personal_preference = extract_personal_preference(pdf)  
    input_string = summary + personal_preference  
    parts = input_string.split('\n') 
     
    data_dict = {}
    data_dict['summary'] = parts 
    df_temp = pd.DataFrame([data_dict])
    # display(df_temp)
    return df_temp

def llm_resume_preprocess(local_s3_resume_path = './data/s3_resumes/' ):
    """
    input:
    local_s3_resume_path = './data/s3_resumes/'

    output: get df that has all resumes summary 
    
    """
    # get resume from local 
    pattern = os.path.join(local_s3_resume_path, '*.pdf')  
    resume_files = glob.glob(pattern) 
    print(f"Found {len(resume_files)} Resumes:", resume_files)

    # loop through all resume and put into all_resume_df
    all_resume_df = pd.DataFrame()  
         
    # get resume summary to df 
    for pdf in resume_files:  
        summary = resume_summary(pdf) 
        resume_df_temp = resume_summary_to_df(summary,pdf)
        all_resume_df = pd.concat([all_resume_df, resume_df_temp], ignore_index=True)
    print(f'Processed all {len(all_resume_df)} resumes. Done.\n') 
    display(all_resume_df.head())
    
    return all_resume_df


def main():
    resume_from_S3()  
    # use llm to summary resume
    os.environ['OPENAI_API_KEY'] = utils.load_specific_api_key(filename='credential.txt', key_name='openai_api_key') 

    prompt = hub.pull("rlm/rag-prompt")
    lm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    all_resume_df = llm_resume_preprocess()
    all_resume_df.to_csv('./data/placeholder_resume_job/all_resume_df.csv', index=False) 

    save_data_to_opensearch('swift_dev_felix_kelly_resume', all_resume_df)


# For demo purpose: when there is change in s3 bucket, we run this main
@app.on_s3_event(bucket=utils.load_specific_api_key(filename='credential.txt', key_name='s3_bucket_felix') ,
                 events=['s3:ObjectCreated:*'])
if __name__ == "__main__":
    main()






 


    








