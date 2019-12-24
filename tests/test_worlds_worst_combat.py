import copy
import json
import pytest
from pathlib import Path

from worlds_worst_serverless.worlds_worst_combat.handler import do_combat
from worlds_worst_serverless.worlds_worst_combat import combat_effects


@pytest.fixture
def player1():
    return {
        "name": "Truckthunders",
        "character_class": "dreamer",
        "max_hit_points": 500,
        "max_ex": 1000,
        "hit_points": 500,
        "ex": 0,
        "status_effects": [],
        "action": "attack",
        "enhanced": False,
    }


@pytest.fixture
def player2():
    return {
        "name": "Crunchbucket",
        "character_class": "cloistered",
        "max_hit_points": 500,
        "max_ex": 1000,
        "hit_points": 500,
        "ex": 0,
        "status_effects": [],
        "action": "area",
        "enhanced": False,
    }


@pytest.fixture
def abilities() -> dict:
    """
    Fixture to read abilities.json and provide the dict
    :return: The abilities dict
    """
    # Read in the abilities data
    path_to_file = (
        Path(__file__).resolve().parents[1]
        / "worlds_worst_serverless"
        / "worlds_worst_combat"
        / "abilities.json"
    )
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
    return {"body": {"Player1": player1, "Player2": player2}}


def test_combat_round_p1_wins(mock_event: dict, abilities: dict) -> None:
    """
    Test a full combat round where Player1 wins

    :param mock_event: Mock AWS lambda event dict
    :param abilities: The abilities dict, read in from abilities.json
    """
    # Arrange
    expected_player2_hp = (
        mock_event["body"]["Player2"]["hit_points"]
        - abilities[2]["effects"][0]["value"]
    )
    expected_message = [
        "Truckthunders uses attack!",
        "Crunchbucket uses area!",
        "Truckthunders wins.",
    ]

    # Act
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])
    combat_message = combat_body["message"]

    # Assert
    assert combat_body["Player2"]["hit_points"] == expected_player2_hp
    assert combat_message == expected_message


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
    player1_attacks = ["area", "attack", "block", "disrupt", "dodge"]
    player2_attacks = ["area", "attack", "block", "disrupt", "dodge"]
    expected_player1_hps = [
        [0, 0, 0, 100, 100],
        [100, 0, 0, 100, 0],
        [100, 100, 0, 0, 0],
        [0, 0, 100, 0, 100],
        [0, 100, 100, 0, 0],
    ]
    expected_player2_hps = [
        [0, 100, 100, 0, 0],
        [0, 0, 100, 0, 100],
        [0, 0, 0, 100, 100],
        [100, 100, 0, 0, 0],
        [100, 0, 0, 100, 0],
    ]

    # Act
    # Perform a round of combat
    for i, player1_attack in enumerate(player1_attacks):
        for j, player2_attack in enumerate(player2_attacks):
            mock_event["body"]["Player1"]["action"] = player1_attack
            mock_event["body"]["Player2"]["action"] = player2_attack

            combat_result = do_combat(mock_event, mock_event)
            combat_body = json.loads(combat_result["body"])

            # Assert - The 400 is a kluge because I don't want to remake the list
            assert (
                combat_body["Player1"]["hit_points"] == 400 + expected_player1_hps[i][j]
            )
            assert (
                combat_body["Player2"]["hit_points"] == 400 + expected_player2_hps[i][j]
            )


def test_check_dead(mock_event: dict) -> None:
    """
    Test that the check_dead() method works as expected

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["hit_points"] = 0
    expected_message = ["Truckthunders died to their status effects."]
    expected_body = {
        "Player1": mock_event["body"]["Player1"],
        "Player2": mock_event["body"]["Player2"],
        "message": expected_message,
    }

    # Act
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])
    combat_message = combat_body["message"]

    # Assert nothing has changed and the combat result equals the input dict
    assert combat_body == expected_body
    assert combat_message == expected_message


def test_multiple_status(mock_event: dict) -> None:
    """
    Test that status effects get correctly applied/updated when there are multiple

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["action"] = "disrupt"
    mock_event["body"]["Player2"]["action"] = "block"
    mock_event["body"]["Player1"]["status_effects"] = [["disorient", 5], ["poison", 12]]
    mock_event["body"]["Player1"]["enhanced"] = True

    # Act
    # Perform a round of combat
    combat_result_1 = do_combat(mock_event, mock_event)
    combat_body_1 = json.loads(combat_result_1["body"])

    # Assert Actual == Expected
    assert combat_body_1["Player1"]["status_effects"] == [
        ["disorient", 4],
        ["poison", 11],
        ["enhancement_sickness", 1],
    ]
    assert combat_body_1["Player2"]["status_effects"] == [["prone", 1]]

    # Act - Do it again! Player1 tries to re-apply prone but is enhancement sick
    # Perform a round of combat
    combat_result_2 = do_combat(combat_result_1, combat_result_1)
    combat_body_2 = json.loads(combat_result_2["body"])

    # Assert Actual == Expected
    assert combat_body_2["Player1"]["status_effects"] == [
        ["disorient", 3],
        ["poison", 10],
    ]
    assert combat_body_2["Player2"]["status_effects"] == []

    # Act - Do it again! Player1 does not re-apply prone
    combat_body_2["Player1"]["enhanced"] = "False"
    combat_result_2 = {"body": combat_body_2}

    # Perform a round of combat
    combat_result_3 = do_combat(combat_result_2, combat_result_2)
    combat_body_3 = json.loads(combat_result_3["body"])

    # Assert Actual == Expected
    assert combat_body_3["Player1"]["status_effects"] == [
        ["disorient", 2],
        ["poison", 9],
    ]
    assert combat_body_3["Player2"]["status_effects"] == []


