try:
    import unzip_requirements
except ImportError:
    pass

import boto3
import json
import os
import shutil
from pathlib import Path

import gpt_2_simple as gpt2

from typing import Dict, Any, List

LambdaDict = Dict[str, Any]


def download_from_s3(bucket: str, bucket_path: str, local_path: str) -> None:
    """
    Function to download a file from S3 bucket

    :param bucket: Name of S3 bucket
    :param bucket_path: Path to file inside S3 bucket
    :param local_path: Path to file inside serverless environment
    """
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, bucket_path, local_path)


def run_inference(input_data: str) -> List:
    """
    Runs model inference on the input_data

    :param input_data: Data input
    :return: List of results
    """
    model_name = "124M"
    sess = gpt2.start_tf_sess()
    # Load the model found in ./models/124M/
    gpt2.load_gpt2(sess, model_name=model_name, model_dir='/tmp/models')
    single_text = gpt2.generate(sess,
                                prefix=input_data,
                                model_name=model_name,
                                return_as_list=True,
                                length=40,
                                truncate='<|endoftext|>',
                                batch_size=1,
                                nsamples=1,
                                temperature=0.8)

    return single_text


def infer(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function do do some machine learning

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    my_bucket = 'worlds-worst-serverless-bucket'

    # Set up local model directory
    local_model_directory = Path('/tmp/models/124M')
    shutil.rmtree(Path('/tmp/models'), ignore_errors=True)
    os.makedirs(local_model_directory)

    # Download model from S3 and extract if it doesn't exist
    # Lambda functions can re-use environments, so sometimes it's still there
    files_to_download = [
        Path('gpt-2-models/124M/checkpoint'),
        Path('gpt-2-models/124M/encoder.json'),
        Path('gpt-2-models/124M/hparams.json'),
        Path('gpt-2-models/124M/model.ckpt.data-00000-of-00001'),
        Path('gpt-2-models/124M/model.ckpt.index'),
        Path('gpt-2-models/124M/model.ckpt.meta'),
        Path('gpt-2-models/124M/vocab.bpe')
    ]
    for file in files_to_download:
        local_file_path = local_model_directory / file.name
        if local_file_path.is_file():
            continue
        else:
            print(f"Downloading {file} to {local_file_path}")
            download_from_s3(my_bucket, file.as_posix(), local_file_path.as_posix())

    # Decode the request
    request_body = event.get('body')
    inference_input = request_body['input']

    # Run inference
    my_result = run_inference(inference_input)

    result = {
        'statusCode': 200,
        'body': json.dumps(my_result, default=lambda x: x.decode('utf-8'))
    }
    return result
