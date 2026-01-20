import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from gsfcharman.api.data import CharacterData, LumnisData, PendingLogoutRequest, SessionData
from gsfcharman.api.main import app, db


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
def sample_character_data(sample_lumnis_data):
    """Sample CharacterData for testing."""
    return CharacterData(name="testcharacter", lumnis=sample_lumnis_data)


@pytest.fixture
def sample_pending_logout_request():
    """Sample PendingLogoutRequest for testing."""
    return PendingLogoutRequest(logout_requested=True, when_requested=datetime.now(timezone.utc))


@pytest.fixture
def sample_session_data():
    """Sample SessionData for testing."""
    return SessionData(last_update=datetime.now(timezone.utc), last_logon=datetime.now(timezone.utc), is_logged_in=True)


@pytest.fixture
def sample_character_data_with_all_fields(sample_lumnis_data, sample_pending_logout_request, sample_session_data):
    """Sample CharacterData with all fields populated for testing."""
    return CharacterData(
        name="testcharacter",
        lumnis=sample_lumnis_data,
        pending_logout_request=sample_pending_logout_request,
        session=sample_session_data,
    )


@pytest.fixture
def database_with_sample_data(sample_character_data, temp_db_dir):
    """Database instance with sample data populated in the app's db."""
    # Create the directory if it doesn't exist
    Path(temp_db_dir).mkdir(parents=True, exist_ok=True)

    # Update the app's global db instance to use the temporary directory
    db.data = {"testcharacter": sample_character_data}
    db.lastSaved = {name: datetime.now(timezone.utc) for name in db.data.keys()}
    db.file_location = str(temp_db_dir)
    return db


@pytest.fixture
def mock_datetime_now():
    """Mock datetime.now for consistent testing."""
    fixed_time = datetime.now(timezone.utc)
    with patch("gsfcharman.api.data.datetime") as mock_datetime:
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
    char_name = "testchar"

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
    }

    # Write to file
    file_path = Path(temp_db_dir) / f"{char_name}.json"
    with open(file_path, "w") as f:
        json.dump(char_data, f, indent=2)

    return temp_db_dir, char_name
