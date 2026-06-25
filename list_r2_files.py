import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_r2_objects():
    # Fetch credentials
    access_key = os.getenv('R2_ACCESS_KEY_ID')
    secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('R2_BUCKET_NAME')
    endpoint_url = os.getenv('R2_ENDPOINT_URL')
    
    if not all([access_key, secret_key, bucket_name, endpoint_url]):
        print("Error: Missing R2 credentials in .env file")
        return

    # Create S3 client for R2
    s3 = boto3.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto'  # R2 uses 'auto'
    )

    try:
        print(f"Listing objects in bucket: {bucket_name}")
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            print(f"{'Key':<50} | {'Size (KB)':<10} | {'Last Modified'}")
            print("-" * 85)
            for obj in response['Contents']:
                size_kb = round(obj['Size'] / 1024, 2)
                last_modified = obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
                print(f"{obj['Key']:<50} | {size_kb:<10} | {last_modified}")
        else:
            print("No objects found in the bucket.")
            
    except Exception as e:
        print(f"Error listing R2 objects: {e}")

if __name__ == "__main__":
    list_r2_objects()
