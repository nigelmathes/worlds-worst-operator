import json

from dataclasses import asdict
from pathlib import Path
from typing import Dict, Tuple, List

import boto3

try:
    from player_data import Player
    from database_ops import get_player
    from action_sets.common_actions import create_update_fields
except ImportError:
    from ..player_data import Player
    from ..database_ops import get_player
    from .common_actions import create_update_fields

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
        f"Which game would you like to play?",
        "You can select from this list by saying, for example: zork2",
        "Select from any of the following games (no need to type the quotes):",
        f"{_get_games_list()}"
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
        message = [
            f"You found {game_name}! You initialize the program and begin "
            f"playing. What is your first command? Look is normally a good start. "
            f"If you want to stop playing {game_name}, type the word quit"
        ]

        updated_player.context = "text_adventure"
        updated_player.target = game_name
        updated_player.history = []

        player_updates = create_update_fields(player, updated_player)

        return player, player, player_updates, player_updates, message

    else:
        message = [
            f"Could not find {player.action}...Are you sure you typed that "
            f"correctly? Here's the game list: {_get_games_list()}"
        ]

        return player, player, {}, {}, message


def start_combat(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Begins combat with a target entity fetched from the database or created

    :param player: The original player, before actions were taken
    :param table: DynamoDB table object

    :return: Changes player.context to "combat" and assigns player.target
    """
    message = []
    if player.context == "home":
        message.append("Starting shit in your own home? Sounds good to me."
                       " Getting you a target to fight.")

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

    player_updates = {}
    player_updates["context"] = "combat"
    player_updates["target"] = target_token

    target_updates = {}
    target_updates["context"] = "combat"
    target_updates["target"] = player.name

    message.append(f"You're in combat with {target.name}!")

    return player, target, player_updates, target_updates, message


def describe_home(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Describe the interior of a players' home
    """
    message = [
        "You are in your home, a small room apart from the rest of the world.",
        "There is a bed, a dresser, and a small hologram which "
        "displays the words, 'Say Play a Game to Begin!'",
        "There is also a target dummy in one corner."
    ]

    return player, player, {}, {}, message


def quit_message(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Tell the player they can quit by logging out
    """
    message = [
        "To quit, press the logout button above! If this was a mistake, "
        "try looking around or going outside."
    ]

    return player, player, {}, {}, message


HOME_ACTIONS_MAP = {
    "play": which_game,
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
    "attack": start_combat,
    "block": start_combat,
    "dodge": start_combat,
    "disrupt": start_combat,
    "area": start_combat,
    "fight": start_combat,
    "combat": start_combat,
    "look": describe_home,
    "look around": describe_home,
    "explore": describe_home,
    "quit": quit_message
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
