import copy
import json
import pytest
from pathlib import Path

from worlds_worst_serverless.worlds_worst_combat.handler import do_combat
from worlds_worst_serverless.worlds_worst_combat import combat_effects


@pytest.fixture
def player1():
    return {
        'name': 'Truckthunders',
        'character_class': 'Dreamer',
        'max_hit_points': 500,
        'max_ex': 1000,
        'hit_points': 500,
        'ex': 0,
        'status_effects': [],
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
        'status_effects': [],
        'attack': 'area',
        'enhanced': 'False'
    }


@pytest.fixture
def abilities() -> dict:
    """
    Fixture to read abilities.json and provide the dict
    :return: The abilities dict
    """
    # Read in the abilities data
    path_to_file = Path.cwd().parent / 'worlds_worst_serverless' / \
                   'worlds_worst_combat' / 'abilities.json'
    with path_to_file.open() as json_file:
        abilities = json.load(json_file)

    return abilities


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
            'Player1': player1,
            'Player2': player2
        }
    }


def test_combat_round_p1_wins(mock_event: dict, abilities: dict) -> None:
    """
    Test a full combat round where Player1 wins

    :param mock_event: Mock AWS lambda event dict
    :param abilities: The abilities dict, read in from abilities.json
    """
    # Arrange
    expected_player2_hp = mock_event['body']['Player2']['hit_points'] - abilities[2][
        'effects'][0]['value']

    # Act
    combat_result = do_combat(mock_event, mock_event)

    # Assert
    assert combat_result['body']['Player2']['hit_points'] == expected_player2_hp


def test_matchups(mock_event: dict) -> None:
    """
    Test that the following holds true:

    Area beats Disrupt and Dodge
    Attack beats Disrupt and Area
    Block beats Attack and Area
    Disrupt beats Block and Dodge
    Dodge beats Attack and Block

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    player1_attacks = ['area', 'attack', 'block', 'disrupt', 'dodge']
    player2_attacks = ['area', 'attack', 'block', 'disrupt', 'dodge']
    expected_player1_hps = [[0, 0, 0, 100, 100],
                            [100, 0, 0, 100, 0],
                            [100, 100, 0, 0, 0],
                            [0, 0, 100, 0, 100],
                            [0, 100, 100, 0, 0]]
    expected_player2_hps = [[0, 100, 100, 0, 0],
                            [0, 0, 100, 0, 100],
                            [0, 0, 0, 100, 100],
                            [100, 100, 0, 0, 0],
                            [100, 0, 0, 100, 0]]

    # Act
    # Perform a round of combat
    for i, player1_attack in enumerate(player1_attacks):
        for j, player2_attack in enumerate(player2_attacks):
            mock_event['body']['Player1']['attack'] = player1_attack
            mock_event['body']['Player2']['attack'] = player2_attack

            combat_result = do_combat(mock_event, mock_event)

            # Assert - The 400 is a kluge because I don't want to remake the list
            assert combat_result['body']['Player1']['hit_points'] == 400 + \
                   expected_player1_hps[i][j]
            assert combat_result['body']['Player2']['hit_points'] == 400 + \
                   expected_player2_hps[i][j]


def test_check_dead(mock_event: dict) -> None:
    """
    Test that the check_dead() method works as expected

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event['body']['Player1']['hit_points'] = 0

    # Add the expected status code to the dict
    mock_event['statusCode'] = 200

    # Act
    combat_result = do_combat(mock_event, mock_event)

    # Assert nothing has changed and the combat result equals the input dict
    assert combat_result == mock_event


@pytest.mark.parametrize("ability_combo,expected_status",
                         [(["disrupt", "block"], [['prone', 1]]),
                          (["area", "disrupt"], [['disorient', 1]])])
def test_enhancements(mock_event: dict, ability_combo: list, expected_status: list) \
        -> None:
    """
    Test that a enhancements are applied properly

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event['body']['Player1']['enhanced'] = True
    mock_event['body']['Player1']['attack'] = ability_combo[0]
    mock_event['body']['Player2']['attack'] = ability_combo[1]

    expected_player1_hp = mock_event['body']['Player1']['hit_points']
    expected_player2_hp = mock_event['body']['Player2']['hit_points'] - 100

    # Act
    # Perform a round of combat
    combat_result = do_combat(mock_event, mock_event)

    # Assert
    assert combat_result['body']['Player1']['hit_points'] == expected_player1_hp
    assert combat_result['body']['Player2']['hit_points'] == expected_player2_hp
    assert combat_result['body']['Player2']['status_effects'] == expected_status


def test_multiple_status(mock_event: dict) -> None:
    """
    Test that status effects get correctly applied/updated when there are multiple

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event['body']['Player1']['attack'] = 'disrupt'
    mock_event['body']['Player2']['attack'] = 'block'
    mock_event['body']['Player1']['status_effects'] = [['disorient', 5],
                                                       ['poison', 12]]
    mock_event['body']['Player1']['enhanced'] = True

    # Act
    # Perform a round of combat
    combat_result_1 = do_combat(mock_event, mock_event)

    # Assert Actual == Expected
    assert combat_result_1['body']['Player1']['status_effects'] == [['disorient', 4],
                                                                    ['poison', 11]]
    assert combat_result_1['body']['Player2']['status_effects'] == [['prone', 1]]

    # Act - Do it again! Player1 re-applies prone
    # Perform a round of combat
    combat_result_2 = do_combat(combat_result_1, combat_result_1)

    # Assert Actual == Expected
    assert combat_result_2['body']['Player1']['status_effects'] == [['disorient', 3],
                                                                    ['poison', 10]]
    assert combat_result_2['body']['Player2']['status_effects'] == [['prone', 1]]

    # Act - Do it again! Player1 does not re-apply prone
    combat_result_2['body']['Player1']['enhanced'] = 'False'
    # Perform a round of combat
    combat_result_3 = do_combat(combat_result_2, combat_result_2)

    # Assert Actual == Expected
    assert combat_result_3['body']['Player1']['status_effects'] == [['disorient', 2],
                                                                    ['poison', 9]]
    assert combat_result_3['body']['Player2']['status_effects'] == []


@pytest.mark.parametrize("status_effect,expected_diff,left",
                         [
                             ("apply_prone", "area", False),
                             ("apply_prone", "block", True),
                             ("apply_disorient", "attack", False),
                             ("apply_disorient", "dodge", True),
                             ("apply_haste", "attack", False),
                             ("apply_haste", "attack", True)
                         ])
def test_rules_change(mock_event: dict, status_effect: str, expected_diff: str,
                      left: bool) -> None:
    """
    Test to check if the rules change properly

    :param mock_event: Mock AWS lambda event dict
    :param status_effect: The applied status effect which changes the rules
    :param expected_diff: Expected change from default rules
    """
    default_rules = {"area": {"beats": ["disrupt", "dodge"],
                              "loses": ["attack", "block"]},
                     "attack": {"beats": ["disrupt", "area"],
                                "loses": ["block", "dodge"]},
                     "block": {"beats": ["area", "attack"],
                               "loses": ["disrupt", "dodge"]},
                     "disrupt": {"beats": ["block", "dodge"],
                                 "loses": ["attack", "area"]},
                     "dodge": {"beats": ["attack", "block"],
                               "loses": ["area", "disrupt"]}}

    _, new_rules = getattr(combat_effects,
                           status_effect)(player=player1,
                                          rules=copy.deepcopy(default_rules),
                                          left=left)
    different_rules = None
    for key in default_rules:
        if new_rules[key] != default_rules[key]:
            different_rules = key

    assert different_rules == expected_diff
