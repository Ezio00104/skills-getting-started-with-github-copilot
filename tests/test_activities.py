"""Integration tests for the FastAPI activity management API.

All tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and fixtures
- Act: Execute the API call
- Assert: Verify the response and side effects
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities(client: TestClient):
    """Test that GET /activities returns all 9 activities."""
    # Arrange
    expected_activities = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Art Studio",
        "Drama Club",
        "Debate Team",
        "Science Club"
    ]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 9
    for activity_name in expected_activities:
        assert activity_name in response.json()


def test_get_activities_returns_200_status(client: TestClient):
    """Test that GET /activities returns HTTP 200 OK."""
    # Arrange & Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200


def test_get_activities_response_has_correct_structure(client: TestClient):
    """Test that each activity has required fields: description, schedule, max_participants, participants."""
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    activities = response.json()

    # Assert
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data, dict)
        assert required_fields.issubset(activity_data.keys())
        assert isinstance(activity_data["participants"], list)
        assert isinstance(activity_data["max_participants"], int)


def test_get_activities_participants_is_list(client: TestClient):
    """Test that participants field in each activity is a list."""
    # Arrange & Act
    response = client.get("/activities")
    activities = response.json()

    # Assert
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["participants"], list)


# ============================================================================
# POST /signup Tests
# ============================================================================

def test_signup_successful_with_valid_activity_and_email(client: TestClient):
    """Test successful signup for an activity with valid inputs."""
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify participant was added
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_fails_with_nonexistent_activity(client: TestClient):
    """Test that signup returns 404 when activity doesn't exist."""
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_fails_with_duplicate_email(client: TestClient):
    """Test that signup returns 409 when student is already signed up."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up for Chess Club

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Student already signed up"


def test_signup_fails_when_activity_is_full(client: TestClient):
    """Test that signup returns 400 when activity has reached max participants."""
    # Arrange
    activity_name = "Tennis Club"
    # Tennis Club has max_participants=10 and already has 1 participant
    # We need to fill it up (add 9 more participants)
    emails = [f"filler{i}@mergington.edu" for i in range(9)]

    # Fill up the activity
    for email in emails:
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Try to add one more (should fail)
    new_email = "overflow@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_increases_participant_count(client: TestClient):
    """Test that participant count increases after successful signup."""
    # Arrange
    activity_name = "Drama Club"
    email = "newstudent@mergington.edu"
    
    # Get initial participant count
    activities_before = client.get("/activities").json()
    initial_count = len(activities_before[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    
    # Verify count increased
    activities_after = client.get("/activities").json()
    final_count = len(activities_after[activity_name]["participants"])
    assert final_count == initial_count + 1
    assert email in activities_after[activity_name]["participants"]


# ============================================================================
# DELETE /remove Participant Tests
# ============================================================================

def test_remove_participant_successful(client: TestClient):
    """Test successful removal of a participant from an activity."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already a participant

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    assert email not in activities_response.json()[activity_name]["participants"]


def test_remove_participant_fails_with_nonexistent_activity(client: TestClient):
    """Test that removal returns 404 when activity doesn't exist."""
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_fails_when_not_found(client: TestClient):
    """Test that removal returns 404 when participant is not in activity."""
    # Arrange
    activity_name = "Art Studio"
    email = "notinactivity@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_participant_decreases_count(client: TestClient):
    """Test that participant count decreases after successful removal."""
    # Arrange
    activity_name = "Debate Team"
    email = "james@mergington.edu"
    
    # Get initial participant count
    activities_before = client.get("/activities").json()
    initial_count = len(activities_before[activity_name]["participants"])

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    
    # Verify count decreased
    activities_after = client.get("/activities").json()
    final_count = len(activities_after[activity_name]["participants"])
    assert final_count == initial_count - 1
    assert email not in activities_after[activity_name]["participants"]


def test_remove_participant_fails_on_double_remove(client: TestClient):
    """Test that removing the same participant twice returns 404 on second attempt."""
    # Arrange
    activity_name = "Science Club"
    email = "aiden@mergington.edu"

    # Act - First removal (should succeed)
    response_first = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert first removal
    assert response_first.status_code == 200

    # Act - Second removal (should fail)
    response_second = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert second removal fails
    assert response_second.status_code == 404
    assert response_second.json()["detail"] == "Participant not found"


# ============================================================================
# GET / Root Tests
# ============================================================================

def test_root_redirects_to_static_index(client: TestClient):
    """Test that GET / redirects to /static/index.html."""
    # Arrange & Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"
