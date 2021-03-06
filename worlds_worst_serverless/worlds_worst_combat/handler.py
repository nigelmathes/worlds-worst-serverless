try:
    import unzip_requirements
except ImportError:
    pass

import json

from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any

try:
    from player_data import Player
    from combat_utilities import (
        calculate_winner,
        check_dead,
        apply_status,
        find_ability,
        apply_ability_effects,
        apply_enhancements,
        apply_ex,
    )
except ImportError:
    from .player_data import Player
    from .combat_utilities import (
        calculate_winner,
        check_dead,
        apply_status,
        find_ability,
        apply_ability_effects,
        apply_enhancements,
        apply_ex,
    )

LambdaDict = Dict[str, Any]


def do_combat(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function do combat

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    request_body = event.get("body")
    if type(request_body) == str:
        request_body = json.loads(request_body)
    left_player = Player(**request_body["Player1"])
    right_player = Player(**request_body["Player2"])

    # Store the series of events
    message = []

    # Read in the abilities data
    path_to_file = Path(__file__).parent / "abilities.json"
    with path_to_file.open() as json_file:
        abilities = json.load(json_file)

    # Define the default combat rules
    rules = {
        "area": {"beats": ["disrupt", "dodge"], "loses": ["attack", "block"]},
        "attack": {"beats": ["disrupt", "area"], "loses": ["block", "dodge"]},
        "block": {"beats": ["area", "attack"], "loses": ["disrupt", "dodge"]},
        "disrupt": {"beats": ["block", "dodge"], "loses": ["attack", "area"]},
        "dodge": {"beats": ["attack", "block"], "loses": ["area", "disrupt"]},
    }

    # Apply status effects
    left_player, right_player, rules, message = apply_status(left_player,
                                                             right_player,
                                                             rules,
                                                             message)

    # Check if anyone died from added effects
    if check_dead(left_player.hit_points, right_player.hit_points):
        # If dead, return the combat results immediately, do not do combat
        if left_player.hit_points <= 0:
            message.append(f"{left_player.name} died to their status effects.")
        else:
            message.append(f"{right_player.name} died to their status effects.")
        combat_results = json.dumps(
            {
                "Player1": asdict(left_player),
                "Player2": asdict(right_player),
                "message": message,
            }
        )
        result = {
            "statusCode": 200,
            "body": combat_results,
            "headers": {"Access-Control-Allow-Origin": "*"},
        }
        return result

    # Determine the winner
    message.append(f"{left_player.name} uses {left_player.action}!")
    message.append(f"{right_player.name} uses {right_player.action}!")
    outcome = calculate_winner(
        rules=rules, left_attack=left_player.action, right_attack=right_player.action
    )

    # Do combat effects based upon the outcome
    if outcome == "left_wins":
        message.append(f"{left_player.name} wins.")
        # Update EX meters
        left_player.ex += 50
        right_player.ex += 100

        # Find the ability to use
        ability_to_use = find_ability(
            abilities, left_player.character_class, left_player.action
        )

        # Apply the effects
        apply_ability_effects(
            ability=ability_to_use, target=right_player, self=left_player
        )

        # If enhanced, apply the enhancements
        if left_player.enhanced is True:
            if ability_to_use['enhancements']:
                message.append(
                    f"{left_player.name} enhanced {left_player.action}! "
                    f"Inflicting {ability_to_use['enhancements'][0]['name']} on"
                    f" {ability_to_use['enhancements'][0]['target']} for"
                    f" {ability_to_use['enhancements'][0]['value']} turn(s)."
                )
                apply_enhancements(
                    ability=ability_to_use, target=right_player, self=left_player
                )
            else:
                message.append(f"{left_player.character_class}s cannot enhance "
                               f"{left_player.action}!")

    elif outcome == "right_wins":
        message.append(f"{right_player.name} wins.")
        # Update EX meters
        left_player.ex += 100
        right_player.ex += 50

        # Find the ability to use
        ability_to_use = find_ability(
            abilities, right_player.character_class, right_player.action
        )

        # Apply the effects
        apply_ability_effects(
            ability=ability_to_use, target=left_player, self=right_player
        )

        # If enhanced, apply the enhancements
        if right_player.enhanced is True:
            if ability_to_use['enhancements']:
                message.append(
                    f"{right_player.name} enhanced {right_player.action}! "
                    f"Inflicting {ability_to_use['enhancements'][0]['name']} on"
                    f" {ability_to_use['enhancements'][0]['target']} for"
                    f" {ability_to_use['enhancements'][0]['value']} turn(s)."
                )
                apply_enhancements(
                    ability=ability_to_use, target=left_player, self=right_player
                )
            else:
                message.append(f"{right_player.character_class}s cannot enhance "
                               f"{right_player.action}!")
    else:
        message.append(f"{left_player.name} and {right_player.name} tie.")
        # Update EX meters
        left_player.ex += 150
        right_player.ex += 150

        # Find both abilities to use
        left_ability = find_ability(
            abilities, left_player.character_class, left_player.action
        )
        right_ability = find_ability(
            abilities, right_player.character_class, right_player.action
        )
        print(f"Using abilities: {right_ability}, {left_ability}")

        # Apply the effects, with left getting priority
        apply_ability_effects(
            ability=left_ability, target=right_player, self=left_player
        )
        apply_ability_effects(
            ability=right_ability, target=left_player, self=right_player
        )

        print(
            f"After applied effects: left_player hp = {left_player.hit_points},"
            f" right_player hp={right_player.hit_points}"
        )

        # If enhanced, apply the enhancements, with left getting priority
        if left_player.enhanced is True:
            if left_ability["enhancements"]:
                message.append(
                    f"{left_player.name} enhanced {left_player.action}! "
                    f"Inflicting {left_ability['enhancements'][0]['name']} on"
                    f" {left_ability['enhancements'][0]['target']} for"
                    f" {left_ability['enhancements'][0]['value']} turn(s)."
                )
                apply_enhancements(
                    ability=left_ability, target=right_player, self=left_player
                )
            else:
                message.append(
                    f"{left_player.name} tried to enhance {left_player.action}, "
                    f"but it can't be enhanced. Nothing happened!"
                )
        if right_player.enhanced is True:
            if right_ability["enhancements"]:
                message.append(
                    f"{right_player.name} enhanced {right_player.action}! "
                    f"Inflicting {right_ability['enhancements'][0]['name']} on"
                    f" {right_ability['enhancements'][0]['target']} for"
                    f" {right_ability['enhancements'][0]['value']} turn(s)."
                )
                apply_enhancements(
                    ability=right_ability, target=left_player, self=right_player
                )
            else:
                message.append(
                    f"{right_player.name} tried to enhance {right_player.action}, "
                    f"but it can't be enhanced. Nothing happened!"
                )

    if left_player.ex == left_player.max_ex:
        apply_ex(left_player)

    if right_player.ex == right_player.max_ex:
        apply_ex(right_player)

    left_player.enhanced = False
    right_player.enhanced = False

    # Return the combat results
    combat_results = json.dumps(
        {
            "Player1": asdict(left_player),
            "Player2": asdict(right_player),
            "message": message,
        }
    )

    result = {
        "statusCode": 200,
        "body": combat_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return result
