from datetime import datetime, timezone

from gsfcharman.api.data import CharacterData, LumnisData, PendingLogoutRequest, SessionData


class TestGetCharacterEndpoint:
    def test_get_existing_character(self, client, database_with_sample_data):
        response = client.get("/characters/testcharacter")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "testcharacter"
        assert response_data["lumnis"]["lumnis_3x"] == 10
        assert response_data["lumnis"]["lumnis_2x"] == 20
        assert response_data["lumnis"]["weekly_resource"] == 5

    def test_get_nonexistent_character(self, client):
        response = client.get("/characters/nonexistentcharacter")

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]


class TestGetCharacterLumnisEndpoint:
    def test_get_existing_character_lumnis(self, client, database_with_sample_data):
        response = client.get("/characters/testcharacter/lumnis")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["lumnis_3x"] == 10
        assert response_data["lumnis_2x"] == 20
        assert response_data["weekly_resource"] == 5
        assert "refresh" in response_data
        assert "last_update" in response_data

    def test_get_lumnis_nonexistent_character(self, client):
        response = client.get("/characters/nonexistentcharacter/lumnis")

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]


class TestPutCharacterEndpoint:
    def test_update_existing_character(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_data = {
            "name": "testcharacter",
            "lumnis": {
                "lumnis_3x": 20,
                "lumnis_2x": 30,
                "weekly_resource": 10,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
        }

        response = client.put("/characters/testcharacter", json=updated_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "testcharacter"
        assert response_data["lumnis"]["lumnis_3x"] == 20
        assert response_data["lumnis"]["lumnis_2x"] == 30
        assert response_data["lumnis"]["weekly_resource"] == 10

    def test_update_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_data = {
            "name": "nonexistentcharacter",
            "lumnis": {
                "lumnis_3x": 20,
                "lumnis_2x": 30,
                "weekly_resource": 10,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
        }

        response = client.put("/characters/nonexistentcharacter", json=updated_data)

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]

    def test_update_character_partial_data(self, client, database_with_sample_data):
        """Test that partial data updates are now valid (all fields optional)."""
        partial_data = {"name": "testcharacter"}

        response = client.put("/characters/testcharacter", json=partial_data)

        # PUT replaces the entire object, so partial data results in None fields
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "testcharacter"
        assert response_data["lumnis"] is None


class TestPutCharacterLumnisEndpoint:
    def test_update_existing_character_lumnis(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_lumnis = {
            "lumnis_3x": 25,
            "lumnis_2x": 35,
            "weekly_resource": 12,
            "refresh": current_time.isoformat(),
            "last_update": current_time.isoformat(),
        }

        response = client.put("/characters/testcharacter/lumnis", json=updated_lumnis)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["lumnis_3x"] == 25
        assert response_data["lumnis_2x"] == 35
        assert response_data["weekly_resource"] == 12

    def test_update_lumnis_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_lumnis = {
            "lumnis_3x": 25,
            "lumnis_2x": 35,
            "weekly_resource": 12,
            "refresh": current_time.isoformat(),
            "last_update": current_time.isoformat(),
        }

        response = client.put("/characters/nonexistentcharacter/lumnis", json=updated_lumnis)

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]


class TestGetCharacterPendingLogoutRequestEndpoint:
    def test_get_existing_character_pending_logout_request(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        pending_logout = PendingLogoutRequest(logout_requested=True, when_requested=current_time)
        database_with_sample_data.data["testcharacter"].pending_logout_request = pending_logout

        response = client.get("/characters/testcharacter/pending-logout-request")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["logout_requested"] is True
        assert "when_requested" in response_data

    def test_get_pending_logout_request_nonexistent_character(self, client):
        response = client.get("/characters/nonexistentcharacter/pending-logout-request")

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]

    def test_get_pending_logout_request_no_pending_request(self, client, database_with_sample_data):
        response = client.get("/characters/testcharacter/pending-logout-request")

        assert response.status_code == 200
        assert response.json() is None


class TestPutCharacterPendingLogoutRequestEndpoint:
    def test_update_existing_character_pending_logout_request(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_pending_logout = {
            "logout_requested": False,
            "when_requested": current_time.isoformat(),
        }

        response = client.put("/characters/testcharacter/pending-logout-request", json=updated_pending_logout)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["logout_requested"] is False
        assert "when_requested" in response_data

    def test_update_pending_logout_request_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_pending_logout = {
            "logout_requested": False,
            "when_requested": current_time.isoformat(),
        }

        response = client.put("/characters/nonexistentcharacter/pending-logout-request", json=updated_pending_logout)

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]


class TestGetCharacterSessionEndpoint:
    def test_get_existing_character_session(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        session = SessionData(last_update=current_time, last_logon=current_time, is_logged_in=True)
        database_with_sample_data.data["testcharacter"].session = session

        response = client.get("/characters/testcharacter/session")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_logged_in"] is True
        assert "last_update" in response_data
        assert "last_logon" in response_data

    def test_get_session_nonexistent_character(self, client):
        response = client.get("/characters/nonexistentcharacter/session")

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]

    def test_get_session_no_session_data(self, client, database_with_sample_data):
        response = client.get("/characters/testcharacter/session")

        assert response.status_code == 200
        assert response.json() is None


class TestPutCharacterSessionEndpoint:
    def test_update_existing_character_session(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_session = {
            "last_update": current_time.isoformat(),
            "last_logon": current_time.isoformat(),
            "is_logged_in": False,
        }

        response = client.put("/characters/testcharacter/session", json=updated_session)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_logged_in"] is False
        assert "last_update" in response_data
        assert "last_logon" in response_data

    def test_update_session_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_session = {
            "last_update": current_time.isoformat(),
            "last_logon": current_time.isoformat(),
            "is_logged_in": False,
        }

        response = client.put("/characters/nonexistentcharacter/session", json=updated_session)

        assert response.status_code == 404
        assert "Character nonexistentcharacter not found" in response.json()["detail"]


class TestPostCharacterEndpoint:
    def test_create_new_character(self, client):
        current_time = datetime.now(timezone.utc)
        character_data = {
            "name": "newcharacter",
            "lumnis": {
                "lumnis_3x": 15,
                "lumnis_2x": 25,
                "weekly_resource": 8,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
            "pending_logout_request": {
                "logout_requested": True,
                "when_requested": current_time.isoformat(),
            },
            "session": {
                "last_update": current_time.isoformat(),
                "last_logon": current_time.isoformat(),
                "is_logged_in": True,
            },
        }

        response = client.post("/characters/newcharacter", json=character_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "newcharacter"
        assert response_data["lumnis"]["lumnis_3x"] == 15
        assert response_data["lumnis"]["lumnis_2x"] == 25
        assert response_data["lumnis"]["weekly_resource"] == 8
        assert response_data["pending_logout_request"]["logout_requested"] is True
        assert response_data["session"]["is_logged_in"] is True

    def test_create_new_character_with_new_lumnis_fields(self, client):
        """Test creating a character with the new LumnisData fields."""
        current_time = datetime.now(timezone.utc)
        character_data = {
            "name": "newcharacter2",
            "lumnis": {
                "lumnis_5x": 5,
                "lumnis_4x": 8,
                "lumnis_3x": 10,
                "lumnis_2x": 20,
                "donations": 100,
                "weekly_resource": 5,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
        }

        response = client.post("/characters/newcharacter2", json=character_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "newcharacter2"
        assert response_data["lumnis"]["lumnis_5x"] == 5
        assert response_data["lumnis"]["lumnis_4x"] == 8
        assert response_data["lumnis"]["lumnis_3x"] == 10
        assert response_data["lumnis"]["lumnis_2x"] == 20
        assert response_data["lumnis"]["donations"] == 100
        assert response_data["lumnis"]["weekly_resource"] == 5

    def test_create_character_conflict_existing(self, client, database_with_sample_data):
        """Test creating a character that already exists."""
        current_time = datetime.now(timezone.utc)
        character_data = {
            "name": "testcharacter",
            "lumnis": {
                "lumnis_3x": 15,
                "lumnis_2x": 25,
                "weekly_resource": 8,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
        }

        response = client.post("/characters/testcharacter", json=character_data)

        assert response.status_code == 409
        assert "Character testcharacter already exists" in response.json()["detail"]

    def test_create_character_partial_data(self, client):
        """Test creating a character with only name."""
        character_data = {"name": "partialcharacter"}

        response = client.post("/characters/partialcharacter", json=character_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "partialcharacter"
        assert response_data["lumnis"] is None
        assert response_data["pending_logout_request"] is None
        assert response_data["session"] is None


class TestErrorHandling:
    def test_character_name_with_special_characters(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        lumnis = LumnisData(
            lumnis_3x=10, lumnis_2x=20, weekly_resource=5, refresh=current_time, last_update=current_time
        )
        character = CharacterData(name="test_character-123", lumnis=lumnis)
        database_with_sample_data.data["test_character-123"] = character

        response = client.get("/characters/test_character-123")

        assert response.status_code == 200
        assert response.json()["name"] == "test_character-123"

    def test_empty_database_responses(self, client):
        response = client.get("/characters/anycharacter")
        assert response.status_code == 404

        response = client.get("/characters/anycharacter/lumnis")
        assert response.status_code == 404

    def test_invalid_json_data(self, client):
        """Test handling of invalid JSON data in PUT/POST requests."""
        invalid_data = "invalid json"

        response = client.put(
            "/characters/testcharacter", data=invalid_data, headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_character_name_case_insensitive(self, client, database_with_sample_data):
        """Test that character names are handled case-insensitively."""
        response = client.get("/characters/TESTCHARACTER")

        assert response.status_code == 200
        assert response.json()["name"] == "testcharacter"

        # Test with mixed case
        response = client.get("/characters/TestCharacter")

        assert response.status_code == 200
        assert response.json()["name"] == "testcharacter"
