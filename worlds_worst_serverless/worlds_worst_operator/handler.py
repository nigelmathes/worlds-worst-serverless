try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
import random

from string import ascii_lowercase
from dataclasses import dataclass, asdict, fields
import decimal
from typing import Dict, Any, Tuple, List

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

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
    # TODO: Implement location
    # location = request_body["location"]
    id_token = request_body["playerId"]
    target_token = 'target_hash'
    action = request_body["action"].lower()

    # Set up the database access
    player_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    # Verify the identity of the player
    player_query = get_player_info(table=player_table, player_token=id_token)
    if 'player_data' in player_query:
        player = Player(**player_query['player_data'])
    else:
        # Return a 401 error if the id does not match an id in the database
        # User is not authorized
        return {
            "statusCode": 401,
            "body": json.dumps({"Error": "Player does not exist in database"}),
            "message": json.dumps('Time to reroll.'),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }

    # Return a 403 error if the submitted information does not match the player DB info
    # User has altered their player information and is not allowed to play
    # TODO: When we receive location information, use this to verify not GPS spoofing
    """
    if location != player_db.location:
        return {
            "statusCode": 403,
            "body": json.dumps({"Error": "Player information does not match"}),
            "message": json.dumps('Stop cheating.'),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }
    """
    # If you get here, auth is good. Take action based on player ID token and action
    # Give the player the input action
    player.attack = action
    player.enhanced = False

    # Get target from the database
    target_query = get_player_info(table=player_table, player_token=target_token)
    if 'player_data' in player_query:
        target = Player(**target_query['player_data'])
    else:
        # Return a 401 error if the id does not match an id in the database
        # User is not authorized
        return {
            "statusCode": 401,
            "body": json.dumps({"Error": "Target does not exist in database"}),
            "message": json.dumps('This is embarrassing. Could not find opponent.'),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }

    # Make the target attack
    possible_attacks = ["attack", "area", "block", "disrupt", "dodge"]
    target.attack = random.choice(possible_attacks)
    #target.enhanced = random.choice([True, False])

    # Perform the combat action
    player, target, player_updates, target_updates, message = do_combat(player, target)

    # Update player and target information if it needs updating
    if player_updates:
        update_player_info(table=player_table, player_token=id_token,
                           update_map=player_updates)
    if target_updates:
        update_player_info(table=player_table, player_token=target_token,
                           update_map=target_updates)

    # Return the results
    action_results = json.dumps(
        {
            "Player": asdict(player),
            "message": message
        }
    )

    result = {
        "statusCode": 200,
        "body": action_results,
        "headers": {"Access-Control-Allow-Origin": "*"}
    }
    return result


def do_combat(player: Player, target: Player) -> Tuple[Player, Player, Dict, Dict, List]:
    """
    Function to do combat based on a Player

    :param player: Dataclass holding player data
    :param target: Dataclass holding target player data
    :return: Updated Player dataclass and dict of fields to update
    """
    arn = 'arn:aws:lambda:us-east-1:437610822210:function:' \
          'worlds-worst-combat-dev-do_combat'
    data = {"body": {"Player1": asdict(player), "Player2": asdict(target)}}
    payload = json.dumps(data)

    # Invoke the combat lambda
    response = lambda_client.invoke(FunctionName=arn,
                                    InvocationType='RequestResponse',
                                    Payload=payload)
    # response of the form:
    # {
    #     "statusCode": 200,
    #     "body": combat_results,
    #     "headers": {"Access-Control-Allow-Origin": "*"},
    # }
    response_payload = json.loads(response.get('Payload').read())
    result = json.loads(response_payload["body"])

    message = result["message"]
    updated_player = Player(**result["Player1"])
    updated_target = Player(**result["Player2"])
    player_updates = create_update_fields(player, updated_player)
    target_updates = create_update_fields(target, updated_target)

    if updated_player.hit_points <= 0:
        message.append(f"{player.name} died! Rezzing. Die less you scrub.")
        player_updates['hit_points'] = player.max_hit_points
        player_updates['ex'] = 0
        player_updates['status_effects'] = list()
        target_updates['hit_points'] = target.max_hit_points
        target_updates['ex'] = 0
        target_updates['status_effects'] = list()
    elif updated_target.hit_points <= 0:
        message.append(f"{target.name} died! Rezzing. Great job winning.")
        player_updates['hit_points'] = player.max_hit_points
        player_updates['ex'] = 0
        player_updates['status_effects'] = list()
        target_updates['hit_points'] = target.max_hit_points
        target_updates['ex'] = 0
        target_updates['status_effects'] = list()
    else:
        message.append(f"{target.name} has {updated_target.hit_points} HP left.")

    return updated_player, updated_target, player_updates, target_updates, message


def create_update_fields(player: Player, updated_player: Player) -> Dict:
    """
    Function to diff two Player entries and output the dictionary mapping
    what fields to update to what value.

    :param player: The original player, before actions were taken
    :param updated_player: The updated player, after actions were taken

    :return: Dictionary mapping Player fields to values which will be updated
    """
    fields_to_update = dict()
    if player != updated_player:
        print(f"{player.name} needs updating!")
        # Loop over player fields and output what needs updating as dict
        for field in fields(player):
            old_value = getattr(player, field.name)
            new_value = getattr(updated_player, field.name)
            if old_value != new_value:
                # Do not update if hit points or EX is max
                if field.name == 'hit_points' and new_value >= player.max_hit_points:
                    print("Hit points already max. Not updating.")
                elif field.name == 'ex' and new_value >= player.max_ex:
                    print("EX meter already max. Not updating.")
                else:
                    print(f"{field.name} is different, updating to {new_value}")
                    fields_to_update[field.name] = new_value

    return fields_to_update


def get_player_info(table: dynamodb.Table, player_token: str) -> Dict:
    """
    Function to get player information from DynamoDB

    :param table: DynamoDB table object
    :param player_token: Player ID token linking player to database entry

    :return: Dictionary containing player information
    """
    # Get player information from the database
    print(f"Getting 'playerId': {player_token} from DB")
    try:
        response = table.get_item(
            Key={
                'playerId': player_token
            }
        )
    except ClientError as e:
        return e.response['Error']['Message']
    else:
        try:
            item = response['Item']

            # Remove the player ID from the response so it doesn't get passed around
            del (item['playerId'])

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
        Item={
            'playerId': 'target_hash',
            'player_data': asdict(player)
        },
    )

    print(f"Created player. response={response}")
    return response


def update_player_info(table: dynamodb.Table, player_token: str,
                       update_map: Dict) -> Dict:
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
        Key={
            'playerId': player_token
        },
        UpdateExpression=update_expression,
        ExpressionAttributeValues=attribute_values
    )

    return response
