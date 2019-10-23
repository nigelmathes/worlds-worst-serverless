import pytest

from worlds_worst_serverless.worlds_worst_combat.handler import do_combat


@pytest.fixture
def player1():
    return {
        'name': 'Truckthunders',
        'character_class': 'Dreamer',
        'max_hit_points': 500,
        'max_ex': 1000,
        'hit_points': 500,
        'ex': 0,
        'status_effects': '[]',
        'attack': 'attack',
        'enhanced': 'False'
    }


@pytest.fixture
def player2():
    return {
        'name': 'Crunchbucket',
        'character_class': 'Cloistered',
        'max_hit_points': 500,
        'max_ex': 1000,
        'hit_points': 500,
        'ex': 0,
        'status_effects': '[]',
        'attack': 'area',
        'enhanced': 'False'
    }


@pytest.fixture
def mock_event(player1: dict, player2: dict) -> dict:
    """
    Fixture to create an AWS Lambda event dict

    :param player1: Input character 1 see above
    :param player2: Input character 2 see above
    :return: Mock event dict
    """
    return {
        'body': {
            'player1': player1,
            'player2': player2
        }
    }


def test_combat_round(mock_event: dict) -> None:
    """
    Test a full combat round

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    expected_player2_hp = 400

    # Act
    combat_result = do_combat(mock_event, mock_event)

    # Assert
    print(combat_result)
    assert combat_result['body']['Player2']['hit_points'] == expected_player2_hp
