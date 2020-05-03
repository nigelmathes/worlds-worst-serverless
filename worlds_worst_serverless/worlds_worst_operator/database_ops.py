import decimal
import json
from dataclasses import asdict
from string import ascii_lowercase
from typing import Dict, Tuple

import boto3

from botocore.exceptions import ClientError

try:
    from player_data import Player
except ImportError:
    from .player_data import Player

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


def get_player(table: dynamodb.Table, player_token: str) -> Dict:
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

            # Remove the player ID from the response so it doesn't get passed around
            del (item["playerId"])

            print("Retrieved Player Info.")
            return json.loads(json.dumps(item, indent=4, cls=DecimalEncoder))
        except KeyError:
            return {"Error": "Queried player does not exist."}


def create_player(table: dynamodb.Table, player: Player) -> Dict:
    """
    Function to create a new player and save to DynamoDB

    :param table: DynamoDB table object
    :param player: Player information to put into the database

    :return: Dictionary containing player information
    """
    # Put player into DB
    response = table.put_item(
        Item={"playerId": player.name, "player_data": asdict(player)}
    )

    print(f"Created player {player.name}")
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


def verify_player(table: dynamodb.Table, player_token: str) -> Tuple[Dict, bool]:
    """
    Verify the identity of the player
    """
    player_query = get_player(table=table, player_token=player_token)
    if "player_data" in player_query:
        # Deal with string vs. list
        if type(player_query["player_data"]["status_effects"]) != list:
            player_query["player_data"]["status_effects"] = json.loads(
                player_query["player_data"]["status_effects"]
            )
        return player_query["player_data"], True
    else:
        # Return a 401 error if the id does not match an id in the database
        # User is not authorized
        return (
            {
                "statusCode": 401,
                "body": json.dumps({"Error": "Player does not exist in database"}),
                "message": json.dumps("Please log in again."),
                "headers": {"Access-Control-Allow-Origin": "*"},
            },
            False,
        )
