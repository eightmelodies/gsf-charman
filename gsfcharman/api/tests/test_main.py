from datetime import datetime, timezone

from gsfcharman.api.data import CharacterData, LumnisData


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
