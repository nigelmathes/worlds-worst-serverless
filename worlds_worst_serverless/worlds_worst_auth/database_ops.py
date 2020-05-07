import decimal
import json
from string import ascii_lowercase
from typing import Dict

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")


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


def create_new_player(table: dynamodb.Table, player_token: str, auth_token: str) -> Dict:
    """
    Function to create a new player and save to DynamoDB when the authenticated
    user doesn't have a character already.

    :param table: DynamoDB table objects
    :param player_token: Name of character
    :param auth_token web token ID of user

    :return: Dictionary containing player information
    """
    # Create base player entry
    new_player_data = {
        "name": player_token,
        "character_class": "dreamer",
        "max_hit_points": 500,
        "max_ex": 1000,
        "hit_points": 500,
        "ex": 0,
        "status_effects": [],
        "action": "attack",
        "enhanced": False,
        "auth_token": auth_token,
        "context": "home",
        "history": [],
    }

    # Put player into DB
    response = table.put_item(
        Item={"playerId": player_token, "player_data": new_player_data}
    )

    print(f"Created player {new_player_data['name']}")
    return response


def update_player(table: dynamodb.Table, player_token: str, update_map: Dict) -> Dict:
    """
    Function to update player information in DynamoDB

    :param table: DynamoDB table object
    :param player_token: Player ID token linking player to database entry
    :param update_map: Dictionary mapping player information to database entry info

    :return: Response of DynamoDB table update
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
        update_expression += f"player_data.{key} = :{letter}, "
        attribute_values[f":{letter}"] = value

    update_expression = update_expression[:-2]

    response = table.update_item(
        Key={"playerId": player_token},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=attribute_values,
    )

    return response


def get_player(table: dynamodb.Table, player_token: str) -> bool:
    """
    Function to get player information from DynamoDB

    :param table: DynamoDB table object
    :param player_token: Player ID token linking player to database entry

    :return: Dictionary containing player information
    """
    # Get player information from the database
    print(f"Getting 'playerId': {player_token} from DB")
    try:
        response = table.get_item(Key={"playerId": player_token})
    except ClientError as e:
        return e.response["Error"]["Message"]
    else:
        try:
            item = response["Item"]

            # Try to remove the playerId from the dict
            del (item["playerId"])

            print("Retrieved Player Info.")
            return True
        except KeyError:
            print("Player does not exist.")
            return False
