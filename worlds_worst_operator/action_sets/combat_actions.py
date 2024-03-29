import json
import random

from dataclasses import asdict
from typing import Dict, Tuple, List

import boto3

try:
    from database_ops import get_player
    from player_data import Player
    from arns import COMBAT_ARN
    from action_sets.common_actions import create_update_fields
except ImportError:
    from ..database_ops import get_player
    from ..player_data import Player
    from ..arns import COMBAT_ARN
    from .common_actions import create_update_fields


lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]


def do_combat(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Do combat based on a Player and that Player's target

    :param player: Dataclass holding player data
    :param table: DynamoDB table object

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    # Get target from the database
    target_query = get_player(table=table, player_token=player.target)
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
        return player, player, dict(), dict(), message

    # Make the target attack
    possible_attacks = ["attack", "area", "block", "disrupt", "dodge"]
    target.action = random.choice(possible_attacks)
    # target.enhanced = random.choice([True, False])

    data = {"body": {"Player1": asdict(player), "Player2": asdict(target)}}
    payload = json.dumps(data)

    # Invoke the combat lambda
    response = lambda_client.invoke(
        FunctionName=COMBAT_ARN, InvocationType="RequestResponse", Payload=payload
    )
    # response of the form:
    # {
    #     "statusCode": 200,
    #     "body": combat_results,
    #     "headers": {"Access-Control-Allow-Origin": "*"},
    # }
    response_payload = json.loads(response.get("Payload").read())
    result = json.loads(response_payload["body"])

    message = result["message"]
    updated_player = Player(**result["Player1"])
    updated_target = Player(**result["Player2"])
    player_updates = create_update_fields(player, updated_player)
    target_updates = create_update_fields(target, updated_target)

    if updated_player.hit_points <= 0:
        message.append(f"{player.name} died! Rezzing. Die less you scrub.")
        # Reset player and set context to home
        player_updates["hit_points"] = player.max_hit_points
        player_updates["ex"] = 0
        player_updates["status_effects"] = list()
        player_updates["context"] = "home"
        player_updates["target"] = ""

        # Reset target
        target_updates["hit_points"] = target.max_hit_points
        target_updates["ex"] = 0
        target_updates["status_effects"] = list()
    elif updated_target.hit_points <= 0:
        message.append(f"{target.name} died! Rezzing. Great job winning.")
        # Reset player and set context to home
        player_updates["hit_points"] = player.max_hit_points
        player_updates["ex"] = 0
        player_updates["status_effects"] = list()
        player_updates["context"] = "home"
        player_updates["target"] = ""

        # Reset target
        target_updates["hit_points"] = target.max_hit_points
        target_updates["ex"] = 0
        target_updates["status_effects"] = list()
    else:
        message.append(f"{target.name} has {updated_target.hit_points} HP left.")

    return updated_player, updated_target, player_updates, target_updates, message


def run_away(player: Player, table: dynamodb.Table) -> ActionResponse:
    """
    Runs away from combat.
    Switches player.context back to "home".
    Preserves target.

    :param player: Dataclass holding player data
    :param table: DynamoDB table object

    :return: Updated Player dataclass and dict of fields to update, and a message
    """
    updated_player = Player(**asdict(player))
    updated_player.context = "home"

    player_updates = create_update_fields(player, updated_player)

    message = ["You ran away!"]

    return updated_player, player, player_updates, {}, message


COMBAT_ACTIONS_MAP = {
    "attack": do_combat,
    "area": do_combat,
    "block": do_combat,
    "disrupt": do_combat,
    "dodge": do_combat,
    "run": run_away,
    "run away": run_away,
    "flee": run_away,
    "escape": run_away,
    "quit": run_away
}
