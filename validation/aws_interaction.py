import boto3
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

def download_json_from_s3(bucket_name, file_key):
    try:
        # Download the file from S3
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        
        # Read the content and parse it as JSON
        content = response['Body'].read().decode('utf-8')
        json_data = json.loads(content)
        
        return json_data
    except Exception as e:
        print(f"Error downloading or parsing JSON from S3: {str(e)}")
        return {}

def upload_json_to_s3(bucket_name, file_key, json_data):
    try:
        # Convert JSON data to a string and upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=json.dumps(json_data),
            ContentType='application/json'
        )
        print(f"Uploaded JSON to S3 bucket {bucket_name} with key {file_key}")
        
        # Construct the direct file URL
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
        return file_url
    except Exception as e:
        print(f"Error uploading JSON to S3: {str(e)}")

# Example usage
if __name__ == "__main__":
    bucket_name = 'vanatensorpoisondata'
    file_key = 'poisin.json'
    
    result = download_json_from_s3(bucket_name, file_key)
    if result:
        print("Successfully downloaded and parsed JSON:")
        print(json.dumps(result, indent=2))
    else:
        print("Failed to download or parse JSON from S3")
