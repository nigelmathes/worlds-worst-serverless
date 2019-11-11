"""
All of these are integration tests requiring either DynamoDB local or
the actual worlds_worst_combat serverless arn/endpoint
"""

import boto3
import copy
import decimal
import json
import pytest
import uuid
from dataclasses import dataclass, asdict

from unittest import mock
from pytest_dynamodb import factories

from worlds_worst_serverless.worlds_worst_operator import handler

my_dynamodb_proc = factories.dynamodb_proc(
    dynamodb_dir="/Users/Nigel/dynamodb_local",
    port=8002,
    delay=False
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
    attack: str
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
        "attack": "attack",
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
            "action": "attack"
        }
    }


@pytest.fixture
def dynamodb_config(dynamodb: boto3.resource,
                    player: dict) -> boto3.resource:
    """
    Fixture to return a dynamodb resource initialized with a table

    :param dynamodb: Local DynamoDB fixture
    :param player: Input character; see above

    :return: boto3 resource with our tables
    """
    # create a table
    table = dynamodb.create_table(
        TableName='Table',
        AttributeDefinitions=[
            {
                'AttributeName': 'playerId',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                "AttributeName": 'playerId',
                "KeyType": 'HASH'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )

    # Put player into DB
    table.put_item(
        Item={
            'playerId': 'player_hash',
            'player_data': player
        },
    )

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
        TableName='Test',
        KeySchema=[
            {
                'AttributeName': 'playerId',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'playerId',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )

    _id = str(uuid.uuid4())

    # put an item into db
    table.put_item(
        Item={
            'playerId': _id,
            'test_key': 'test_value'
        },
    )

    # get the item
    item = table.get_item(
        Key={
            'playerId': _id,
        }
    )

    # check the content of the item
    assert item['Item']['test_key'] == 'test_value'


def test_get_player_info(player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a good event sent invokes the proper response

    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange - get entries from local mock database
    db_entry = dynamodb_config.get_item(
        Key={
            'playerId': 'player_hash',
        }
    )
    db_item = db_entry['Item']
    del db_item['playerId']
    player_from_db = json.loads(json.dumps(db_item, indent=4, cls=DecimalEncoder))
    expected_result = {'player_data': player}

    # Act
    test_result = handler.get_player_info(table=dynamodb_config,
                                          player_token='player_hash')

    # Assert
    assert test_result == expected_result
    assert test_result == player_from_db


def test_update_player_info(player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a good event sent invokes the proper response

    :param player: Input character dictionary
    :param dynamodb_config: boto3 resource with our tables
    """
    # Arrange - get entries from local mock database
    original_db_entry = dynamodb_config.get_item(
        Key={
            'playerId': 'player_hash',
        }
    )
    db_item = original_db_entry['Item']
    del db_item['playerId']
    original_player_from_db = json.loads(json.dumps(db_item, indent=4,
                                                    cls=DecimalEncoder))

    fields_to_update = dict()
    fields_to_update['hit_points'] = 400

    # Act
    test_result = handler.update_player_info(table=dynamodb_config,
                                             player_token='player_hash',
                                             update_map=fields_to_update)

    updated_db_entry = dynamodb_config.get_item(
        Key={
            'playerId': 'player_hash',
        }
    )
    db_item = updated_db_entry['Item']
    del db_item['playerId']
    updated_player_from_db = json.loads(json.dumps(db_item, indent=4,
                                                   cls=DecimalEncoder))

    # Assert
    assert original_player_from_db != updated_player_from_db
    assert updated_player_from_db['player_data']['hit_points'] == 400
    assert test_result['ResponseMetadata']['HTTPStatusCode'] == 200


def test_do_combat(mocker: mock, player: dict) -> None:
    """
    Test that a good combat request gets properly sent to our lambda function

    :param mocker: Pytest mock fixture
    :param player: Input character dictionary
    """
    # Arrange
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.random.choice",
                 return_value='block')
    input_player = Player(**player)
    expected_fields_to_update = {
        "hit_points": 400,
        "ex": 100
    }
    expected_message = [
        'Truckthunders uses attack!',
        'Test_Opponent uses block!',
        'Test_Opponent wins.'
    ]

    # Act
    updated_player, fields_to_update, message = handler.do_combat(input_player)

    # Assert
    assert input_player != updated_player
    assert fields_to_update == expected_fields_to_update
    assert message == expected_message


def test_route_tasks_and_response(mocker: mock, mock_event: dict,
                                  player: dict, dynamodb_config: boto3.resource) -> None:
    """
    Test that a combat action proceeds correctly and returns the right response

    :param mocker: Pytest mock fixture
    :param mock_event: Mock AWS lambda event dict
    :param player: Input character dictionary
    :param dynamodb_config: boto3 config with our resource
    """
    # Arrange
    # Mock all the things we already tested
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.random.choice",
                 return_value='block')
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.boto3.resource",
                 return_value=dynamodb_config)
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.os.environ",
                 return_value="Table")
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler"
                 ".get_player_info", return_value={'player_data': player})
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler"
                 ".update_player_info", return_value={})

    # Expect player to get hit for 100 damage and get 100 ex
    expected_player = Player(**player)
    expected_player.hit_points = 400
    expected_player.ex = 100

    expected_message = [
        "Truckthunders uses attack!",
        "Test_Opponent uses block!",
        "Test_Opponent wins."
    ]

    expected_action_results = json.dumps(
        {
            "Player": asdict(expected_player),
            "message": expected_message
        }
    )

    expected_response = {
        "statusCode": 200,
        "body": expected_action_results,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    response = handler.route_tasks_and_response(mock_event, mock_event)

    # Assert
    assert response == expected_response


def test_route_bad_id(mocker: mock, mock_event: dict,
                      dynamodb_config: boto3.resource) -> None:
    """
    Test that the operator router returns 401 Unauthorized if the player ID is wrong

    :param mocker: Pytest mock fixture
    :param mock_event: Mock AWS lambda event dict
    :param dynamodb_config: boto3 config with our resource
    """
    # Arrange
    # Mock all the things we already tested
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.random.choice",
                 return_value='block')
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.boto3.resource",
                 return_value=dynamodb_config)
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.os.environ",
                 return_value="Table")
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler"
                 ".get_player_info",
                 return_value={"Error": "Queried player does not exist."})
    mock_event["body"]["playerId"] = 'wrong_key'

    expected_response = {
        "statusCode": 401,
        "body": json.dumps({"Error": "Player does not exist in database"}),
        "message": json.dumps('Time to reroll.'),
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    response = handler.route_tasks_and_response(mock_event, mock_event)

    # Assert
    assert response == expected_response


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
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.random.choice",
                 return_value='block')
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.boto3.resource",
                 return_value=dynamodb_config)
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler.os.environ",
                 return_value="Table")
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler"
                 ".get_player_info",
                 return_value={'player_data': player})
    mocker.patch("worlds_worst_serverless.worlds_worst_operator.handler"
                 ".update_player_info", return_value={})

    altered_mock_event = copy.deepcopy(mock_event)
    altered_mock_event["body"]["Player"]["name"] = 'Dumb McDumbface'

    expected_response = {
            "statusCode": 403,
            "body": json.dumps({"Error": "Player information does not match"}),
            "headers": {"Access-Control-Allow-Origin": "*"},
        }

    # Act
    response = handler.route_tasks_and_response(altered_mock_event, mock_event)

    # Assert
    assert response == expected_response
"""
