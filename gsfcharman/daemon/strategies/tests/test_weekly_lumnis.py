"""Tests for WeeklyLumnis strategy."""

from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis


class TestWeeklyLumnisStrategy:
    """Test cases for WeeklyLumnis strategy."""

    def test_lumnis_available_ranked_highest(self, lumnis_available, lumnis_started_early):
        """Characters with available Lumnis should come before started characters."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_started_early, lumnis_available])

        # Characters with available Lumnis should be first
        assert result == [lumnis_available, lumnis_started_early]

    def test_started_characters_ranked_by_refresh(self, lumnis_started_early, lumnis_started_late):
        """Characters with earlier refresh dates should come first."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_started_late, lumnis_started_early])

        # Character with earlier refresh date should be first
        assert result == [lumnis_started_early, lumnis_started_late]

    def test_completed_characters_excluded(self, lumnis_completed, lumnis_available):
        """Completed characters should be excluded from results."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_completed, lumnis_available])

        # Only non-completed characters should be returned
        assert result == [lumnis_available]

    def test_empty_result_when_all_completed(self, lumnis_completed):
        """Should return empty list when all characters have completed."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_completed])

        # Should return empty list
        assert result == []

    def test_multiple_completed_characters_excluded(self, lumnis_completed, lumnis_started_early):
        """Multiple completed characters should all be excluded."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_completed, lumnis_started_early])

        # Only non-completed characters should be returned
        assert result == [lumnis_started_early]

    def test_no_lumnis_data_excluded(self, no_lumnis_data, lumnis_available):
        """Characters with no Lumnis data should be excluded."""
        strategy = WeeklyLumnis()
        result = strategy.select([no_lumnis_data, lumnis_available])

        # Only characters with Lumnis data should be returned
        assert result == [lumnis_available]

    def test_complex_mixed_scenario(
        self, lumnis_available, lumnis_started_early, lumnis_started_late, lumnis_completed, no_lumnis_data
    ):
        """Test complex scenario with mixed character states."""
        strategy = WeeklyLumnis()
        characters = [lumnis_completed, lumnis_started_late, lumnis_available, no_lumnis_data, lumnis_started_early]
        result = strategy.select(characters)

        # Expected order: available first, then started characters by refresh date
        expected = [lumnis_available, lumnis_started_early, lumnis_started_late]
        assert result == expected

    def test_only_available_characters(self, lumnis_available):
        """Test with only available characters."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_available])

        # Should return the available character
        assert result == [lumnis_available]

    def test_only_started_characters(self, lumnis_started_early, lumnis_started_late):
        """Test with only started characters."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_started_late, lumnis_started_early])

        # Should return started characters sorted by refresh date
        assert result == [lumnis_started_early, lumnis_started_late]