def test_random_gun(mock_event: dict) -> None:
    """
    Test to make sure the random gun chooses randomly
    
    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["character_class"] = "creator"
    mock_event["body"]["Player1"]["action"] = "attack"
    mock_event["body"]["Player1"]["enhanced"] = True
    mock_event["body"]["Player2"]["action"] = "disrupt"
    possible_status = [
        "pistol",
        "rifle",
        "shotgun",
        "rocket_launcher",
        "enhancement_sickness",
    ]

    # Act
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])

    # Assert
    assert combat_body["Player1"]["status_effects"][0][0] in possible_status
    assert combat_body["Player1"]["status_effects"][0][1] == 1
    assert len(combat_body["Player1"]["status_effects"]) == 2


def test_enhance_bad(mock_event: dict) -> None:
    """
    Test to check behavior of enhancing an un-enhanceable ability

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["action"] = "attack"
    mock_event["body"]["Player1"]["enhanced"] = True
    mock_event["body"]["Player2"]["action"] = "attack"

    # Act
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])

    # Assert
    assert "Nothing happened!" in combat_body["message"][-1]
    assert len(combat_body["Player1"]["status_effects"]) == 0
    assert len(combat_body["Player2"]["status_effects"]) == 0


def test_enhance_status(mock_event: dict) -> None:
    """
    Test to make sure enhancement fatigue is applied after successfully
    enhancing an ability

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["action"] = "disrupt"
    mock_event["body"]["Player1"]["enhanced"] = True
    mock_event["body"]["Player2"]["action"] = "disrupt"

    # Act
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])

    # Assert
    assert len(combat_body["Player1"]["status_effects"]) == 1
    assert len(combat_body["Player2"]["status_effects"]) == 1
    assert combat_body["Player1"]["status_effects"] == [["enhancement_sickness", 1]]


def test_enhancement_sickness(mock_event: dict) -> None:
    """
    Test to make sure enhancement sickness works when
    you want to try to enhance 3x (it fails the 2nd time, succeeds the 3rd)

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["action"] = "disrupt"
    mock_event["body"]["Player1"]["enhanced"] = True
    mock_event["body"]["Player2"]["action"] = "disrupt"

    # Act
    first_combat_result = do_combat(mock_event, mock_event)
    first_combat_body = json.loads(first_combat_result["body"])
    second_combat_result = do_combat(mock_event, mock_event)
    second_combat_body = json.loads(second_combat_result["body"])
    third_combat_result = do_combat(mock_event, mock_event)
    third_combat_body = json.loads(third_combat_result["body"])

    # Assert
    assert 'Truckthunders enhanced disrupt!' in first_combat_body['message'][-1]
    assert 'failed due to enhancement sickness' in second_combat_body['message'][0]
    assert 'Truckthunders enhanced disrupt!' in third_combat_body['message'][-1]
    assert 'failed due to enhancement sickness' not in third_combat_body['message'][0]


