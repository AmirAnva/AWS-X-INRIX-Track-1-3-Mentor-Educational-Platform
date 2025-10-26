import boto3
import dotenv
from botocore.exceptions import ClientError
import os

dotenv.load_dotenv()

access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

BUCKET_NAME = "mntrai-transcribe-bucket"

s3 = boto3.client(
    service_name="s3",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name="us-east-1",
)

transcribe = boto3.client(
    service_name="transcribe",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name="us-east-1",
)

bedrock = boto3.client(
    service_name="bedrock-runtime",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name="us-east-1",
)

def create_bucket_if_not_exists():
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket {BUCKET_NAME} already exists.")
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            s3.create_bucket(Bucket=BUCKET_NAME)
            print(f"Bucket {BUCKET_NAME} created.")
        else:
            raise

def upload_file_to_s3(file_name, object_name):
    try:
        s3.upload_file(file_name, BUCKET_NAME, object_name)
        print(f"File {file_name} uploaded to bucket {BUCKET_NAME} as {object_name}.")
    except ClientError as e:
        print(f"Failed to upload {file_name} to S3: {e}")
        return False
    return True

def delete_file_from_s3(object_name):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=object_name)
        print(f"File {object_name} deleted from bucket {BUCKET_NAME}.")
    except ClientError as e:
        print(f"Failed to delete {object_name} from S3: {e}")
        return False
    return True

def transcribe_file_from_s3(object_name, job_name):
    file_uri = f"s3://{BUCKET_NAME}/{object_name}"
    job_args = {
        "TranscriptionJobName": job_name,
        "Media": {"MediaFileUri": file_uri},
        "MediaFormat": "wav",
        "LanguageCode": "en-US",
    }
    response = transcribe.start_transcription_job(**job_args)
    job = response["TranscriptionJob"]
    print(job)
    print("Started transcription job %s.", job_name)

def wait_for_transcription_job(job_name):
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            print(f"Transcription job {job_name} finished with status: {job_status}")
            return status
        print(f"Transcription job {job_name} is still in progress...")

def find_submission_errors(transcription_text, submitted_notes):
    prompt = """Using the Text Transcript File and the Student’s notes can you please see all of the general ideas and sub-ideas from the Text Transcript file, and compare it with the General Ideas and sub-ideas found in the Student’s notes and see where there are gaps Transcript to notes, or if there is any information in the Students notes that is not correctly interpreted from the Transcript File. Your repsonse should be one (1) paragraph. Avoid markdown and emojis."""
    prompt += f"""\n\n
    Transcript File:\n{transcription_text}\n\n
    Student Notes:\n{submitted_notes}
    """
    response = bedrock.converse(
        modelId="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={"maxTokens": 512}
    )
    response = response['output']['message']['content'][0]['text']
    return response

create_bucket_if_not_exists()

# if __name__ == "__main__":
    # find_submission_errors("This is a sample transcription text about climate change and its effects.", "Climate change effects.")