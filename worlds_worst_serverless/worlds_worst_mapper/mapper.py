try:
    import unzip_requirements
except ImportError:
    pass

import json
from typing import Dict, Any

from fuzzywuzzy import process


try:
    from guidelines import ACTIONS_MAP
except ImportError:
    from .guidelines import ACTIONS_MAP

LambdaDict = Dict[str, Any]


def get_matching_action(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function to receive an action and find the closest matching action in
    the ACTIONS_MAP dictionary.

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Function name corresponding to the best matching action
    """
    # Decode the request
    request_body = event.get("body")
    if type(request_body) == str:
        request_body = json.loads(request_body)
    command_to_match = request_body["action"]

    possible_actions = ACTIONS_MAP.keys()

    matched_action = process.extractOne(command_to_match, possible_actions)

    function_to_execute = ACTIONS_MAP[matched_action[0]]

    result = {
        "statusCode": 200,
        "body": function_to_execute,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    print(f"Sending response: {result}")
    return result
