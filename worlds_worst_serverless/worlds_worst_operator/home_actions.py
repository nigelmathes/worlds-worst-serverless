from typing import Dict, Tuple, List

import boto3

try:
    from player_data import Player
    from arns import TEXT_ADVENTURE_ARN
    from common_actions import create_update_fields
except ImportError:
    from .player_data import Player
    from .arns import TEXT_ADVENTURE_ARN
    from .common_actions import create_update_fields


lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
ActionResponse = Tuple[Player, Player, Dict, Dict, List]

HOME_ACTIONS_MAP = {
    "placeholder": print('placeholding'),
}
