import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import mock_open, patch

from gsfcharman.data import CharacterData, Database, LumnisData, SafeToLogoutData


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


class TestSafeToLogoutData:
    def test_safe_to_logout_data_creation(self, sample_logout_safety_data):
        assert sample_logout_safety_data.safe_to_logout is True

    def test_safe_to_logout_data_from_json(self, sample_logout_safety_data):
        from_json = SafeToLogoutData(**json.loads(sample_logout_safety_data.model_dump_json(by_alias=True)))

        assert from_json.safe_to_logout == sample_logout_safety_data.safe_to_logout
        assert from_json.last_update == sample_logout_safety_data.last_update


class TestCharacterData:
    def test_character_data_creation(self, sample_character_data):
        assert sample_character_data.name == "TestCharacter"
        assert sample_character_data.lumnis.lumnis_3x == 10
        assert sample_character_data.logout_safety.safe_to_logout is True

    def test_character_from_json(self, sample_character_data):
        from_json = CharacterData(**json.loads(sample_character_data.model_dump_json(by_alias=True)))

        assert from_json.name == sample_character_data.name
        assert from_json.lumnis.lumnis_3x == sample_character_data.lumnis.lumnis_3x
        assert from_json.logout_safety.last_update == sample_character_data.logout_safety.last_update

    def test_character_with_partial_lumnis_data(self, sample_lumnis_data):
        """Test creating a character with only lumnis data (no logout_safety)."""
        char = CharacterData(name="PartialChar", lumnis=sample_lumnis_data)

        assert char.name == "PartialChar"
        assert char.lumnis is not None
        assert char.lumnis.lumnis_3x == 10
        assert char.lumnis.lumnis_2x == 20
        assert char.lumnis.weekly_resource == 5
        assert char.logout_safety is None

    def test_character_with_only_name(self):
        """Test creating a character with only name (all other fields None)."""
        char = CharacterData(name="NameOnly")

        assert char.name == "NameOnly"
        assert char.lumnis is None
        assert char.logout_safety is None


class TestDatabase:
    def test_database_initialization(self):
        db = Database()

        assert isinstance(db.data, dict)
        assert isinstance(db.lastSaved, dict)
        assert "chardata" in db.FILE_LOCATION
        assert db.PERIODIC_WRITE_INTERVAL_SECONDS == 10

    def test_database_initialization_with_data(self, sample_character_data):
        test_data = {"TestCharacter": sample_character_data}
        db = Database(data=test_data)

        assert "TestCharacter" in db.data
        assert db.data["TestCharacter"].name == "TestCharacter"

    def test_characters(self, sample_character_data):
        character1 = sample_character_data
        character2 = sample_character_data.model_copy()
        character2.name = "Character2"

        test_data = {"Character1": character1, "Character2": character2}
        db = Database(data=test_data)

        characters = db.characters()
        assert isinstance(characters, set)
        assert "Character1" in characters
        assert "Character2" in characters
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
        assert db.data[char_name].logout_safety.safe_to_logout is False

    def test_save_method(self, temp_db_dir, sample_character_data, mock_datetime_now):
        """Test Database.save() method."""
        current_time = datetime.now(timezone.utc)

        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.data = {"TestCharacter": sample_character_data}
        db.lastSaved = {"TestCharacter": current_time}

        # Set lastSaved to a time that should trigger save (15 seconds ago)
        old_time = current_time - timedelta(seconds=15)
        db.lastSaved["TestCharacter"] = old_time

        db.save()

        # Check if file was created
        saved_file = Path(temp_db_dir) / "TestCharacter.json"
        assert saved_file.exists()

        # Verify content
        with open(saved_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data["name"] == "TestCharacter"
        assert saved_data["lumnis"]["lumnis_3x"] == 10
        assert saved_data["logout_safety"]["safe_to_logout"] is True

    def test_save_skips_recent_entries(self, temp_db_dir, sample_character_data, mock_datetime_now):
        """Test Database.save() skips entries saved recently."""
        current_time = datetime.now(timezone.utc)

        db = Database()
        db.FILE_LOCATION = temp_db_dir
        db.data = {"TestCharacter": sample_character_data}

        # Set lastSaved to current time (should skip save)
        db.lastSaved = {"TestCharacter": current_time}

        # Mock file operations to check if save was called
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                db.save()

                # json.dump should not be called if save is skipped
                mock_json_dump.assert_not_called()
