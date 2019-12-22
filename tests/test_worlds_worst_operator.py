"""
All of these are integration tests requiring either DynamoDB local or
the actual worlds_worst_combat serverless arn/endpoint
"""

import boto3
import decimal
import json
import pytest
import uuid
from dataclasses import dataclass, asdict

from unittest import mock
from pytest_dynamodb import factories

from worlds_worst_serverless.worlds_worst_operator import operator
from worlds_worst_serverless.worlds_worst_operator import database_ops
from worlds_worst_serverless.worlds_worst_operator import actions

my_dynamodb_proc = factories.dynamodb_proc(
    dynamodb_dir="/Users/nmathes/dynamodb_local", port=8002, delay=False
)
dynamodb = factories.dynamodb("my_dynamodb_proc")


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    """
    This is a workaround for: http://bugs.python.org/issue16535
    """

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


@dataclass
class Player:
    """
    Class to hold player information
    """

    name: str
    character_class: str
    max_hit_points: int
    max_ex: int
    hit_points: int
    ex: int
    status_effects: list
    action: str
    enhanced: bool


@pytest.fixture
def player():
    return {
        "name": "Truckthunders",
        "character_class": "Dreamer",
        "max_hit_points": 500,
        "max_ex": 1000,
        "hit_points": 500,
        "ex": 0,
        "status_effects": [],
        "action": "attack",
        "enhanced": False,
    }


@pytest.fixture
def mock_event(player: dict) -> dict:
    """
    Fixture to create an AWS Lambda event dict

    :param player: Input character; see above
    :return: Mock event dict
    """
    return {
        "body": {
            "Player": player,
            "playerId": "player_hash",
            "action": "attack",
            "enhanced": False,
        }
    }


