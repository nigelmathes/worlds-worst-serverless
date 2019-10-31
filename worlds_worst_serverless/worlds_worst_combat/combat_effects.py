"""
Holds all combat effects logic

Inflict is to cause an affliction and add a status effect
Apply is to do something right away

All apply_* functions take these inputs and give these outputs:

apply_*(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    :param player: The player being affected
    :param rules: The rules dictionary to edit
    :param left: Whether the player is on the left for the sake of the rules dict
    :return: Updated Player and ruleset

All inflict_* functions take these inputs and give these outputs:

inflict_*(value: int, player: Player) -> Player:
    :param value: How much damage to do to target
    :param player: The character being damaged
    :return: Updated Player
"""
from random import randrange
from typing import Tuple, Any

Player = Any


def inflict_damage(value: int, player: Player) -> Player:
    """
    Deal damage
    """
    player.hit_points -= value

    return player


def inflict_percent_damage(value: int, player: Player) -> Player:
    """
    Deal percent max health damage
    """
    player.hit_points -= int(round((value / 100.0) * player.max_hit_points))

    return player


def inflict_heal(value: int, player: Player) -> Player:
    """
    Do healing
    """
    player.hit_points += value

    return player


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def inflict_prone(value: int, player: Player) -> Player:
    """
    Make the target prone.
    Next turn, block loses to area
    """
    player.status_effects.append(["prone", value])

    return player


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def apply_prone(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of prone to the player:
    block loses to area
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
    Next turn, dodge loses to attack
    """
    player.status_effects.append(["disorient", value])

    return player


# Enhanced effect of Dreamer's Fold Earth - disorient
def apply_disorient(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of disorient to the target:
    dodge loses to attack
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
    Make the target hasted.
    Next turn, target's attack will beat an opposing attack (no clash)
    """
    player.status_effects.append(["haste", value])

    return player


# Enhanced effect of Chosen's Extreme Speed - haste
def apply_haste(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of haste to the target:
    attack beats attack
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


# Enhanced effect of Chemist's Poison Dart
def inflict_poison(value: int, player: Player) -> Player:
    """
    Make the target take damage for value rounds by
    adding the status effect to the target's statuses
    """
    player.status_effects.append(["poison", value])

    return player


# Enhanced effect of Chemist's Poison Dart
def apply_poison(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of poison to the target:
    Take 10% max HP damage
    """
    player = inflict_percent_damage(value=10, player=player)

    return player, rules


# Enhanced effect of Cloistered's High Ground
def inflict_counter_attack(value: int, player: Player) -> Player:
    """
    Gain the high ground.
    Next turn, your area beats attack
    """
    player.status_effects.append(["counter_attack", value])

    return player


# Enhanced effect of Cloistered's High Ground
def apply_counter_attack(
    player: Player, rules: dict, left: bool
) -> Tuple[Player, dict]:
    """
    Apply the effects of counter_attack:
    area beats attack
    """
    # "area": {"beats": ["disrupt", "dodge", "attack"], "loses": ["block"]}
    if left:
        # Remove attack from the area: loses dict
        if "attack" in rules["area"]["loses"]:
            rules["area"]["loses"].remove("attack")

        # Add attack to the attack: beats dict
        if "attack" not in rules["area"]["beats"]:
            rules["area"]["beats"].append("attack")

    # "attack": {"beats": ["disrupt"], "loses": ["block", "dodge", "area"]},
    else:
        # Remove attack from the attack: beats dict
        if "area" in rules["attack"]["beats"]:
            rules["attack"]["beats"].remove("area")

        # Add attack to the attack: loses dict
        if "area" not in rules["attack"]["loses"]:
            rules["attack"]["loses"].append("area")

    return player, rules


# Enhanced effect of Cloistered's Broad Deflection
def inflict_counter_disrupt(value: int, player: Player) -> Player:
    """
    Expand your defense.
    Next turn, block beats disrupt
    """
    player.status_effects.append(["counter_disrupt", value])

    return player


# Enhanced effect of Cloistered's Broad Deflection
def apply_counter_disrupt(
    player: Player, rules: dict, left: bool
) -> Tuple[Player, dict]:
    """
    Apply the effects of counter_disrupt:
    block beats disrupt
    """
    # "block": {"beats": ["area", "attack", "disrupt"], "loses": ["dodge"]}
    if left:
        # Remove disrupt from the block: loses dict
        if "disrupt" in rules["block"]["loses"]:
            rules["block"]["loses"].remove("disrupt")

        # Add disrupt to the block: beats dict
        if "disrupt" not in rules["block"]["beats"]:
            rules["block"]["beats"].append("disrupt")

    # "disrupt": {"beats": ["dodge"], "loses": ["attack", "area", "block"]},
    else:
        # Remove block from the disrupt: beats dict
        if "block" in rules["disrupt"]["beats"]:
            rules["disrupt"]["beats"].remove("block")

        # Add block to the disrupt: loses dict
        if "block" not in rules["disrupt"]["loses"]:
            rules["disrupt"]["loses"].append("block")

    return player, rules


# Enhanced effect of Creator's Conjure Weaponry / Armory Shopping
def inflict_random_gun(value: int, player: Player) -> Player:
    """
    A gun materializes in your hands.
    Next turn, random effect:
        0) Pistol - Attack is now dodge
        1) Rifle - 1.5x damage
        2) Shotgun - Attack always clashes
        3) Rocket Launcher - Attack is now area

    """
    possible_status = ["pistol", "rifle", "shotgun", "rocket_launcher"]
    player.status_effects.append([possible_status[randrange(4)], value])

    return player


# Enhanced effect of Creator's Conjure Weaponry / Armory Shopping
# TODO: Test all random effects
def apply_pistol(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of pistol:
    attack is now dodge
    """
    # "attack": {"beats": ["attack", "block"], "loses": ["area", "disrupt"]}
    if left:
        rules["attack"] = rules["dodge"]

    # "area": {"beats": ["disrupt", "dodge", "attack"], "loses": ["block"]},
    # "attack": {"beats": ["disrupt", "area"], "loses": ["block", "dodge", "attack"]},
    # "block": {"beats": ["area"],  "loses": ["disrupt", "dodge", "attack"]},
    # "disrupt": {"beats": ["block", "dodge", "attack"], "loses": ["area"]},
    # "dodge": {"beats": ["block"], "loses": ["area", "disrupt"]}}
    else:
        for left_key in rules:
            for right_key in rules[left_key]:
                # If right has attack, remove it
                if "attack" in rules[left_key][right_key]:
                    rules[left_key][right_key].remove("attack")
                # If right has dodge, add attack
                if "dodge" in rules[left_key][right_key]:
                    rules[left_key][right_key].append("attack")

    return player, rules


