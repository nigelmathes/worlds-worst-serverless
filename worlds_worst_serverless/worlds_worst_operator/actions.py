import json

from dataclasses import asdict, fields
from typing import Dict, Tuple, List

import boto3

try:
    from database_ops import get_player_info, create_player, update_player_info
    from player_data import Player
except ImportError:
    from .database_ops import get_player, create_player, update_player
    from .player_data import Player


lambda_client = boto3.client("lambda", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]


def unknown_action(player: Player, target: Player) -> ActionResponse:
    """
    Function to do nothing because the action could not be resolved.
    In the message list, returns a message saying the action was bad.

    :return: Original inputs matching updated inputs, and a message
    """
    message = ["Action could not be resolved, type better next time"]
    return player, target, dict(), dict(), message


def do_combat(player: Player, target: Player) -> ActionResponse:
    """
    Function to do combat based on a Player

    :param player: Dataclass holding player data
    :param target: Dataclass holding target player data
    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    arn = (
        "arn:aws:lambda:us-east-1:437610822210:function:"
        "worlds-worst-combat-dev-do_combat"
    )
    data = {"body": {"Player1": asdict(player), "Player2": asdict(target)}}
    payload = json.dumps(data)

    # Invoke the combat lambda
    response = lambda_client.invoke(
        FunctionName=arn, InvocationType="RequestResponse", Payload=payload
    )
    # response of the form:
    # {
    #     "statusCode": 200,
    #     "body": combat_results,
    #     "headers": {"Access-Control-Allow-Origin": "*"},
    # }
    response_payload = json.loads(response.get("Payload").read())
    result = json.loads(response_payload["body"])

    message = result["message"]
    updated_player = Player(**result["Player1"])
    updated_target = Player(**result["Player2"])
    player_updates = create_update_fields(player, updated_player)
    target_updates = create_update_fields(target, updated_target)

    if updated_player.hit_points <= 0:
        message.append(f"{player.name} died! Rezzing. Die less you scrub.")
        player_updates["hit_points"] = player.max_hit_points
        player_updates["ex"] = 0
        player_updates["status_effects"] = list()
        target_updates["hit_points"] = target.max_hit_points
        target_updates["ex"] = 0
        target_updates["status_effects"] = list()
    elif updated_target.hit_points <= 0:
        message.append(f"{target.name} died! Rezzing. Great job winning.")
        player_updates["hit_points"] = player.max_hit_points
        player_updates["ex"] = 0
        player_updates["status_effects"] = list()
        target_updates["hit_points"] = target.max_hit_points
        target_updates["ex"] = 0
        target_updates["status_effects"] = list()
    else:
        message.append(f"{target.name} has {updated_target.hit_points} HP left.")

    return updated_player, updated_target, player_updates, target_updates, message


def change_character(player: Player, updated_player: Player) -> Dict:
    """

    :param player: The original player, before actions were taken
    :param updated_player: The updated player, after actions were taken

    :return: Dictionary mapping Player fields to values which will be updated
    """
    pass
    # return updated_player, updated_target, player_updates, target_updates, message


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
                if field.name == "hit_points" and new_value >= player.max_hit_points:
                    print("Hit points already max. Not updating.")
                elif field.name == "ex" and new_value >= player.max_ex:
                    print("EX meter already max. Not updating.")
                else:
                    print(f"{field.name} is different, updating to {new_value}")
                    fields_to_update[field.name] = new_value

    return fields_to_update


# Map commands to functions that if perfectly matched will execute
ACTIONS_MAP = {
    "attack": do_combat,
    "area": do_combat,
    "block": do_combat,
    "disrupt": do_combat,
    "dodge": do_combat,
}
