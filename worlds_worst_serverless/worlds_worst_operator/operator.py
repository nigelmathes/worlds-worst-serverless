try:
    import unzip_requirements
except ImportError:
    pass

import json
import os
from pathlib import Path

from dataclasses import asdict
from typing import Dict, Any, Callable, Tuple

import boto3
from fuzzywuzzy import process

try:
    from database_ops import create_player, update_player, verify_player
    from player_data import Player
    from actions import ACTIONS_MAP, unknown_action, do_combat
except ImportError:
    from .database_ops import create_player, update_player, verify_player
    from .player_data import Player
    from .actions import ACTIONS_MAP, unknown_action, do_combat

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
lambda_client = boto3.client("lambda", region_name="us-east-1")

LambdaDict = Dict[str, Any]


def route_tasks_and_response(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function to take auth credentials from the frontend and update the
    JWT associated with a player's character in dynamodb

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
    target_token = "target_hash"
    action = request_body["action"].lower()

    enhanced_words_with_typos = [
        "enhance",
        "enhanced",
        "enhancement",
        "enhanec",
        "nehance",
        "enhancd",
    ]
    # Handle if the user is enhancing their command
    if any(word in action for word in enhanced_words_with_typos):
        enhanced = True
    else:
        enhanced = False

    # Set up the database access
    player_table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])

    # Verify the ID of the player and load player data if successful
    player_data, verified = verify_player(table=player_table, player_token=id_token)

    if verified:
        player = Player(**player_data)
    else:
        # Contains the return dict with a 401 statusCode
        return player_data

    # If you get here, auth is good. Take action based on player info and action
    action_to_do, function_to_run = route_action(action=action)

    # Give the player the input action and its enhanced flag
    player.action = action_to_do
    player.enhanced = enhanced

    # Perform the action
    player, target, player_updates, target_updates, message = function_to_run(
        player=player, table=player_table
    )

    # Update player and target information if it needs updating
    if player_updates:
        update_player(
            table=player_table, player_token=id_token, update_map=player_updates
        )
    if target_updates:
        update_player(
            table=player_table, player_token=target_token, update_map=target_updates
        )

    # Return the results
    action_results = json.dumps({"Player": asdict(player), "message": message})

    result = {
        "statusCode": 200,
        "body": action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return result


def route_action(action: str) -> Tuple[str, Callable]:
    """
    Function to take in an action and route the command to the appropriate functions

    :param action: String action to take

    :return: List of functions to call, in order, to complete the action
    """
    if action in ACTIONS_MAP:
        # Perfect match
        return action, ACTIONS_MAP[action]
    else:
        # Fuzzy match
        possible_actions = ACTIONS_MAP.keys()
        matched_action = process.extractOne(action, possible_actions)[0]

        return matched_action, ACTIONS_MAP[matched_action]


def reset_characters(table: dynamodb.Table) -> Dict:
    """
    Function to reset the characters in table

    :param table: DynamoDB table object
    :return: Response to return
    """
    with open(
        Path(__file__).resolve().parent / "default_players.json", "r"
    ) as default_file:
        default_characters = json.load(default_file)

    message = list()
    for default_character in default_characters:
        player = Player(**default_character)
        create_player(table=table, player=player)
        message.append(f"Reset {player.name}")

    # Return the results
    action_results = json.dumps({"Player": asdict(player), "message": message})

    result = {
        "statusCode": 200,
        "body": action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    return result
