"""
Holds all combat effects logic

Inflict is to cause an affliction and add a status effect
Apply is to do something right away
"""
import json
from typing import Tuple, Any

Player = Any


def inflict_damage(value: int, player: Player) -> Player:
    """
    Deal damage

    :param value: How much damage to do to target
    :param player: The character being damaged

    :return: Updated Player
    """
    player.hit_points -= value

    return player


def inflict_percent_damage(value: int, player: Player) -> Player:
    """
    Deal percent max health damage

    :param value: How much % of max HP damage to do to target
    :param player: The character being damaged

    :return: Updated Player
    """
    player.hit_points -= int(round((value / 100.) * player.max_hit_points))

    return player


def inflict_heal(value: int, player: Player) -> Player:
    """
    Do healing

    :param value: How much damage to do to target
    :param player: The character being healed

    :return: Updated Player
    """
    player.hit_points += value

    return player


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def inflict_prone(value: int, player: Player) -> Player:
    """
    Make the target prone by adding the status effect to the target's statuses
    Next turn, target’s block does not beat area

    :param value: How long the effect lasts
    :param player: The list of status effects for a given player

    :return: Updated Player
    """
    player.status_effects.append(['prone', value])

    return player


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def apply_prone(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of prone to the player:
    Next turn, player’s block does not beat area.

    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict

    :return: Updated Player and ruleset
    """
    # "block": {"beats": ["attack"], "loses": ["disrupt", "dodge", "area"]}
    if left:
        # Remove area from the block: beats dict
        if "area" in rules["block"]["beats"]:
            rules["block"]["beats"].remove("area")

        # Add area to the block: loses dict
        if "area" not in rules["block"]["loses"]:
            rules["block"]["loses"].append("area")

    # "area": {"beats": ["disrupt", "dodge", "block"], "loses": ["attack"]}
    else:
        # Remove block from the area: loses dict
        if "block" in rules["area"]["loses"]:
            rules["area"]["loses"].remove("block")

        # Add block to the area: beats dict
        if "block" not in rules["area"]["beats"]:
            rules["area"]["beats"].append("block")

    return player, rules


# Enhanced effect of Dreamer's Fold Earth - disorient
def inflict_disorient(value: int, player: Player) -> Player:
    """
    Make the target disoriented by adding the status effect to the target's statuses

    :param value: How long the effect lasts
    :param player: The list of status effects for a given player

    :return: Updated Player
    """
    player.status_effects.append(['disorient', value])

    return player


# Enhanced effect of Dreamer's Fold Earth - disorient
def apply_disorient(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of disorient to the target:
    Next turn, target’s dodge does not beat attack.

    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict

    :return: Updated Player and ruleset
    """
    # "dodge": {"beats": ["block"], "loses": ["area", "disrupt", "attack"]}
    if left:
        # Remove area from the block: beats dict
        if "attack" in rules["dodge"]["beats"]:
            rules["dodge"]["beats"].remove("attack")

        # Add area to the block: loses dict
        if "attack" not in rules["dodge"]["loses"]:
            rules["dodge"]["loses"].append("attack")

    # "attack": {"beats": ["area", "disrupt", "dodge"], "loses": ["block"]}
    else:
        # Remove block from the area: loses dict
        if "dodge" in rules["attack"]["loses"]:
            rules["attack"]["loses"].remove("dodge")

        # Add block to the area: beats dict
        if "dodge" not in rules["attack"]["beats"]:
            rules["attack"]["beats"].append("dodge")

    return player, rules


# Enhanced effect of Chosen's Extreme Speed - haste
def inflict_haste(value: int, player: Player) -> Player:
    """
    Make the target hasted by adding the status effect to the target's statuses

    :param value: How long the effect lasts
    :param player: The character receiving the status effect

    :return: Updated player class
    """
    player.status_effects.append(['haste', value])

    return player


# Enhanced effect of Chosen's Extreme Speed - haste
def apply_haste(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of haste to the target:
    Next turn, target's attack will beat an opposing attack (no clash)

    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict

    :return: Updated Player and ruleset
    """
    # "attack": {"beats": ["disrupt", "area", "attack"], "loses": ["block", "dodge"]}
    if left:
        # Remove attack from the attack: loses dict
        if "attack" in rules["attack"]["loses"]:
            rules["attack"]["loses"].remove("attack")

        # Add attack to the attack: beats dict
        if "attack" not in rules["attack"]["beats"]:
            rules["attack"]["beats"].append("attack")

    # "attack": {"beats": ["disrupt", "area"], "loses": ["block", "dodge", "attack"]}
    else:
        # Remove attack from the attack: beats dict
        if "attack" in rules["attack"]["beats"]:
            rules["attack"]["beats"].remove("attack")

        # Add attack to the attack: loses dict
        if "attack" not in rules["attack"]["loses"]:
            rules["attack"]["loses"].append("attack")

    return player, rules


# Enhanced effect of NOT IMPLEMENTED
def inflict_delayed_double_damage(value: int, player: Player) -> Player:
    """
    Make the target's next attack do double damage by
    adding the status effect to the target's statuses

    :param value: How long the effect lasts
    :param player: The character receiving the status effect

    :return: Updated player class
    """
    player.status_effects.append(['delayed_double_damage', value])

    return player


# Enhanced effect of NOT IMPLEMENTED
def apply_delayed_double_damage(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of double_damage to the target:
    Next turn, target's attack will do double damage

    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict

    :return: Updated Player and ruleset
    """
    player = inflict_damage(value=100, player=player)

    return player, rules


# Enhanced effect of Chemist's Poison Dart
def inflict_poison(value: int, player: Player) -> Player:
    """
    Make the target take damage for value rounds by
    adding the status effect to the target's statuses

    :param value: How long the effect lasts
    :param player: The character receiving the status effect

    :return: Updated player class
    """
    player.status_effects.append(['poison', value])

    return player


# Enhanced effect of Chemist's Poison Dart
def apply_poison(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of poison to the target:
    Take 10% max HP damage

    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict

    :return: Updated Player and ruleset
    """
    player = inflict_percent_damage(value=10, player=player)

    return player, rules
