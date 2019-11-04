import boto3
import json
import pytest
import uuid

from pytest_dynamodb import factories

from worlds_worst_serverless.worlds_worst_operator import handler

my_dynamodb_proc = factories.dynamodb_proc(
    dynamodb_dir="/Users/Nigel/dynamodb_local",
    port=8002,
    delay=False,
)
dynamodb = factories.dynamodb("my_dynamodb_proc")


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
        "enhanced": "False",
    }


@pytest.fixture
def mock_event(player: dict) -> dict:
    """
    Fixture to create an AWS Lambda event dict

    :param player: Input character; see above
    :return: Mock event dict
    """
    return {
        "statusCode": 200,
        "body": {
            "Player": player,
            "id": "player_hash",
            "action": "attack"
        },
        "headers": {"Access-Control-Allow-Origin": "*"}
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
        TableName='TestPlayers',
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                "AttributeName": "id",
                "KeyType": "HASH"
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
            'id': 'player_hash',
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
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
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
            'id': _id,
            'test_key': 'test_value'
        },
    )

    # get the item
    item = table.get_item(
        Key={
            'id': _id,
        }
    )

    # check the content of the item
    assert item['Item']['test_key'] == 'test_value'


def test_route_tasks_and_response(mock_event: dict,
                                  player: dict,
                                  dynamodb_config: boto3.resource) -> None:
    """
    Test that a good event sent invokes the proper response

    :param dynamodb_config: boto3 resource with our tables
    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange - get entries from local mock database
    player_from_db = dynamodb_config.get_item(
        Key={
            'id': 'player_hash',
        }
    )
    expected_result = json.dumps(
        {"Player": player, "response": None}
    )
    expected_response = {
        "statusCode": 200,
        "body": expected_result,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    test_response = handler.route_tasks_and_response(event=mock_event,
                                                     context=mock_event)

    # Assert
    assert test_response == expected_response
