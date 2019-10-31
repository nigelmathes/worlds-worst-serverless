try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
from dataclasses import dataclass, asdict
import decimal
from typing import Dict, Any

import requests

import boto3
from botocore.exceptions import ClientError
dynamodb = boto3.resource('dynamodb')

LambdaDict = Dict[str, Any]


@dataclass
class Player:
    """
    Class to hold player information
    """

    name: str
    character_class: str
    max_hit_points: int
    max_ex: int
    hit_points: int
    ex: int
    status_effects: list
    attack: str
    enhanced: bool


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    """
    This is a workaround for: http://bugs.python.org/issue16535
    """
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def route_tasks_and_response(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function to take input in the form of a Player object, along with login
    credentials and a command

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    request_body = event.get("body")
    if type(request_body) == str:
        request_body = json.loads(request_body)
    player = Player(**request_body["Player"])
    id_token = request_body["id"]
    action = request_body["action"]

    # Set up the database access
    player_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    # Get player information from the database
    try:
        response = player_table.get_item(
            Key={
                'playerId': id_token
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        item = response['Item']
        print("GetItem succeeded:")
        print(json.dumps(item, indent=4, cls=DecimalEncoder))

    # Verify the identity of the player




    # Return the results
    action_results = json.dumps(
        {"Player": asdict(player), "response": None}
    )

    result = {
        "statusCode": 200,
        "body": action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return result