@pytest.fixture
def dynamodb_config(dynamodb: boto3.resource, player: dict) -> boto3.resource:
    """
    Fixture to return a dynamodb resource initialized with a table

    :param dynamodb: Local DynamoDB fixture
    :param player: Input character; see above

    :return: boto3 resource with our tables
    """
    # create a table
    table = dynamodb.create_table(
        TableName="Table",
        AttributeDefinitions=[{"AttributeName": "playerId", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "playerId", "KeyType": "HASH"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Put player into DB
    table.put_item(Item={"playerId": "player_hash", "player_data": player})

    # Put target into DB
    table.put_item(Item={"playerId": "target_hash", "player_data": player})

    return table


def test_dynamodb(dynamodb: boto3.resource):
    """
    Simple test for DynamoDB.
    # Create a table
    # Put an item
    # Get the item and check the content of this item
    """
    # create a table
    table = dynamodb.create_table(
        TableName="Test",
        KeySchema=[{"AttributeName": "playerId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "playerId", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    _id = str(uuid.uuid4())

    # put an item into db
    table.put_item(Item={"playerId": _id, "test_key": "test_value"})

    # get the item
    item = table.get_item(Key={"playerId": _id})

    # check the content of the item
    assert item["Item"]["test_key"] == "test_value"


def test_get_player(player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a good event sent invokes the proper response

    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange - get entries from local mock database
    db_entry = dynamodb_config.get_item(Key={"playerId": "player_hash"})
    db_item = db_entry["Item"]
    del db_item["playerId"]
    player_from_db = json.loads(json.dumps(db_item, indent=4, cls=DecimalEncoder))
    expected_result = {"player_data": player}

    # Act
    test_result = database_ops.get_player(
        table=dynamodb_config, player_token="player_hash"
    )

    # Assert
    assert test_result == expected_result
    assert test_result == player_from_db


def test_update_player(player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a good event sent invokes the proper response

    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange - get entries from local mock database
    original_db_entry = dynamodb_config.get_item(Key={"playerId": "player_hash"})
    db_item = original_db_entry["Item"]
    del db_item["playerId"]
    original_player_from_db = json.loads(
        json.dumps(db_item, indent=4, cls=DecimalEncoder)
    )

    fields_to_update = dict()
    fields_to_update["hit_points"] = 400

    # Act
    test_result = operator.update_player(
        table=dynamodb_config, player_token="player_hash", update_map=fields_to_update
    )

    updated_db_entry = dynamodb_config.get_item(Key={"playerId": "player_hash"})
    db_item = updated_db_entry["Item"]
    del db_item["playerId"]
    updated_player_from_db = json.loads(
        json.dumps(db_item, indent=4, cls=DecimalEncoder)
    )

    # Assert
    assert original_player_from_db != updated_player_from_db
    assert updated_player_from_db["player_data"]["hit_points"] == 400
    assert test_result["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_change_class(player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that we can change character class

    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange - get entries from local mock database
    db_entry = dynamodb_config.get_item(Key={"playerId": "player_hash"})
    db_item = db_entry["Item"]
    player_from_db = json.loads(json.dumps(db_item, indent=4, cls=DecimalEncoder))

    # Act
    updated_player, _, player_updates, _, message = actions.change_class(
        player=Player(**player), new_class='hacker'
    )

    #db_entry = dynamodb_config.get_item(Key={"playerId": "player_hash"})
    #db_item = db_entry["Item"]
    #updated_player = json.loads(json.dumps(db_item, indent=4, cls=DecimalEncoder))

    # Assert
    assert player_from_db != updated_player
    assert player_updates == {'character_class': 'hacker'}
    assert message == ['Changed class from Dreamer to hacker']


def test_do_combat(mocker: mock, player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a good combat request gets properly sent to our lambda function

    :param mocker: Pytest mock fixture
    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.actions.random.choice",
        return_value="attack",
    )

    input_player = Player(**player)
    expected_player_updates = {"hit_points": 400, "ex": 150}
    expected_target_updates = expected_player_updates
    expected_message = [
        "Truckthunders uses attack!",
        "Truckthunders uses attack!",
        "Truckthunders and Truckthunders tie.",
        "Truckthunders has 400 HP left.",
    ]

    # Act
    updated_player, updated_target, player_updates, target_updates, message = operator.do_combat(
        player=input_player, table=dynamodb_config
    )

    # Assert
    assert input_player != updated_player
    assert player_updates == expected_player_updates
    assert target_updates == expected_target_updates
    assert message == expected_message


def test_route_tasks_and_response(
    mocker: mock, mock_event: dict, player: dict, dynamodb_config: boto3.resource
) -> None:
    """
    Test that a combat action proceeds correctly and returns the right response

    :param mocker: Pytest mock fixture
    :param mock_event: Mock AWS lambda event dict
    :param player: Input character dictionary
    :param dynamodb_config: boto3 config with our resource
    """
    # Arrange
    # Mock all the things we already tested
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.actions.random.choice",
        return_value="block",
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.operator.boto3.resource",
        return_value=dynamodb_config,
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.operator.os.environ",
        return_value="Table",
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.actions.get_player",
        return_value={"player_data": player},
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.database_ops.get_player",
        return_value={"player_data": player},
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.operator.update_player",
        return_value={},
    )

    # Expect player to get hit for 100 damage and get 100 ex
    expected_player = Player(**player)
    expected_player.hit_points = 400
    expected_player.ex = 100

    expected_message = [
        "Truckthunders uses attack!",
        "Truckthunders uses block!",
        "Truckthunders wins.",
        "Truckthunders has 500 HP left.",
    ]

    expected_action_results = json.dumps(
        {"Player": asdict(expected_player), "message": expected_message}
    )

    expected_response = {
        "statusCode": 200,
        "body": expected_action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    response = operator.route_tasks_and_response(mock_event, mock_event)

    # Assert
    assert response == expected_response


def test_route_bad_id(
    mocker: mock, mock_event: dict, dynamodb_config: boto3.resource
) -> None:
    """
    Test that the operator router returns 401 Unauthorized if the player ID is wrong

    :param mocker: Pytest mock fixture
    :param mock_event: Mock AWS lambda event dict
    :param dynamodb_config: boto3 config with our resource
    """
    # Arrange
    # Mock all the things we already tested
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.actions.random.choice",
        return_value="block",
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.operator.boto3.resource",
        return_value=dynamodb_config,
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.operator.os.environ",
        return_value="Table",
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.actions" ".get_player",
        return_value={"Error": "Queried player does not exist."},
    )
    mocker.patch(
        "worlds_worst_serverless.worlds_worst_operator.database_ops.get_player",
        return_value={"Error": "Queried player does not exist."},
    )
    mock_event["body"]["playerId"] = "wrong_key"

    expected_response = {
        "statusCode": 401,
        "body": json.dumps({"Error": "Player does not exist in database"}),
        "message": json.dumps("Time to reroll."),
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    response = operator.route_tasks_and_response(mock_event, mock_event)

    # Assert
    assert response == expected_response


def test_reset_characters(
    mock_event: dict, player: dict, dynamodb_config: boto3.resource
) -> None:
    """
    Test that a reset request loads the default players and resets the database

    :param mock_event: Mock AWS lambda event dict
    :param player: Input character dictionary
    :param dynamodb_config: boto3 config with our resource
    """
    # Arrange
    expected_player = Player(**player)

    expected_message = []

    expected_action_results = json.dumps(
        {"Player": asdict(expected_player), "message": expected_message}
    )

    expected_response = {
        "statusCode": 200,
        "body": expected_action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    response = operator.reset_characters(table=dynamodb_config)
    response = json.loads(response['body'])

    # Assert
    assert len(response['message']) == 8


def test_route_action() -> None:
    """
    Test that the route_action method's fuzzy matching works
    """
    # Arrange
    expected_action = "attack"
    expected_function = operator.do_combat

    # Act
    routed_action, function_to_run = operator.route_action("attac")

    # Assert
    assert routed_action == expected_action
    assert function_to_run == expected_function


""" TODO: Make this not FUBAR
def test_route_bad_character(mocker: mock, mock_event: dict, player: dict,
                             dynamodb_config: boto3.resource) -> None:
    
    Test that the operator router returns 403 Forbidden if the input
    player does not match the player in the database

    :param mocker: Pytest mock fixture
    :param mock_event: Mock AWS lambda event dict
    :param player: Input character dictionary
    :param dynamodb_config: boto3 config with our resource
    
    # Arrange
    # Mock all the things we already tested
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.operator.random.choice",
                 return_value='block')
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.operator.boto3.resource",
                 return_value=dynamodb_config)
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.operator.os.environ",
                 return_value="Table")
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.operator"
                 ".get_player",
                 return_value={'player_data': player})
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.operator"
                 ".update_player", return_value={})

    altered_mock_event = copy.deepcopy(mock_event)
    altered_mock_event["body"]["Player"]["name"] = 'Dumb McDumbface'

    expected_response = {
            "statusCode": 403,
            "body": json.dumps({"Error": "Player information does not match"}),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }

    # Act
    response = operator.route_tasks_and_response(altered_mock_event, mock_event)

    # Assert
    assert response == expected_response
"""
