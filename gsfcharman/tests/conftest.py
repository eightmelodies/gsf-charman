import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from gsfcharman.data import CharacterData, LumnisData, SafeToLogoutData
from gsfcharman.main import app, db


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create a temporary directory for database files."""
    return tmp_path


@pytest.fixture
def sample_lumnis_data():
    """Sample LumnisData for testing."""
    return LumnisData(
        lumnis_3x=10,
        lumnis_2x=20,
        weekly_resource=5,
        refresh=datetime.now(timezone.utc),
        last_update=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_logout_safety_data():
    """Sample SafeToLogoutData for testing."""
    return SafeToLogoutData(safe_to_logout=True, last_update=datetime.now(timezone.utc))


@pytest.fixture
def sample_character_data(sample_lumnis_data, sample_logout_safety_data):
    """Sample CharacterData for testing."""
    return CharacterData(name="TestCharacter", lumnis=sample_lumnis_data, logout_safety=sample_logout_safety_data)


@pytest.fixture
def database_with_sample_data(sample_character_data):
    """Database instance with sample data populated in the app's db."""
    db.data = {"TestCharacter": sample_character_data}
    db.lastSaved = {name: datetime.now(timezone.utc) for name in db.data.keys()}
    return db


@pytest.fixture
def mock_datetime_now():
    """Mock datetime.now for consistent testing."""
    fixed_time = datetime.now(timezone.utc)
    with patch("gsfcharman.data.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        mock_datetime.timezone = timezone
        yield mock_datetime


@pytest.fixture(autouse=True)
def reset_db_state():
    """Reset database state before each test."""
    # Clear any existing data
    db.data.clear()
    db.lastSaved.clear()
    yield
    # Clean up after test
    db.data.clear()
    db.lastSaved.clear()


@pytest.fixture
def sample_json_files(temp_db_dir, sample_character_data):
    """Create sample JSON files for testing database loading."""
    char_name = "TestChar"

    # Create sample character data
    char_data = {
        "name": char_name,
        "lumnis": {
            "lumnis_3x": 15,
            "lumnis_2x": 25,
            "weekly_resource": 8,
            "refresh": datetime.now(timezone.utc).isoformat(),
            "last_update": datetime.now(timezone.utc).isoformat(),
        },
        "logout_safety": {"safe_to_logout": False, "last_update": datetime.now(timezone.utc).isoformat()},
    }

    # Write to file
    file_path = Path(temp_db_dir) / f"{char_name}.json"
    with open(file_path, "w") as f:
        json.dump(char_data, f, indent=2)

    return temp_db_dir, char_name
