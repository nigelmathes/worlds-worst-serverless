"""
Holds all combat logic
"""
import json
from typing import Tuple
from .handler import Player
from . import combat_effects


def calculate_winner(rules: dict, left_attack: str, right_attack: str) -> str:
    """
    Function to calculate the winner of combat
    Left player has priority and goes first

    :param rules: Dictionary of current rules
    :param left_attack: Attack type of priority player
    :param right_attack: Attack type of right player
    :return: Result of combat, either "left_wins", "right_wins", or "draw"
    """
    priority_rules = rules[left_attack]

    if right_attack in priority_rules['beats']:
        return "left_wins"
    elif right_attack in priority_rules['loses']:
        return "right_wins"
    else:
        return "draw"


def check_dead(left_hp: int, right_hp: int) -> bool:
    """
    Method to check if either player is dead

    :param left_hp: Hit points of priority player
    :param right_hp: Hit points of right player
    :return: True if somebody is dead, else False
    """
    if left_hp <= 0:
        return True
    elif right_hp <= 0:
        return True
    else:
        return False


def apply_status(player1: Player, player2: Player, rules: dict) -> Tuple[Player,
                                                                         Player,
                                                                         dict]:
    """
    Method to apply status effects before combat begins

    :param player1: Player representing left player
    :param player2: Player representing right player
    :param rules: Dictionary of current rules

    :return: Updated player1 and player2
    """
    if player1.status_effects:
        status_effects = json.loads(player1.status_effects)
        for status_effect in status_effects:
            # Apply the status effect
            player1, rules = getattr(combat_effects,
                                     'apply_' + status_effect['name'])(player=player1,
                                                                       rules=rules,
                                                                       left=True)

            # Decrease the duration of this status effect
            status_effects[status_effect]['value'] -= 1

            # Remove status effect if duration is 0
            if status_effects[status_effect]['value'] == 0:
                del status_effects[status_effect]

        player1.status_effects = str(status_effects)

    if player2.status_effects:
        status_effects = json.loads(player2.status_effects)
        for status_effect in status_effects:
            # Apply the status effect
            player2, rules = getattr(combat_effects,
                                     'apply_' + status_effect['name'])(player=player2,
                                                                       rules=rules,
                                                                       left=False)

            # Decrease the duration of this status effect
            status_effects[status_effect]['value'] -= 1

            # Remove status effect if duration is 0
            if status_effects[status_effect]['value'] == 0:
                del status_effects[status_effect]

        player2.status_effects = str(status_effects)

    return player1, player2, rules
