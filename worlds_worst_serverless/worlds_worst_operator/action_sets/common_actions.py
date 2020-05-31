import json

from dataclasses import fields
from typing import Dict, Tuple, List

import boto3
from fuzzywuzzy import process

try:
    from database_ops import get_player
    from player_data import Player
except ImportError:
    from ..database_ops import get_player
    from ..player_data import Player

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
    return player, target, {}, {}, message


def change_class(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Function to change a player's class

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object (unused)

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
        return player, player, {}, {}, message

    possible_classes = [
        "dreamer",
        "cloistered",
        "chosen",
        "chemist",
        "creator",
        "hacker",
        "architect",
        "photonic",
    ]

    # Find the new class to play
    if player.action in possible_classes:
        matched_class = player.action
    else:
        # Fuzzy match
        matched_class = process.extractOne(player.action, possible_classes)[0]

    player_updates = {}
    target_updates = {}

    # Reset player and target HP to restart combat
    player_updates["character_class"] = matched_class
    player_updates["hit_points"] = player.max_hit_points
    player_updates["ex"] = 0
    player_updates["status_effects"] = list()
    target_updates["hit_points"] = target.max_hit_points
    target_updates["ex"] = 0
    target_updates["status_effects"] = list()

    message = [
        f"Changing class from {player.character_class} to" f" {matched_class}.",
        "Resetting HP, EX and status for player and target.",
    ]

    return player, target, player_updates, target_updates, message


def change_class_message(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Function to produce message response to 2-step change character

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object (unused)

    :return: Unchanged Player dataclass with no updates, and a message
    """
    message = [
        "What class would you like to change to?",
        "You may choose from:",
        "Dreamer, Cloistered, Chosen, Chemist, Creator,"
        " Hacker, Architect, or Photonic",
        "Enter that choice now."
    ]

    return player, player, {}, {}, message


def get_player_info(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Function to return all information about a Player

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object

    :return: Unchanged Player dataclass with no updates and no message
    """
    if player.character_class[0] in ('a', 'e', 'i', 'o', 'u'):
        article = 'an'
    else:
        article = 'a'

    message = [
        f"You are {player.name}, {article} {player.character_class}",
        f"You have {player.hit_points} HP and {player.ex} EX",
        f"Your status effects are {player.status_effects}",
        f"You are currently {player.context}. What would you like to do?"
    ]
    return player, player, {}, {}, message


def create_update_fields(player: Player, updated_player: Player) -> Dict:
    """
    Function to diff two Player entries and output the dictionary mapping
    what fields to update to what value.

    :param player: The original player, before actions were taken
    :param updated_player: The updated player, after actions were taken

    :return: Dictionary mapping Player fields to values which will be updated
    """
    fields_to_update = {}
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
COMMON_ACTIONS_MAP = {
    "change": change_class_message,
    "change class": change_class_message,
    "change character": change_class_message,
    "dreamer": change_class,
    "cloistered": change_class,
    "chosen": change_class,
    "chemist": change_class,
    "creator": change_class,
    "hacker": change_class,
    "architect": change_class,
    "photonic": change_class,
    "get player info": get_player_info,
    "status": get_player_info,
    "my status": get_player_info,
    "my information": get_player_info,
}
