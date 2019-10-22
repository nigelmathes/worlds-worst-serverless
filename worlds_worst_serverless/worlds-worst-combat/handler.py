try:
    import unzip_requirements
except ImportError:
    pass

from dataclasses import dataclass, asdict
from typing import Dict, Any

from .combat_utilities import calculate_winner, check_dead, apply_status
from .combat_effects import *

LambdaDict = Dict[str, Any]


@dataclass
class Player:
    """
    Class to hold player information
    """
    name: str
    max_hit_points: int
    max_ex: int
    ex: int
    hit_points: int
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
    combat_results = dict()

    # Decode the request
    request_body = event.get('body')
    left_player = Player(**request_body['player1'])
    right_player = Player(**request_body['player2'])

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
        if left_player.hit_points == 0:
            print("Player1 died.")
        else:
            print("Player2 died.")
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
        pass
    elif outcome == 'right_wins':
        # Update EX meters
        left_player.ex += 100
        right_player.ex += 50
        pass
    else:
        # Update EX meters
        left_player.ex += 150
        right_player.ex += 150
        pass

    result = {
        'statusCode': 200,
        'body': combat_results
    }
    return result
