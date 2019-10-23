try:
    import unzip_requirements
except ImportError:
    pass

import json

from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any

from .combat_utilities import calculate_winner, check_dead, apply_status, \
    find_ability, apply_ability_effects, apply_enhancements


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
    status_effects: str
    attack: str
    enhanced: bool


def do_combat(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function do do some machine learning

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    request_body = event.get('body')
    left_player = Player(**request_body['player1'])
    right_player = Player(**request_body['player2'])

    # Read in the abilities data
    path_to_file = Path(__file__).parent / 'abilities.json'
    with path_to_file.open() as json_file:
        abilities = json.load(json_file)

    # Define the default combat rules
    rules = {"area": {"beats": ["disrupt", "dodge"],
                      "loses": ["attack", "block"]},
             "attack": {"beats": ["disrupt", "area"],
                        "loses": ["block", "dodge"]},
             "block": {"beats": ["area", "attack"],
                       "loses": ["disrupt", "dodge"]},
             "disrupt": {"beats": ["block", "dodge"],
                         "loses": ["attack", "area"]},
             "dodge": {"beats": ["attack", "block"],
                       "loses": ["area", "disrupt"]}}

    left_player, right_player, rules = apply_status(left_player, right_player, rules)

    # Check if anyone died from added effects
    if check_dead(left_player.hit_points, right_player.hit_points):
        # If dead, return the combat results immediately, do not do combat
        combat_results = {'Player1': asdict(left_player),
                          'Player2': asdict(right_player)}
        result = {
            'statusCode': 200,
            'body': combat_results
        }
        return result

    # Determine the winner
    outcome = calculate_winner(rules=rules,
                               left_attack=left_player.attack,
                               right_attack=right_player.attack)

    # Do combat effects based upon the outcome
    if outcome == 'left_wins':
        # Update EX meters
        left_player.ex += 50
        right_player.ex += 100

        # Find the ability to use
        ability_to_use = find_ability(abilities,
                                      left_player.character_class,
                                      left_player.attack)

        # Apply the effects
        apply_ability_effects(ability=ability_to_use,
                              target=right_player,
                              self=left_player)

        # If enhanced, apply the enhancements
        apply_enhancements(ability=ability_to_use,
                           target=right_player,
                           self=left_player)

    elif outcome == 'right_wins':
        # Update EX meters
        left_player.ex += 100
        right_player.ex += 50

        # Find the ability to use
        ability_to_use = find_ability(abilities,
                                      right_player.character_class,
                                      right_player.attack)

        # Apply the effects
        apply_ability_effects(ability=ability_to_use,
                              target=left_player,
                              self=right_player)

        # If enhanced, apply the enhancements
        apply_enhancements(ability=ability_to_use,
                           target=left_player,
                           self=right_player)
    else:
        # Update EX meters
        left_player.ex += 150
        right_player.ex += 150

        # Find both abilities to use
        left_ability = find_ability(abilities,
                                     left_player.character_class,
                                     left_player.attack)
        right_ability = find_ability(abilities,
                                      right_player.character_class,
                                      right_player.attack)

        # Apply the effects, with left getting priority
        apply_ability_effects(ability=left_ability,
                              target=right_player,
                              self=left_player)
        apply_ability_effects(ability=right_ability,
                              target=left_player,
                              self=right_player)

        # If enhanced, apply the enhancements, with left getting priority
        apply_enhancements(ability=left_ability,
                           target=right_player,
                           self=left_player)
        apply_enhancements(ability=right_ability,
                           target=left_player,
                           self=right_player)

    # Return the combat results
    combat_results = {'Player1': asdict(left_player),
                      'Player2': asdict(right_player)}
    result = {
        'statusCode': 200,
        'body': combat_results
    }
    return result