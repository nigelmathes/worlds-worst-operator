import json

from dataclasses import dataclass, asdict
from typing import Callable

import pytest

from pytest_mock import MockFixture

from worlds_worst_operator.operator import (
    route_tasks_and_response,
    build_actions_map,
    route_action,
)
from worlds_worst_operator.action_sets.common_actions import (
    COMMON_ACTIONS_MAP,
    get_player_info,
    change_class_message,
    change_class,
)
from worlds_worst_operator.action_sets.combat_actions import COMBAT_ACTIONS_MAP
from worlds_worst_operator.action_sets.home_actions import HOME_ACTIONS_MAP
from worlds_worst_operator.action_sets.text_adventure_actions import (
    TEXT_ADVENTURE_ACTIONS_MAP,
)
from worlds_worst_operator.player_data import Player


@dataclass
class TestMocks:
    """
    Class to hold multiple mocks to be delivered as a fixture
    """

    dynamodb_mock: MockFixture
    lambda_mock: MockFixture
    verify_mock: MockFixture
    os_mock: MockFixture
    mock_player_data: Player


@pytest.fixture
def test_mocks(mocker: MockFixture) -> TestMocks:
    """
    Deliver multiple mocks as a fixture
    """
    dynamodb_mock = mocker.patch(
        "worlds_worst_operator.operator.boto3.resource", autospec=True
    )
    lambda_mock = mocker.patch("worlds_worst_operator.operator.boto3.client")

    mock_player_data = Player(
        name="testing",
        character_class="dreamer",
        max_hit_points=100,
        max_ex=100,
        hit_points=100,
        ex=0,
        status_effects=[],
        action="get player info",
        enhanced=False,
        auth_token="auth_token",
        context="home",
        target="",
        history=[],
    )

    verify_mock = mocker.patch(
        "worlds_worst_operator.operator.verify_player",
        return_value=(asdict(mock_player_data), True),
    )

    os_mock = mocker.patch("worlds_worst_operator.operator.os")

    return TestMocks(
        dynamodb_mock=dynamodb_mock,
        lambda_mock=lambda_mock,
        verify_mock=verify_mock,
        mock_player_data=mock_player_data,
        os_mock=os_mock,
    )


def test_route_tasks_and_response(test_mocks: TestMocks) -> None:
    """
    Test normal usage of route_tasks_and_response()
    """
    # Arrange
    test_input = {
        "body": {"playerId": "truckthunders", "action": "get info", "enhanced": False}
    }
    expected_player = test_mocks.mock_player_data
    expected_player.history = ["get info"]

    expected_body = json.dumps(
        {
            "Player": asdict(expected_player),
            "message": [
                "You are testing, a dreamer",
                "You have 100 HP and 0 EX",
                "Your status effects are []",
                "You are currently home. What would you like to do?",
            ],
        }
    )

    expected_result = {
        "statusCode": 200,
        "body": expected_body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }

    # Act
    test_result = route_tasks_and_response(event=test_input, context=test_input)

    # Assert
    assert test_result == expected_result


def test_build_actions_map_home() -> None:
    """
    Test that the build_actions_map() function returns appropriate
    sets of actions for "home" context
    """
    # Arrange
    test_context = "home"
    expected_result = COMMON_ACTIONS_MAP
    expected_result.update(HOME_ACTIONS_MAP)

    # Act
    test_result = build_actions_map(context=test_context)

    # Assert
    assert test_result == expected_result


def test_build_actions_map_combat() -> None:
    """
    Test that the build_actions_map() function returns appropriate
    sets of actions for "combat" context
    """
    # Arrange
    test_context = "combat"
    expected_result = COMMON_ACTIONS_MAP
    expected_result.update(COMBAT_ACTIONS_MAP)

    # Act
    test_result = build_actions_map(context=test_context)

    # Assert
    assert test_result == expected_result


def test_build_actions_map_text() -> None:
    """
    Test that the build_actions_map() function returns appropriate
    sets of actions for "text_adventure" context
    """
    # Arrange
    test_context = "text_adventure"
    expected_result = TEXT_ADVENTURE_ACTIONS_MAP

    # Act
    test_result = build_actions_map(context=test_context)

    # Assert
    assert test_result == expected_result


@pytest.mark.parametrize(
    "test_input,expected_result",
    [
        ("get info", ("get player info", get_player_info)),
        ("change class", ("change class", change_class_message)),
        ("select dreamer", ("dreamer", change_class)),
    ],
)
def test_route_action_common(test_input: str, expected_result: Callable) -> None:
    """
    Test that the route_action() method returns the correct action from
    COMMON_ACTIONS_MAP based upon different test inputs
    """
    # Arrange done in parametrize
    # Act
    test_result = route_action(action=test_input, actions_map=COMMON_ACTIONS_MAP)

    # Assert
    assert test_result == expected_result
