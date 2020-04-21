try:
    import unzip_requirements
except ImportError:
    pass

import json
import os

from typing import Dict, Any

import boto3

try:
    from database_ops import update_player, get_player, create_new_player
except ImportError:
    from .database_ops import update_player, get_player, create_new_player

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
lambda_client = boto3.client("lambda", region_name="us-east-1")

LambdaDict = Dict[str, Any]


def authenticate(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function to take input in the form of a Player object, along with login
    credentials and a command

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    print(event)
    request_body = event.get("body")
    if type(request_body) == str:
        request_body = json.loads(request_body)
    player_name = request_body["playerId"]
    id_token = request_body["auth_token"]

    # Set up the database access
    player_table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])

    if get_player(table=player_table, player_token=player_name):
        update_dict = {
            "auth_token": id_token
        }
        response = update_player(
            table=player_table, player_token=player_name, update_map=update_dict
        )
        return {
            "statusCode": 200,
            "body": response,
            "headers": {"Access-Control-Allow-Origin": "*"},
        }
    else:
        response = create_new_player(
            table=player_table, player_token=player_name, auth_token=id_token
        )
        return {
            "statusCode": 200,
            "body": response,
            "headers": {"Access-Control-Allow-Origin": "*"},
        }