# Enhanced effect of Creator's Conjure Weaponry / Armory Shopping
# TODO: Test all random effects
def apply_rifle(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of rifle:
    1.5x damage
    """
    player = inflict_damage(150, player)

    return player, rules


# Enhanced effect of Creator's Conjure Weaponry / Armory Shopping
# TODO: Test all random effects
def apply_shotgun(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of shotgun:
    attack always clashes
    """
    # "attack": {"beats": [], "loses": []}
    if left:
        rules["attack"] = {"beats": [], "loses": []}

    # "area": {"beats": ["disrupt", "dodge"], "loses": ["block"]},
    # "attack": {"beats": ["disrupt", "area"], "loses": ["block", "dodge"]},
    # "block": {"beats": ["area"],  "loses": ["disrupt", "dodge"]},
    # "disrupt": {"beats": ["block", "dodge"], "loses": ["area"]},
    # "dodge": {"beats": ["block"], "loses": ["area", "disrupt"]}}
    else:
        for left_key in rules:
            for right_key in rules[left_key]:
                # If beats or loses has attack, remove it
                if "attack" in rules[left_key][right_key]:
                    rules[left_key][right_key].remove("attack")

    return player, rules


# Enhanced effect of Creator's Conjure Weaponry / Armory Shopping
# TODO: Test all random effects
def apply_rocket_launcher(
    player: Player, rules: dict, left: bool
) -> Tuple[Player, dict]:
    """
    Apply the effects of rocket_launcher:
    attack is now area
    """
    # "attack": {"beats": ["disrupt", "dodge"], "loses": ["attack", "block"]},
    if left:
        rules["attack"] = rules["area"]

    # "area": {"beats": ["disrupt", "dodge"], "loses": ["block"]},
    # "attack": {"beats": ["disrupt", "area", "attack"], "loses": ["block", "dodge"]},
    # "block": {"beats": ["area", "attack"], "loses": ["disrupt", "dodge"]},
    # "disrupt": {"beats": ["block", "dodge"], "loses": ["area", "attack"]},
    # "dodge": {"beats": ["block"], "loses": ["area", "attack", "disrupt"]}
    else:
        for left_key in rules:
            for right_key in rules[left_key]:
                # If right has attack, remove it
                if "attack" in rules[left_key][right_key]:
                    rules[left_key][right_key].remove("attack")
                # If right has area, add attack
                if "area" in rules[left_key][right_key]:
                    rules[left_key][right_key].append("attack")

    return player, rules


# Enhanced effect of Hacker's Flicker
# TODO: Test this to make sure both anti attack and anti area are covered
def inflict_anti_attack(value: int, player: Player) -> Player:
    """
    Your character flickers in place, and attacks seem to go through you
    Next turn, take damage if player uses attack
    """
    player.status_effects.append(["anti_attack", value])

    return player


# Enhanced effect of Hacker's Flicker
# TODO: Test this to make sure both anti attack and anti area are covered
def apply_anti_attack(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of anti_attack:
    Take damage if player attacks
    """
    if player.attack == "attack":
        player = inflict_damage(100, player)

    return player, rules


# Enhanced effect of Hacker's Flicker
def inflict_anti_area(value: int, player: Player) -> Player:
    """
    Your character flickers in place, and attacks seem to go through you
    Next turn, take damage if player uses area
    """
    player.status_effects.append(["anti_area", value])

    return player


# Enhanced effect of Hacker's Flicker
def apply_anti_area(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of anti_attack:
    Take damage if player area
    """
    if player.attack == "area":
        player = inflict_damage(100, player)

    return player, rules


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def inflict_lag(value: int, player: Player) -> Player:
    """
    Make the target lag.
    Next turn, attack beats dodge
    """
    player.status_effects.append(["lag", value])

    return player


# Enhanced effect of Dreamer's Moving Sidewalk - prone
def apply_lag(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of lag to the player:
    attack beats dodge
    """
    # "attack": {"beats": ["disrupt", "area", "dodge"], "loses": ["block"]},
    if left:
        # Remove dodge from the attack: loses dict
        if "dodge" in rules["attack"]["loses"]:
            rules["attack"]["loses"].remove("dodge")

        # Add dodge to the attack: beats dict
        if "dodge" not in rules["attack"]["beats"]:
            rules["attack"]["beats"].append("dodge")

    # "dodge": {"beats": ["block"], "loses": ["area", "disrupt", "attack"]}}
    else:
        # Remove attack from the dodge: beats dict
        if "attack" in rules["dodge"]["beats"]:
            rules["dodge"]["beats"].remove("attack")

        # Add block to the area: beats dict
        if "attack" not in rules["dodge"]["loses"]:
            rules["dodge"]["loses"].append("attack")

    return player, rules


# Enhanced effect of Architect's Robot Phalanx / Swarm
def inflict_absorb(value: int, player: Player) -> Player:
    """
    Next turn, heal percent health damage you dealt
    """
    player.status_effects.append(["absorb", value])

    return player


# Enhanced effect of Architect's Robot Phalanx / Swarm
def apply_absorb(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of poison to the target:
    Heal a percentage of the damage you dealt last turn
    """
    player = inflict_heal(value=50, player=player)

    return player, rules


# Enhanced effect of Photonic's Light Barrier
def inflict_buff_attack(value: int, player: Player) -> Player:
    """
    Next turn, attack deals double damage.
    """
    player.status_effects.append(["buff_attack", value])

    return player


# Enhanced effect of Photonic's Light Barrier
def apply_double_damage(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of double_damage to the target:
    do double damage
    """
    if player.attack == "attack":
        player = inflict_damage(value=100, player=player)

    return player, rules


# Enhanced effect of Photonic's Solid Light
def inflict_connected(value: int, player: Player) -> Player:
    """
    Next turn, disrupt always clashes
    """
    player.status_effects.append(["connected", value])

    return player


# Enhanced effect of Photonic's Solid Light
def apply_connected(player: Player, rules: dict, left: bool) -> Tuple[Player, dict]:
    """
    Apply the effects of connected:
    disrupt always clashes
    """
    # "disrupt": {"beats": [], "loses": []}
    if left:
        rules["disrupt"] = {"beats": [], "loses": []}

    # "area": {"beats": ["dodge"], "loses": ["attack", "block"]},
    # "attack": {"beats": ["area"], "loses": ["block", "dodge"]},
    # "block": {"beats": ["area", attack],  "loses": ["dodge"]},
    # "disrupt": {"beats": ["block", "dodge"], "loses": ["attack", "area"]},
    # "dodge": {"beats": ["attack", "block"], "loses": ["area"]}}
    else:
        for left_key in rules:
            for right_key in rules[left_key]:
                # If beats or loses has attack, remove it
                if "disrupt" in rules[left_key][right_key]:
                    rules[left_key][right_key].remove("disrupt")

    return player, rules
