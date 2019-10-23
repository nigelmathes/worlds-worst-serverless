"""
Holds all combat logic
"""
import json
from typing import Tuple, Any

from . import combat_effects

Player = Any


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


def find_ability(abilities: list, character_class: str, attack_type: str):
    """
    Function to find the right ability to use for a given combat outcome

    :param abilities: List of dicts of abilities read in from abilities.json
    :param character_class: Name of character class
    :param attack_type: Name of attack
    :return: Ability dict entry
    """
    # Find the ability to use
    ability_to_use = {'effects': [], 'enhancements': []}
    for ability in abilities:
        if (ability['class'] == character_class) \
                and (ability['type'] == attack_type):
            ability_to_use = ability
            break

    return ability_to_use


def apply_ability_effects(ability: dict, target: Player, self: Player) -> \
        None:
    """
    Apply the effects of the given ability

    :param ability: The ability dict
    :param target: Target, as in enemy. The one being damaged, if damage is done
    :param self: Self, as in the user of the ability.
    """
    for effect in ability['effects']:
        if effect['target'] == 'target':
            getattr(combat_effects, 'inflict_' + effect['effect'])(
                value=effect['value'],
                player=target)
        elif effect['target'] == 'self':
            getattr(combat_effects, 'inflict_' + effect['effect'])(
                value=effect['value'],
                player=self)


def apply_enhancements(ability: dict, target: Player, self: Player) -> \
        None:
    """
    Apply the effects of the given ability's enhancements

    :param ability: The ability dict
    :param target: Target, as in enemy. The one being damaged, if damage is done
    :param self: Self, as in the user of the ability.
    """
    print(ability)
    for enhancement in ability['enhancements']:
        if enhancement['target'] == 'target':
            getattr(combat_effects, 'inflict_' + enhancement['effect'])(
                value=enhancement['value'],
                player=target)
        elif enhancement['target'] == 'self':
            getattr(combat_effects, 'inflict_' + enhancement['effect'])(
                value=enhancement['value'],
                player=self)