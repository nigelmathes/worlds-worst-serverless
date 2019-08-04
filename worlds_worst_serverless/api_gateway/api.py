import codecs
import os
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, APIRouter
from starlette.responses import HTMLResponse
import boto3

from typing import List, Dict
from tempfile import TemporaryDirectory

router = APIRouter()
app = FastAPI()

BUCKET_NAME = 'worlds_worst_serverless-bucket'
S3 = boto3.client('s3', region_name='us-east-1')


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/gateway/files/")
async def upload_images(files: List[UploadFile] = File(...)) -> Dict:
    # Dump incoming files into a temporary directory
    with TemporaryDirectory() as tmp_dir_name:
        for file in files:
            contents = await file.read()

            # Write the file to the temp directory
            with open(os.path.join(tmp_dir_name, file.filename), "wb") as fout:
                fout.write(contents)

    result = {"Test": "This is a tests."}

    return result


@app.get("/gateway/")
async def gateway_portal() -> HTMLResponse:
    """
     Main web page

     :return: starlette.responses.HTMLResponse with the static page in
              ./gateway.html
     """
    with codecs.open(
            Path.cwd() / "api_gateway" / "templates" / "gateway.html", "r"
    ) as static_file:
        content = static_file.read()

    return HTMLResponse(content=content)
