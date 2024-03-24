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

import glob  
import re

from IPython.display import display


import ast

def load_specific_api_key(filename='credential.txt', key_name='openai_api_key'):
    """
    Load a specific API key from a file containing a dictionary of keys.
    
    :param filename: The name of the file to read.
    :param key_name: The specific key of the API key to retrieve. ex: openai_api_key, email_api_key, aws_access_key_id, aws_secret_access_key. 
    :return: The API key value, or None if not found.
    """
    try:
        with open(filename, 'r') as file:
            # Read the contents of the file
            file_contents = file.read()
            # Safely evaluate the string as a Python dictionary
            credentials_dict = ast.literal_eval(file_contents)
            # Extract and return the specific API key
            return credentials_dict.get(key_name)
    except FileNotFoundError:
        print("The credentials file was not found.")
    except SyntaxError as e:
        print(f"Syntax error in the credentials file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None  # Return None if there was an issue



def rag_invoke(loader) :
    """ 
    input: 
    need to have loader for corresponded doc format, ex: 
    loader = PyPDFLoader(pdf) 

    output: create rag_chain
    """ 
    pages = loader.load_and_split()
    faiss_index = FAISS.from_documents(pages, OpenAIEmbeddings())
    retriever = faiss_index.as_retriever() 

    rag_chain = (
    {"context": retriever | format_docs,
    "question": RunnablePassthrough() }
    | prompt
    | lm
    | StrOutputParser()
    )
    return rag_chain


def create_opensearch_client():
    """ 
    Create and return an OpenSearch client.
    """
    host = 'search-swift-hire-dev-jfmldmym4cfbiwdhwmtuqq6ihy.us-west-2.es.amazonaws.com'
    port = 443
    auth = ('swift', 'Hire123!') # For testing only. Don't store credentials in code.
    
    print('Connect to OpenSearch client: ')
    client = Elasticsearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
    )
    return client















