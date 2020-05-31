from dataclasses import asdict
from pathlib import Path
from typing import Dict, Tuple, List

import boto3

try:
    from player_data import Player
    from action_sets.common_actions import create_update_fields
except ImportError:
    from ..player_data import Player
    from ..action_sets.common_actions import create_update_fields


lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]


def _get_games_list() -> List:
    """
    Helper function to strip file extensions from the GAMES_LIST to output
    available games to the player.

    :return: List of possible game names.
    """
    games_list = []
    for game in GAMES_LIST:
        games_list.append(Path(game).stem)

    return games_list


def which_game(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Asks the user which game they would like to play, with clarifying syntax.

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object (unused)

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    message = [
        f"Which game would you like to play? You can select from this list by saying, "
        f"for example: zork2\n {_get_games_list()}"
    ]

    return player, player, {}, {}, message


def play_text_adventure(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Sets the context to "text_adventure" and the target to the selected
    text adventure game.

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object (unused)

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    updated_player = Player(**asdict(player))

    matched_game = [s for s in GAMES_LIST if player.action in s][0]

    if matched_game:
        game_name = Path(matched_game).stem
        message = [f"You found {game_name}! You initialize the program and begin "
                   f"playing. What is your first command? Look is normally a good start. "
                   f"If you want to stop playing {game_name}, type the word quit"]

        updated_player.context = "text_adventure"
        updated_player.target = game_name

        player_updates = create_update_fields(player, updated_player)

        return player, player, player_updates, player_updates, message

    else:
        message = [f"Could not find {player.action}...Are you sure you typed that "
                   f"correctly? Here's the game list: {_get_games_list()}"]

        return player, player, {}, {}, message


HOME_ACTIONS_MAP = {
    "play a game": which_game,
    "play text adventure": which_game,
    "905": play_text_adventure,
    "acorncourt": play_text_adventure,
    "advent": play_text_adventure,
    "adventureland": play_text_adventure,
    "afflicted": play_text_adventure,
    "anchor": play_text_adventure,
    "awaken": play_text_adventure,
    "balances": play_text_adventure,
    "ballyhoo": play_text_adventure,
    "curses": play_text_adventure,
    "cutthroat": play_text_adventure,
    "deephome": play_text_adventure,
    "detective": play_text_adventure,
    "dragon": play_text_adventure,
    "enchanter": play_text_adventure,
    "enter": play_text_adventure,
    "gold": play_text_adventure,
    "hhgg": play_text_adventure,
    "hollywood": play_text_adventure,
    "huntdark": play_text_adventure,
    "infidel": play_text_adventure,
    "inhumane": play_text_adventure,
    "jewel": play_text_adventure,
    "karn": play_text_adventure,
    "lgop": play_text_adventure,
    "library": play_text_adventure,
    "loose": play_text_adventure,
    "lostpig": play_text_adventure,
    "ludicorp": play_text_adventure,
    "lurking": play_text_adventure,
    "moonlit": play_text_adventure,
    "murdac": play_text_adventure,
    "night": play_text_adventure,
    "omniquest": play_text_adventure,
    "partyfoul": play_text_adventure,
    "pentari": play_text_adventure,
    "planetfall": play_text_adventure,
    "plundered": play_text_adventure,
    "reverb": play_text_adventure,
    "seastalker": play_text_adventure,
    "sherlock": play_text_adventure,
    "snacktime": play_text_adventure,
    "sorcerer": play_text_adventure,
    "spellbrkr": play_text_adventure,
    "spirit": play_text_adventure,
    "temple": play_text_adventure,
    "theatre": play_text_adventure,
    "trinity": play_text_adventure,
    "tryst205": play_text_adventure,
    "weapon": play_text_adventure,
    "wishbringer": play_text_adventure,
    "yomomma": play_text_adventure,
    "zenon": play_text_adventure,
    "zork1": play_text_adventure,
    "zork2": play_text_adventure,
    "zork3": play_text_adventure,
    "ztuu": play_text_adventure,
}

GAMES_LIST = [
    "905.z5",
    "acorncourt.z5",
    "advent.z5",
    "adventureland.z5",
    "afflicted.z8",
    "anchor.z8",
    "awaken.z5",
    "balances.z5",
    "ballyhoo.z3",
    "curses.z5",
    "cutthroat.z3",
    "deephome.z5",
    "detective.z5",
    "dragon.z5",
    "enchanter.z3",
    "enter.z5",
    "gold.z5",
    "hhgg.z3",
    "hollywood.z3",
    "huntdark.z5",
    "infidel.z3",
    "inhumane.z5",
    "jewel.z5",
    "karn.z5",
    "lgop.z3",
    "library.z5",
    "loose.z5",
    "lostpig.z8",
    "ludicorp.z5",
    "lurking.z3",
    "moonlit.z5",
    "murdac.z5",
    "night.z5",
    "omniquest.z5",
    "partyfoul.z8",
    "pentari.z5",
    "planetfall.z3",
    "plundered.z3",
    "reverb.z5",
    "seastalker.z3",
    "sherlock.z5",
    "snacktime.z8",
    "sorcerer.z3",
    "spellbrkr.z3",
    "spirit.z5",
    "temple.z5",
    "theatre.z5",
    "trinity.z4",
    "tryst205.z5",
    "weapon.z5",
    "wishbringer.z3",
    "yomomma.z8",
    "zenon.z5",
    "zork1.z5",
    "zork2.z5",
    "zork3.z5",
    "ztuu.z5",
]
