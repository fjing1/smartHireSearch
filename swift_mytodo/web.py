import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime

bucket_name = "swift-hire-felix-kelly-us-west-2"

def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id='AKIA5FTZC7FQDRFCWX4V',
                      aws_secret_access_key='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')

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

def main():
    st.title('Resume Uploader')
    st.write('Upload your resume in PDF format and we will store it in our AWS S3 Bucket!')

    first_name = st.text_input('First Name')
    last_name = st.text_input('Last Name')
    target_title = st.text_input('Target title, such as sde, ds, da, de').lower()
    target_location = st.text_input("Target cities, such as Toronto, Vancouver, Montreal, etc").lower()
    email = st.text_input("Enter the email you want to receive job apply links").lower()
    # TODO: 
    # salary expectation
    # location
    # highest education?
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    if uploaded_file is not None and first_name and last_name:
        with open("temp_file.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        if st.button('Submit'):
            #timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            s3_filename = f"{first_name}_{last_name}_{target_title}_{target_location}_{email}.pdf"
            upload_to_aws('temp_file.pdf', bucket_name, s3_filename)
            st.success("Your resume has been uploaded successfully!")

if __name__ == "__main__":
    main()
