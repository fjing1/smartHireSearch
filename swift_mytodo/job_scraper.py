import os
import boto3
from chalice import Chalice, AuthResponse, Rate
from chalicelib import auth, db
import pandas as pd
from apify_client import ApifyClient
from datetime import datetime
from opensearchpy import OpenSearch, helpers
import utils
app = Chalice(app_name='mytodo')
app.debug = True
_DB = None
_USER_DB = None
apify_client = ApifyClient(utils.load_specific_api_key(filename='credential.txt', key_name='apify_client_apikey') ) 

# Define locations as a global variable
locations = {"w+CAIQICIHVG9yb250bw==": "Toronto", "w+CAIQICIJVmFuY291dmVy": "Vancourver", "w+CAIQICIITW9udHJlYWw=": "Montreal"}

def get_job_data(uule, jt):
    run_input = {
        "csvFriendlyOutput": True,
        "includeUnfilteredResults": False,
        "maxConcurrency": 10,
        "maxPagesPerQuery": 3,
        "queries": f"https://www.google.com/search?ibp=htl;jobs&q={jt}&uule={uule}",
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
    }

    actor_call = apify_client.actor('dan.scraper/google-jobs-scraper').call(run_input=run_input)
    dataset_items = apify_client.dataset(actor_call['defaultDatasetId']).list_items().items

    d = pd.DataFrame(dataset_items)
    d["query"] = jt
    d["location"] = locations[uule]
    d["run_time"] = str(datetime.now())

    return d

def save_to_es(df):
    host = 'search-swift-hire-dev-jfmldmym4cfbiwdhwmtuqq6ihy.us-west-2.es.amazonaws.com' #put your host here
    port = 443
    auth = ('swift', 'Hire123!') # For testing only. Don't store credentials in code.

    client = OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
    )

    index_name = "swift_dev_felix_kelly_jobposts"

    if not client.indices.exists(index_name):
        client.indices.create(index=index_name)

    def doc_generator(df):
        for i, row in df.iterrows():
            doc = {
                "_index": index_name,
                "_source": row.to_dict(),
            }
            yield doc

    helpers.bulk(client, doc_generator(df))

    print("Data Saved to Elastic Search dashboard Done.")
    
# for demo purpose, s3 bucket change
# for regular routine use 
# @app.schedule(Rate(24, unit=Rate.HOURS))
@
def every_24_hour(event):
    position_df = pd.DataFrame()
    job_titles = ["Software Engineer",  "Data Engineer", "Data Scientist"]

    for uule in locations:
        print(locations[uule])
        for jt in job_titles:
            print(jt)
            d = get_job_data(uule, jt)
            position_df = pd.concat([position_df, d])

        print("="*30)

    position_df.drop(columns='thumbnail', inplace=True)
    print("start the openserach part")
    save_to_es(position_df)

every_24_hour()