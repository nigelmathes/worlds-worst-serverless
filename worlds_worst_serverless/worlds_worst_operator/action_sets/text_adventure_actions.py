import json

from dataclasses import asdict
from typing import Dict, Tuple, List

import boto3

try:
    from player_data import Player
    from arns import TEXT_ADVENTURE_ARN
    from action_sets.common_actions import create_update_fields
except ImportError:
    from ..player_data import Player
    from ..arns import TEXT_ADVENTURE_ARN
    from ..action_sets.common_actions import create_update_fields


lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]


def play_game(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Plays game defined in player.context using commands stored in player.history along
    with player.action, appending player.action to player.history and sending to
    the text adventure lambda.

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object (unused)

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    updated_player = Player(**asdict(player))

    # If player wants to quit the game, don't pass the quit action to the text
    # adventure game, just end here and send the player home
    quit_with_typos = ["quit", "qit", "qut", "quitt", "quuit", "quiit"]
    if any(word in player.action for word in quit_with_typos):
        updated_player.context = "home"
        updated_player.history = []
        updated_player.target = "None"
        message = [f"You turn off {player.target}, returning home."]
        player_updates = create_update_fields(player, updated_player)

        return player, player, player_updates, player_updates, message

    # If not quitting, play the text adventure game
    updated_player.history.append(player.action)

    data = {"body": {"actions": updated_player.history, "game": updated_player.target}}
    payload = json.dumps(data)

    # Invoke the text adventure lambda
    response = lambda_client.invoke(
        FunctionName=TEXT_ADVENTURE_ARN,
        InvocationType="RequestResponse",
        Payload=payload
    )
    # response of the form:
    # {
    #     "statusCode": 200,
    #     "body": text_adventure_result,
    #     "headers": {"Access-Control-Allow-Origin": "*"},
    # }
    response_payload = json.loads(response.get("Payload").read())
    result = json.loads(response_payload["body"])

    message = result["message"]
    player_updates = create_update_fields(player, updated_player)

    return player, player, player_updates, player_updates, message


TEXT_ADVENTURE_ACTIONS_MAP = {
    "default": play_game,
}
