try:
    import unzip_requirements
except ImportError:
    pass

import boto3
import json

from typing import Dict, Any

LambdaDict = Dict[str, Any]


def download_from_s3(bucket: str, bucket_path: str, local_path: str) -> None:
    """
    Function to download a file from S3 bucket

    :param bucket: Name of S3 bucket
    :param bucket_path: Path to file inside S3 bucket
    :param local_path: Path to file inside serverless environment
    """
    s3_client = boto3.client("s3")
    s3_client.download_file(bucket, bucket_path, local_path)


def write_story(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function do do some machine learning

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    request_body = event.get("body")
    story_context = request_body["context"]
    action = request_body["action"]

    # Generate story based on context and action
    my_result = "Nothing here yet"

    result = {
        "statusCode": 200,
        "body": json.dumps(my_result, default=lambda x: x.decode("utf-8")),
    }
    return result
