import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import mock_open, patch

from gsfcharman.api.data import CharacterData, Database, LumnisData


class TestLumnisData:
    def test_lumnis_data_creation(self, sample_lumnis_data):
        assert sample_lumnis_data.lumnis_3x == 10
        assert sample_lumnis_data.lumnis_2x == 20
        assert sample_lumnis_data.weekly_resource == 5

    def test_lumnis_from_json(self, sample_lumnis_data):
        from_json = LumnisData(**json.loads(sample_lumnis_data.model_dump_json(by_alias=True)))

        assert from_json.lumnis_3x == sample_lumnis_data.lumnis_3x == 10
        assert from_json.lumnis_2x == sample_lumnis_data.lumnis_2x == 20
        assert from_json.weekly_resource == sample_lumnis_data.weekly_resource == 5


class TestCharacterData:
    def test_character_data_creation(self, sample_character_data):
        assert sample_character_data.name == "testcharacter"
        assert sample_character_data.lumnis.lumnis_3x == 10

    def test_character_from_json(self, sample_character_data):
        from_json = CharacterData(**json.loads(sample_character_data.model_dump_json(by_alias=True)))

        assert from_json.name == sample_character_data.name
        assert from_json.lumnis.lumnis_3x == sample_character_data.lumnis.lumnis_3x

    def test_character_with_partial_lumnis_data(self, sample_lumnis_data):
        """Test creating a character with only lumnis data (no logout_safety)."""
        char = CharacterData(name="partialchar", lumnis=sample_lumnis_data)

        assert char.name == "partialchar"
        assert char.lumnis is not None
        assert char.lumnis.lumnis_3x == 10
        assert char.lumnis.lumnis_2x == 20
        assert char.lumnis.weekly_resource == 5

    def test_character_with_only_name(self):
        """Test creating a character with only name (all other fields None)."""
        char = CharacterData(name="nameonly")

        assert char.name == "nameonly"
        assert char.lumnis is None


class TestDatabase:
    def test_database_initialization(self):
        db = Database()

        assert isinstance(db.data, dict)
        assert isinstance(db.lastSaved, dict)
        assert "chardata" in db.FILE_LOCATION
        assert db.PERIODIC_WRITE_INTERVAL_SECONDS == 10

    def test_database_initialization_with_data(self, sample_character_data):
        test_data = {"testcharacter": sample_character_data}
        db = Database(data=test_data)

        assert "testcharacter" in db.data
        assert db.data["testcharacter"].name == "testcharacter"

    def test_characters(self, sample_character_data):
        character1 = sample_character_data
        character2 = sample_character_data.model_copy()
        character2.name = "character2"

        test_data = {"character1": character1, "character2": character2}
        db = Database(data=test_data)

        characters = db.characters()
        assert isinstance(characters, set)
        assert "character1" in characters
        assert "character2" in characters
        assert len(characters) == 2

    def test_load_with_empty_directory(self, temp_db_dir):
        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.load()

        assert len(db.data) == 0

    def test_load_with_json_files(self, sample_json_files):
        temp_db_dir, char_name = sample_json_files

        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.load()

        assert char_name in db.data
        assert db.data[char_name].name == char_name
        assert db.data[char_name].lumnis.lumnis_3x == 15
        assert db.data[char_name].lumnis.lumnis_2x == 25
        assert db.data[char_name].lumnis.weekly_resource == 8

    def test_save_method(self, temp_db_dir, sample_character_data, mock_datetime_now):
        """Test Database.save() method."""
        current_time = datetime.now(timezone.utc)

        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.data = {"testcharacter": sample_character_data}
        db.lastSaved = {"testcharacter": current_time}

        # Set lastSaved to a time that should trigger save (15 seconds ago)
        old_time = current_time - timedelta(seconds=15)
        db.lastSaved["testcharacter"] = old_time

        db.save()

        # Check if file was created
        saved_file = Path(temp_db_dir) / "testcharacter.json"
        assert saved_file.exists()

        # Verify content
        with open(saved_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data["name"] == "testcharacter"
        assert saved_data["lumnis"]["lumnis_3x"] == 10

    def test_save_skips_recent_entries(self, temp_db_dir, sample_character_data, mock_datetime_now):
        """Test Database.save() skips entries saved recently."""
        current_time = datetime.now(timezone.utc)

        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.data = {"testcharacter": sample_character_data}

        # Set lastSaved to current time (should skip save)
        db.lastSaved = {"testcharacter": current_time}

        # Mock file operations to check if save was called
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                db.save()

                # json.dump should not be called if save is skipped
                mock_json_dump.assert_not_called()
