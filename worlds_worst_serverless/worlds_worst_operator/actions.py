import copy
import json
import random

from dataclasses import asdict, fields
from typing import Dict, Tuple, List

import boto3

try:
    from database_ops import get_player, create_player, update_player
    from player_data import Player
except ImportError:
    from .database_ops import get_player, create_player, update_player
    from .player_data import Player


lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]


def unknown_action(player: Player, target: Player) -> ActionResponse:
    """
    Function to do nothing because the action could not be resolved.
    In the message list, returns a message saying the action was bad.

    :return: Original inputs matching updated inputs, and a message
    """
    message = ["Action could not be resolved, type better next time"]
    return player, target, dict(), dict(), message


def do_combat(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Function to do combat based on a Player

    :param player: Dataclass holding player data
    :param table: DynamoDB table object
    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    # Get target from the database
    target_token = "target_hash"
    target_query = get_player(table=table, player_token=target_token)
    if "player_data" in target_query:
        # Deal with string vs. list
        if type(target_query["player_data"]["status_effects"]) != list:
            target_query["player_data"]["status_effects"] = json.loads(
                target_query["player_data"]["status_effects"]
            )
        target = Player(**target_query["player_data"])
    else:
        # Return a 401 error if the id does not match an id in the database
        # User is not authorized
        message = ["ERROR. This is embarrassing. Could not find opponent in database."]
        return player, player, dict(), dict(), message

    # Make the target attack
    possible_attacks = ["attack", "area", "block", "disrupt", "dodge"]
    target.action = random.choice(possible_attacks)
    # target.enhanced = random.choice([True, False])

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


def change_class(player: Player, new_class: str) -> ActionResponse:
    """
    Function to change a player's class

    :param player: The original player, before actions were taken
    :param new_class: The class to change into

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    old_player = copy.deepcopy(player)
    player.character_class = new_class

    player_updates = create_update_fields(old_player, player)

    message = [f"Changed class from {old_player.character_class} to"
               f" {player.character_class}"]

    return player, player, player_updates, dict(), message


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
    "change character": change_class,
    "change class": change_class
}
