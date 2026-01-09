from datetime import datetime, timezone

from gsfcharman.data import CharacterData, LumnisData, SafeToLogoutData


class TestGetCharacterEndpoint:
    def test_get_existing_character(self, client, database_with_sample_data):
        response = client.get("/characters/TestCharacter")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "TestCharacter"
        assert response_data["lumnis"]["lumnis_3x"] == 10
        assert response_data["lumnis"]["lumnis_2x"] == 20
        assert response_data["lumnis"]["weekly_resource"] == 5
        assert response_data["logout_safety"]["safe_to_logout"] is True

    def test_get_nonexistent_character(self, client):
        response = client.get("/characters/NonExistentCharacter")

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]


class TestGetCharacterLumnisEndpoint:
    def test_get_existing_character_lumnis(self, client, database_with_sample_data):
        response = client.get("/characters/TestCharacter/lumnis")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["lumnis_3x"] == 10
        assert response_data["lumnis_2x"] == 20
        assert response_data["weekly_resource"] == 5
        assert "refresh" in response_data
        assert "last_update" in response_data

    def test_get_lumnis_nonexistent_character(self, client):
        response = client.get("/characters/NonExistentCharacter/lumnis")

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]


class TestGetCharacterLogoutSafetyEndpoint:
    def test_get_existing_character_logout_safety(self, client, database_with_sample_data):
        response = client.get("/characters/TestCharacter/safe-to-logout")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["safe_to_logout"] is True
        assert "last_update" in response_data

    def test_get_logout_safety_nonexistent_character(self, client):
        response = client.get("/characters/NonExistentCharacter/safe-to-logout")

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]


class TestPutCharacterEndpoint:
    def test_update_existing_character(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_data = {
            "name": "TestCharacter",
            "lumnis": {
                "lumnis_3x": 20,
                "lumnis_2x": 30,
                "weekly_resource": 10,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
            "logout_safety": {"safe_to_logout": False, "last_update": current_time.isoformat()},
        }

        response = client.put("/characters/TestCharacter", json=updated_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "TestCharacter"
        assert response_data["lumnis"]["lumnis_3x"] == 20
        assert response_data["lumnis"]["lumnis_2x"] == 30
        assert response_data["lumnis"]["weekly_resource"] == 10
        assert response_data["logout_safety"]["safe_to_logout"] is False

    def test_update_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_data = {
            "name": "NonExistentCharacter",
            "lumnis": {
                "lumnis_3x": 20,
                "lumnis_2x": 30,
                "weekly_resource": 10,
                "refresh": current_time.isoformat(),
                "last_update": current_time.isoformat(),
            },
            "logout_safety": {"safe_to_logout": False, "last_update": current_time.isoformat()},
        }

        response = client.put("/characters/NonExistentCharacter", json=updated_data)

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]

    def test_update_character_partial_data(self, client, database_with_sample_data):
        """Test that partial data updates are now valid (all fields optional)."""
        partial_data = {"name": "TestCharacter"}

        response = client.put("/characters/TestCharacter", json=partial_data)

        # PUT replaces the entire object, so partial data results in None fields
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "TestCharacter"
        assert response_data["lumnis"] is None
        assert response_data["logout_safety"] is None


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

        response = client.put("/characters/TestCharacter/lumnis", json=updated_lumnis)

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

        response = client.put("/characters/NonExistentCharacter/lumnis", json=updated_lumnis)

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]


class TestPutCharacterLogoutSafetyEndpoint:
    def test_update_existing_character_logout_safety(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        updated_logout_safety = {"safe_to_logout": False, "last_update": current_time.isoformat()}

        response = client.put("/characters/TestCharacter/safe-to-logout", json=updated_logout_safety)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["safe_to_logout"] is False

    def test_update_logout_safety_nonexistent_character(self, client):
        current_time = datetime.now(timezone.utc)
        updated_logout_safety = {"safe_to_logout": False, "last_update": current_time.isoformat()}

        response = client.put("/characters/NonExistentCharacter/safe-to-logout", json=updated_logout_safety)

        assert response.status_code == 404
        assert "Character NonExistentCharacter not found" in response.json()["detail"]


class TestErrorHandling:
    def test_character_name_with_special_characters(self, client, database_with_sample_data):
        current_time = datetime.now(timezone.utc)
        lumnis = LumnisData(
            lumnis_3x=10, lumnis_2x=20, weekly_resource=5, refresh=current_time, last_update=current_time
        )
        logout_safety = SafeToLogoutData(safe_to_logout=True, last_update=current_time)
        character = CharacterData(name="Test_Character-123", lumnis=lumnis, logout_safety=logout_safety)
        database_with_sample_data.data["Test_Character-123"] = character

        response = client.get("/characters/Test_Character-123")

        assert response.status_code == 200
        assert response.json()["name"] == "Test_Character-123"

    def test_empty_database_responses(self, client):
        response = client.get("/characters/AnyCharacter")
        assert response.status_code == 404

        response = client.get("/characters/AnyCharacter/lumnis")
        assert response.status_code == 404

        response = client.get("/characters/AnyCharacter/safe-to-logout")
        assert response.status_code == 404
