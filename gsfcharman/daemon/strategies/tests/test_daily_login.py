"""Tests for DailyLogin strategy."""

from gsfcharman.daemon.strategies.daily_login import DailyLogin


class TestDailyLoginStrategy:
    """Test cases for DailyLogin strategy."""

    def test_character_needs_login_selected(self, character_needs_login):
        """Character with old heartbeat should be selected for login."""
        result = DailyLogin().select([character_needs_login])

        assert result == [character_needs_login]

    def test_character_recent_login_excluded(self, character_recent_login):
        """Character with recent heartbeat should be excluded from login."""
        result = DailyLogin().select([character_recent_login])

        assert result == []

    def test_character_no_session_included(self, character_no_heartbeat):
        """Character without session data should be included (treated as needing login)."""
        result = DailyLogin().select([character_no_heartbeat])

        assert result == [character_no_heartbeat]

    def test_mixed_characters_includes_no_session_and_needs_login(
        self, character_needs_login, character_recent_login, character_no_heartbeat
    ):
        """Characters with no session data or old activity should be selected."""
        characters = [character_recent_login, character_no_heartbeat, character_needs_login]
        result = DailyLogin().select(characters)

        # Should include characters with no session and characters with old activity
        assert len(result) == 2
        assert character_no_heartbeat in result
        assert character_needs_login in result
        assert character_recent_login not in result

    def test_includes_no_session_character(self, character_recent_login, character_no_heartbeat):
        """Character with no session should be included, recent login should not."""
        result = DailyLogin().select([character_recent_login, character_no_heartbeat])

        # Should include character with no session, exclude recent login
        assert len(result) == 1
        assert result == [character_no_heartbeat]
        assert character_recent_login not in result

    def test_multiple_characters_needing_login(self, character_needs_login, character_another_needs_login):
        """Multiple characters needing login should all be selected."""
        result = DailyLogin().select([character_needs_login, character_another_needs_login])

        # Order doesn't matter for DailyLogin since all share same deadline
        assert len(result) == 2
        assert character_needs_login in result
        assert character_another_needs_login in result

    def test_login_reset_time_calculation(self):
        """Test that login reset time is calculated correctly."""
        strategy = DailyLogin()
        reset_time = strategy._get_when_login_reset()

        # The reset time should be today's midnight EST + 27 minutes, converted to UTC
        # This should be a reasonable time (between 4-8 AM UTC depending on daylight saving)
        assert 4 <= reset_time.hour <= 8  # EST is UTC-5, EDT is UTC-4
        assert reset_time.minute == 27  # The offset should always be 27 minutes
        assert reset_time.tzinfo is not None  # Should have timezone info

    def test_character_with_null_session_included(self, character_null_session):
        """Character with null session data should be included (treated as needing login)."""
        result = DailyLogin().select([character_null_session])
        # Characters with null session data should be included
        assert len(result) == 1
        assert result == [character_null_session]
