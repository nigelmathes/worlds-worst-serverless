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
    from action_sets.common_actions import COMMON_ACTIONS_MAP, unknown_action
    from action_sets.combat_actions import COMBAT_ACTIONS_MAP
    from action_sets.home_actions import HOME_ACTIONS_MAP
except ImportError:
    from .database_ops import create_player, update_player, verify_player
    from .player_data import Player
    from .action_sets.common_actions import COMMON_ACTIONS_MAP, unknown_action
    from .action_sets.combat_actions import COMBAT_ACTIONS_MAP
    from .action_sets.home_actions import HOME_ACTIONS_MAP
    from .action_sets.text_adventure_actions import TEXT_ADVENTURE_ACTIONS_MAP

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

    # Set up the database access
    player_table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])

    # Verify the ID of the player and load player data if successful
    player_data, verified = verify_player(table=player_table, player_token=id_token)

    if verified:
        player = Player(**player_data)
    else:
        # Contains the return dict with a 401 statusCode
        return player_data

    # If you get here, auth is good.
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

    # Build the actions map
    actions_map = build_actions_map(context=player.context)

    # Take action based on player info and action
    action_to_do, function_to_run = route_action(action=action, actions_map=actions_map)

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


def build_actions_map(context: str) -> Dict:
    """
    Function to use the context passed to determine which actions dicts should be
    combined to use for routing

    :param context: String containing the context of the player

    :return: Full actions dictionary to traverse to determine function to run
    """
    combined_actions_map = COMMON_ACTIONS_MAP

    if context == 'home':
        combined_actions_map.update(HOME_ACTIONS_MAP)
    if context == 'combat':
        combined_actions_map.update(COMBAT_ACTIONS_MAP)
    if context == 'text_adventure':
        # Remove the common actions so they don't clash with the
        # commands in the text adventure, leaving only "default.
        # This is now a pass-through to the text adventure game engine
        for key in combined_actions_map:
            del combined_actions_map[key]
        combined_actions_map.update(TEXT_ADVENTURE_ACTIONS_MAP)

    return combined_actions_map


def route_action(action: str, actions_map: dict) -> Tuple[str, Callable]:
    """
    Function to take in an action and route the command to the appropriate functions

    :param action: String action to take
    :param actions_map: Dictionary of possible actions

    :return: List of functions to call, in order, to complete the action
    """
    if action in actions_map:
        # Perfect match
        return action, actions_map[action]
    else:
        # Fuzzy match
        possible_actions = actions_map.keys()
        matched_action = process.extractOne(action, possible_actions)[0]

        return matched_action, actions_map[matched_action]


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
