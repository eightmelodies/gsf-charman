"""Pytest fixtures for strategy testing."""

from datetime import datetime, timedelta, timezone

import pytest

from gsfcharman.api.data import CharacterData, LumnisData, SessionData

# Fixed date for consistent testing (Monday of a test week)
TEST_WEEK_START = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def lumnis_available() -> CharacterData:
    """Character with Lumnis available (7300/7300, refresh=None)."""
    return CharacterData(
        name="available",
        lumnis=LumnisData(
            lumnis_3x=7300,
            lumnis_2x=7300,
            weekly_resource=0,
            refresh=None,
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def lumnis_started_early() -> CharacterData:
    """Character that has started Lumnis with early refresh date (Tuesday) - 3x phase."""
    return CharacterData(
        name="started_early",
        lumnis=LumnisData(
            lumnis_3x=5000,
            lumnis_2x=7300,  # 3x being used first, 2x still at max
            weekly_resource=10000,
            refresh=TEST_WEEK_START + timedelta(days=1),  # Tuesday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def lumnis_started_middle() -> CharacterData:
    """Character that has started Lumnis with middle refresh date (Thursday) - 3x exhausted, 2x available."""
    return CharacterData(
        name="started_middle",
        lumnis=LumnisData(
            lumnis_3x=0,  # 3x exhausted
            lumnis_2x=7300,  # 2x now available
            weekly_resource=15000,
            refresh=TEST_WEEK_START + timedelta(days=3),  # Thursday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def lumnis_started_late() -> CharacterData:
    """Character that has started Lumnis with late refresh date (Saturday) - 2x phase."""
    return CharacterData(
        name="started_late",
        lumnis=LumnisData(
            lumnis_3x=0,  # 3x exhausted
            lumnis_2x=4000,  # 2x being used
            weekly_resource=20000,
            refresh=TEST_WEEK_START + timedelta(days=5),  # Saturday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def lumnis_completed() -> CharacterData:
    """Character that has completed Lumnis bonus (Monday - completed early)."""
    return CharacterData(
        name="completed",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=25000,
            refresh=TEST_WEEK_START,  # Monday - completed same day
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def resource_available_no_refresh() -> CharacterData:
    """Character that can earn weekly resource but hasn't started Lumnis."""
    return CharacterData(
        name="resource_no_refresh",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=0,
            refresh=None,
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def resource_available_has_refreshed() -> CharacterData:
    """Character that can earn weekly resource and has started Lumnis (Wednesday)."""
    return CharacterData(
        name="resource_has_refreshed",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=0,
            refresh=TEST_WEEK_START + timedelta(days=2),  # Wednesday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def resource_available_has_refreshed_later() -> CharacterData:
    """Character that can earn weekly resource and has started Lumnis (Thursday)."""
    return CharacterData(
        name="resource_with_refresh",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=0,
            refresh=TEST_WEEK_START + timedelta(days=3),  # Thursday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def resource_capped() -> CharacterData:
    """Character that has capped weekly resource (Friday)."""
    return CharacterData(
        name="resource_capped",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=50000,
            refresh=TEST_WEEK_START + timedelta(days=4),  # Friday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def resource_incapable() -> CharacterData:
    """Character that has a null resource value, ie., they are incapable of earning resource"""
    return CharacterData(
        name="resource_incapable",
        lumnis=LumnisData(
            lumnis_3x=0,
            lumnis_2x=0,
            weekly_resource=None,
            refresh=TEST_WEEK_START + timedelta(days=4),  # Friday
            last_update=TEST_WEEK_START,
        ),
    )


@pytest.fixture
def no_lumnis_data() -> CharacterData:
    """Character with no Lumnis data."""
    return CharacterData(name="no_data", lumnis=None)


# Daily Login Test Fixtures
@pytest.fixture
def character_needs_login() -> CharacterData:
    """Character that needs daily login (heartbeat before reset time)."""
    # Create a heartbeat time that's definitely before the daily reset
    from gsfcharman.daemon.strategies.daily_login import DailyLogin

    reset_time = DailyLogin()._get_when_login_reset()
    old_heartbeat = reset_time - timedelta(hours=12)
    return CharacterData(name="needs_login", session=SessionData(last_update=old_heartbeat))


@pytest.fixture
def character_recent_login() -> CharacterData:
    """Character that recently logged in (heartbeat after reset time)."""
    # Create a heartbeat time that's definitely after the daily reset
    from gsfcharman.daemon.strategies.daily_login import DailyLogin

    reset_time = DailyLogin()._get_when_login_reset()
    recent_heartbeat = reset_time + timedelta(hours=1)
    return CharacterData(name="recent_login", session=SessionData(last_update=recent_heartbeat))


@pytest.fixture
def character_no_heartbeat() -> CharacterData:
    """Character with no heartbeat data."""
    return CharacterData(name="no_heartbeat")


@pytest.fixture
def character_at_reset_time() -> CharacterData:
    """Character with heartbeat exactly at reset time."""
    # Calculate the reset time for the test week start date
    from gsfcharman.daemon.strategies.daily_login import DailyLogin

    strategy = DailyLogin()
    reset_time = strategy._get_when_login_reset()

    # Use a fixed time that would be at reset for testing
    # Since we can't easily control the current time, we'll use a mock approach
    return CharacterData(
        name="at_reset",
        session=SessionData(
            last_update=TEST_WEEK_START + timedelta(hours=5)
        ),  # 5 AM UTC = midnight EST + 27 min offset
    )


@pytest.fixture
def character_another_needs_login() -> CharacterData:
    """Another character that needs daily login (similar to character_needs_login but different name)."""
    from gsfcharman.daemon.strategies.daily_login import DailyLogin

    reset_time = DailyLogin()._get_when_login_reset()
    old_heartbeat = reset_time - timedelta(hours=24)  # Different time than character_needs_login
    return CharacterData(name="another_needs_login", session=SessionData(last_update=old_heartbeat))


@pytest.fixture
def character_null_session() -> CharacterData:
    """Character with null session.last_update."""
    return CharacterData(name="null_session", session=SessionData(last_update=None))
