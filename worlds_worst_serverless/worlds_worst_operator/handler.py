try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
from string import ascii_lowercase
from dataclasses import dataclass, asdict
import decimal
from typing import Dict, Any

import requests

import boto3
from botocore.exceptions import ClientError
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

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

    # Verify the identity of the player
    player_db = Player(**get_player_info(table=player_table, player_token=id_token))

    # Return a 403 error if the submitted information does not match the player DB info
    # User has altered their player information and is not allowed to play
    if player != player_db:
        return {
            "statusCode": 403,
            "body": json.dumps({"Error": "Player information does not match"}),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }

    # If you get here, auth is good. Take action based on player ID token and action
    # TODO: Make this do something besides dummy functionality
    fields_to_update = dict()
    updated_player = player
    fields_to_update['hit_points'] = 400

    # Update player information if it needs updating
    if fields_to_update:
        update_player_info(table=player_table, player_token=id_token,
                           update_map=fields_to_update)

    # Return the results
    action_results = json.dumps(
        {"Player": asdict(updated_player), "response": None}
    )

    result = {
        "statusCode": 200,
        "body": action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return result


def get_player_info(table: dynamodb.Table, player_token: str) -> Dict:
    """
    Function to get player information from DynamoDB

    :param table: DynamoDB table object
    :param player_token: Player ID token linking player to database entry

    :return: Dictionary containing player information
    """
    # Get player information from the database
    try:
        response = table.get_item(
            Key={
                'playerId': player_token
            }
        )
    except ClientError as e:
        return e.response['Error']['Message']
    else:
        item = response['Item']

        # Remove the player ID from the response so it doesn't get passed around
        del(item['playerId'])

        print("Retrieved Player Info.")
        return json.dumps(item, indent=4, cls=DecimalEncoder)


def update_player_info(table: dynamodb.Table, player_token: str,
                       update_map: Dict) -> Dict:
    """
    Function to update player information in DynamoDB

    :param table: DynamoDB table object
    :param player_token: Player ID token linking player to database entry
    :param update_map: Dictionary mapping player information to database entry info

    :return:
    """
    update_expression = "set "
    attribute_values = dict()
    alphabet = iter(ascii_lowercase)

    # Construct the UpdateExpression and ExpressionAttributeValues for update
    # Of the form:
    #     UpdateExpression="set info.rating = :r, info.plot=:p, info.actors=:a",
    #     ExpressionAttributeValues={
    #         ':r': decimal.Decimal(5.5),
    #         ':p': "Everything happens all at once.",
    #         ':a': ["Larry", "Moe", "Curly"]
    #     },
    for key, value in update_map.items():
        letter = next(alphabet)
        update_expression = f"{key}.value = :{letter}, "
        attribute_values[f":{letter}"] = value

    print(f"Update Expression: {update_expression}")
    print(f"Attribute Values: {attribute_values}")

    response = table.update_item(
        Key={
            'playerId': player_token
        },
        UpdateExpression=update_expression,
        ExpressionAttributeValues=attribute_values
    )

    return response
