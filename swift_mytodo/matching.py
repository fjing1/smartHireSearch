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


# # Summary [PART 2]: 
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
# import cdata.elasticsearch as mod 
# get data from elastic search

from opensearchpy import OpenSearch, helpers

import glob  
import re
 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail 

from IPython.display import display

import resume_summary
import utils

def get_job_data_from_opensearch(job_index_name = 'swift_dev_felix_kelly_jo' ): 
    """
    input:
    job_index_name = 'swift_dev_felix_kelly'

    output:
    get latest job data from opensearch, job_index_name.
    
    """
    host = utils.load_specific_api_key(filename='credential.txt', key_name='opensearch_host') 
    port = 443
    auth = ('swift', 'Hire123!') # For testing only. Don't store credentials in code.
    
    print('connect to OpenSearch client: ')
    client = OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
        timeout = 120, # increase this for 3220 files
        #connection_class=RequestsHeepConnection
        )

    # # warning: job_size need to check 
    job_result = client.search(index=job_index_name, scroll = '3m', size = 3220, body={"query": {"match_all": {}}})  
    print("Total documents:", job_result['hits']['total']['value'])
    
    jobs_df = pd.DataFrame([job['_source'] for job in job_result['hits']['hits']])
    print(f'check whole jobs_df shape {jobs_df.shape}')

    # warning: will need a specific way to get lastest 24hr jobs 
    latest_jobs_df = jobs_df.head(100)  
    print('Got latest job data from ES. Done.')
    return latest_jobs_df


def extract_email_regex(list_of_strings):
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for string in list_of_strings:
        if re.search(email_pattern, string):
            return re.search(email_pattern, string).group()
 

def matching(loader, resume_summary):  
    """
    input:
    loader - loader for specific data format.
    resume_summary: summary string text 

    Given each resume_summary, provide job recommendation based on LLM.
    
    output:
    send top recommendated job links to job seeker via email campaign.
    
    """
    resume_summary_formatted = "\n".join(resume_summary)
    print(f"--------------------Formatted Resume Summary:--------------------\n {resume_summary_formatted} \n ************************") 
    
    rag_chain = resume_summary.rag_invoke(job_loader)   
    
    joblink = rag_chain.invoke("  Given a summary from a resume represented by" + resume_summary_formatted + 
    '''identify and rank the TOP 3 job postings that are the best match based on the following criteria:
Exact Match on Job Title: The job title in the job posting must match 100% with the job title or role being sought as mentioned in the {resume_summary}. This is a critical requirement, and only job postings with a title that exactly matches should be considered for the TOP 3.
Recency of the Job Posting: Preference is given to the most recent job listings found in their metadata.
Similarity in Job Skills: The job listing must have skill requirements that closely match the skills listed in the {resume_summary}.
Matching Desired Job Location: The location mentioned in the job posting should match the desired job location specified in the {resume_summary}.
For each of the TOP 3 matches, structure the output as follows, providing the job title and the company name, followed by the phrase "Apply on:" and then the direct link to the job application or job posting (applyLink):
1. Job Title at Company Name - Apply on: [link]
2. Job Title at Company Name - Apply on: [link]
3. Job Title at Company Name - Apply on: [link] '''
    )  
    # print(f' links: {joblink}')  
    job_list = joblink.split('\n')
    print(f'\nCHECK {len(job_list)} job_list: \n{job_list}\n') 

    resume_email = extract_email_regex(resume_summary) 
    print(f'\nCHECK resume_email: {resume_email}\n')
    return resume_email, job_list


def send_job_recommendations(emails, job_links,email_api_key):
    job_links = job_links.replace('\n', '<br>') # HTML tag for a line break
    message = Mail(
        from_email='f2jing@uwaterloo.ca',
        to_emails=emails,
        subject='SWIFTHIRE Job Recommendations for You',
        #print(tyoe(jo
        html_content=f"""
        <p>Hi there,</p>
        <p>We've found some job opportunities that match your resume well:</p>
        <ul>
        """ + job_links + """
        </ul>
        <p>Best of luck with your job search!</p>
        <p>Best regards,</p>
        <p>Your Name</p>
        """
    )
    try:
        sg = SendGridAPIClient(email_api_key)
        response = sg.send(message)
        print(f"\n\n---------------------Email sent! Status code: {response.status_code} -----------------------\n")
    except Exception as e:
        print(f"An error occurred: {e}")


  

if __name__ == "__main__":
    # get job data 
    latest_jobs_df = get_job_data_from_opensearch() 
    latest_jobs_df.to_csv('./data/placeholder_resume_job/latest_jobs_df.csv', index=False)  # need to create dir: placeholder_resume_job
    latest_jobs_df.head(1) 

    # get resume data
    all_resume_df = pd.read_csv('./data/placeholder_resume_job/all_resume_df.csv') 

 
    # run LLM matching between resume and jobs  
    job_loader = CSVLoader(file_path='./data/placeholder_resume_job/latest_jobs_df.csv')

    for resume_summary in all_resume_df['summary'].tolist() : 
        
        resume_email, joblinks = matching(job_loader, resume_summary) 
        # rm square brackets comes with the list
        email_api = utils.load_specific_api_key(filename='credential.txt', key_name='email_api_key')
        joblinks_clickable = '\n'.join(joblinks)
        send_job_recommendations(resume_email, joblinks_clickable, email_api) 
        
        #print(resume_email, joblinks_clickable)


