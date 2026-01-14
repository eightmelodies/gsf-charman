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

    def test_character_no_heartbeat_excluded(self, character_no_heartbeat):
        """Character without heartbeat data should be excluded."""
        result = DailyLogin().select([character_no_heartbeat])

        assert result == []

    def test_mixed_characters_only_needs_login(
        self, character_needs_login, character_recent_login, character_no_heartbeat
    ):
        """Only characters needing login should be selected from mixed group."""
        characters = [character_recent_login, character_no_heartbeat, character_needs_login]
        result = DailyLogin().select(characters)

        assert result == [character_needs_login]

    def test_empty_result_when_no_eligible(self, character_recent_login, character_no_heartbeat):
        """Empty result when no characters meet criteria."""
        result = DailyLogin().select([character_recent_login, character_no_heartbeat])

        assert result == []

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

    def test_character_with_null_session_excluded(self, character_null_session):
        """Character with null session.last_update should be excluded."""
        result = DailyLogin().select([character_null_session])
        assert result == []
