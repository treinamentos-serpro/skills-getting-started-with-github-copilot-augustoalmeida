from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_activities_returns_activity_details(client):
    # Arrange
    expected_activity = "Chess Club"
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert expected_activity in activities
    assert set(activities[expected_activity]) == expected_fields
    assert activities[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant_and_returns_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_response.json()[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        (
            "Chess Club",
            "michael@mergington.edu",
            400,
            "Student already signed up for this activity",
        ),
        ("Missing Club", "new.student@mergington.edu", 404, "Activity not found"),
    ],
)
def test_signup_returns_error_for_invalid_request(
    client, activity_name, email, expected_status, expected_detail
):
    # Arrange
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_unregister_removes_participant_and_returns_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities_response.json()[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Missing Club", "student@mergington.edu", "Activity not found"),
        (
            "Chess Club",
            "not.signed.up@mergington.edu",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_returns_not_found_for_invalid_request(
    client, activity_name, email, expected_detail
):
    # Arrange
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
