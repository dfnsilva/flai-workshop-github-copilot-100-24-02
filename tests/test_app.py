"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to original state before each test."""
    original_state = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original_state.items():
        activities[name]["participants"] = participants


# --- GET /activities ---

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_get_activities_includes_expected_fields():
    response = client.get("/activities")
    data = response.json()
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess


# --- GET / (redirect) ---

def test_root_redirects_to_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# --- POST /activities/{activity_name}/signup ---

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    assert email in activities["Chess Club"]["participants"]


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent Club/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_registered():
    email = "michael@mergington.edu"  # already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


# --- DELETE /activities/{activity_name}/signup ---

def test_unregister_success():
    email = "michael@mergington.edu"  # already in Chess Club
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_unregister_removes_participant():
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/signup", params={"email": email})
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_activity_not_found():
    response = client.delete(
        "/activities/Nonexistent Club/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "notregistered@mergington.edu"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
