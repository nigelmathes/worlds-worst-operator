"""
Placeholder
"""
from worlds_worst_operator.operator import route_tasks_and_response


def test_route_tasks_and_response() -> None:
    """
    Test normal usage of route_tasks_and_response()
    """
    dynamodb_table = "worlds-worst-operator-"

    test_input = {
        "body": {
            "playerId": "truckthunders",
            "action": "get info",
            "enhanced": False
        }
    }

    # Act
    response = route_tasks_and_response(event=test_input, context=test_input)

    # Assert
    pass


if __name__ == "__main__":
    test_route_tasks_and_response()
