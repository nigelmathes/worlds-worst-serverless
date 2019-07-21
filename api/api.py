from fastapi import FastAPI
import boto3

app = FastAPI()

BUCKET_NAME = 'worlds-worst-serverless-bucket'
S3 = boto3.client('s3', region_name='us-east-1')


@app.get("/")
async def root():
    return {"message": "Hello World"}