@pytest.mark.parametrize(
    "character_class,ability_combo,expected_status",
    [
        ("dreamer", ["disrupt", "block"], [["prone", 1]]),
        ("dreamer", ["area", "disrupt"], [["disorient", 1]]),
        ("chosen", ["dodge", "attack"], [["enhancement_sickness", 1], ["haste", 1]]),
        ("chemist", ["attack", "disrupt"], [["poison", 2]]),
        (
            "cloistered",
            ["dodge", "attack"],
            [["enhancement_sickness", 1], ["counter_attack", 1]],
        ),
        (
            "cloistered",
            ["block", "area"],
            [["enhancement_sickness", 1], ["counter_disrupt", 1]],
        ),
        ("hacker", ["dodge", "attack"], [["anti_attack", 1], ["anti_area", 1]]),
        ("hacker", ["disrupt", "block"], [["enhancement_sickness", 1], ["lag", 1]]),
        (
            "architect",
            ["block", "attack"],
            [["enhancement_sickness", 1], ["absorb", 1]],
        ),
        ("architect", ["area", "dodge"], [["enhancement_sickness", 1], ["absorb", 1]]),
        (
            "photonic",
            ["block", "area"],
            [["enhancement_sickness", 1], ["buff_attack", 1]],
        ),
        ("photonic", ["attack", "disrupt"], [["connected", 1]]),
    ],
)
def test_enhancements(
    mock_event: dict,
    abilities: dict,
    character_class: str,
    ability_combo: list,
    expected_status: list,
) -> None:
    """
    Test that a enhancements are applied properly

    :param mock_event: Mock AWS lambda event dict
    """
    # Arrange
    mock_event["body"]["Player1"]["character_class"] = character_class
    mock_event["body"]["Player1"]["enhanced"] = True
    mock_event["body"]["Player1"]["action"] = ability_combo[0]
    mock_event["body"]["Player2"]["action"] = ability_combo[1]

    player1_action = [
        x
        for x in abilities
        if x["class"] == character_class and x["type"] == ability_combo[0]
    ]
    expected_target = player1_action[0]["enhancements"][0]["target"]

    expected_player1_hp = mock_event["body"]["Player1"]["hit_points"]
    expected_player2_hp = mock_event["body"]["Player2"]["hit_points"] - 100

    # Act
    # Perform a round of combat
    combat_result = do_combat(mock_event, mock_event)
    combat_body = json.loads(combat_result["body"])

    # Assert
    assert combat_body["Player1"]["hit_points"] == expected_player1_hp
    assert combat_body["Player2"]["hit_points"] == expected_player2_hp
    if expected_target == "target":
        assert combat_body["Player2"]["status_effects"] == expected_status
    else:
        assert combat_body["Player1"]["status_effects"] == expected_status


@pytest.mark.parametrize(
    "status_effect,expected_diff,left",
    [
        ("apply_prone", ["area"], False),
        ("apply_prone", ["block"], True),
        ("apply_disorient", ["attack"], False),
        ("apply_disorient", ["dodge"], True),
        ("apply_haste", ["attack"], False),
        ("apply_haste", ["attack"], True),
        ("apply_counter_attack", ["attack"], False),
        ("apply_counter_attack", ["area"], True),
        ("apply_counter_disrupt", ["disrupt"], False),
        ("apply_counter_disrupt", ["block"], True),
        ("apply_pistol", ["attack", "area", "block", "disrupt", "dodge"], False),
        ("apply_pistol", ["attack"], True),
        ("apply_shotgun", ["area", "block", "disrupt", "dodge"], False),
        ("apply_shotgun", ["attack"], True),
        ("apply_rocket_launcher", ["attack", "area", "disrupt", "dodge"], False),
        ("apply_rocket_launcher", ["attack"], True),
        ("apply_connected", ["attack", "area", "block", "dodge"], False),
        ("apply_connected", ["disrupt"], True),
        ("apply_lag", ["dodge"], False),
        ("apply_lag", ["attack"], True),
    ],
)
def test_rules_change(
    mock_event: dict, status_effect: str, expected_diff: str, left: bool
) -> None:
    """
    Test to check if the rules change properly

    :param mock_event: Mock AWS lambda event dict
    :param status_effect: The applied status effect which changes the rules
    :param expected_diff: Expected change from default rules
    """
    default_rules = {
        "area": {"beats": ["disrupt", "dodge"], "loses": ["attack", "block"]},
        "attack": {"beats": ["disrupt", "area"], "loses": ["block", "dodge"]},
        "block": {"beats": ["area", "attack"], "loses": ["disrupt", "dodge"]},
        "disrupt": {"beats": ["block", "dodge"], "loses": ["attack", "area"]},
        "dodge": {"beats": ["attack", "block"], "loses": ["area", "disrupt"]},
    }

    _, _, new_rules = getattr(combat_effects, status_effect)(
        self=player1, target=player2, rules=copy.deepcopy(default_rules), left=left
    )
    different_rules = list()
    for key in default_rules:
        if new_rules[key] != default_rules[key]:
            different_rules.append(key)

    assert set(different_rules) == set(expected_diff)
