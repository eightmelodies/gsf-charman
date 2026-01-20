"""Tests for WeeklyLumnis strategy."""

from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis


class TestWeeklyLumnisStrategy:
    """Test cases for WeeklyLumnis strategy."""

    def test_no_refresh_characters_returned_first(self, lumnis_available, lumnis_started_early):
        """Characters without refresh dates are returned first, excluding started characters."""
        strategy = WeeklyLumnis()
        result = strategy.select([lumnis_started_early, lumnis_available])

        # Only characters without refresh dates are returned (lumnis_available has no refresh)
        assert result == [lumnis_available]

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

    def test_no_lumnis_data_included_if_no_refresh(self, no_lumnis_data, lumnis_available):
        """Characters with no Lumnis data are included if they have no refresh date."""
        strategy = WeeklyLumnis()
        result = strategy.select([no_lumnis_data, lumnis_available])

        # Both characters have no refresh dates, so both are included
        assert result == [no_lumnis_data, lumnis_available]

    def test_complex_mixed_scenario(
        self, lumnis_available, lumnis_started_early, lumnis_started_late, lumnis_completed, no_lumnis_data
    ):
        """Test complex scenario with mixed character states."""
        strategy = WeeklyLumnis()
        characters = [lumnis_completed, lumnis_started_late, lumnis_available, no_lumnis_data, lumnis_started_early]
        result = strategy.select(characters)

        # Expected: only characters without refresh dates are returned first
        expected = [lumnis_available, no_lumnis_data]
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

    def test_4x_5x_fields_included_in_total(self, lumnis_available):
        """Test that 4x and 5x fields are included in Lumnis total calculation."""
        strategy = WeeklyLumnis()

        # Create a character with 4x and 5x fields
        character_with_4x_5x = lumnis_available.model_copy()
        character_with_4x_5x.lumnis.lumnis_4x = 1000
        character_with_4x_5x.lumnis.lumnis_5x = 2000

        result = strategy.select([character_with_4x_5x])

        # Should include character with 4x/5x fields
        assert result == [character_with_4x_5x]

    def test_donations_field_ignored(self, lumnis_available):
        """Test that donations field doesn't affect Lumnis logic."""
        strategy = WeeklyLumnis()

        # Create a character with donations but no Lumnis
        character_with_donations = lumnis_available.model_copy()
        character_with_donations.lumnis.donations = 5000
        character_with_donations.lumnis.lumnis_2x = 0
        character_with_donations.lumnis.lumnis_3x = 0
        character_with_donations.lumnis.lumnis_4x = 0
        character_with_donations.lumnis.lumnis_5x = 0

        result = strategy.select([character_with_donations])

        # Character with no refresh date is included regardless of Lumnis status
        assert result == [character_with_donations]

    def test_mixed_2x_3x_4x_5x_values(self, lumnis_available):
        """Test characters with mixed 2x/3x/4x/5x values."""
        strategy = WeeklyLumnis()

        # Create a character with mixed values
        character_mixed = lumnis_available.model_copy()
        character_mixed.lumnis.lumnis_2x = 1000
        character_mixed.lumnis.lumnis_3x = 2000
        character_mixed.lumnis.lumnis_4x = 3000
        character_mixed.lumnis.lumnis_5x = 4000

        result = strategy.select([character_mixed])

        # Should include character with mixed values (has remaining Lumnis)
        assert result == [character_mixed]

    def test_zero_values_included_if_no_refresh(self, lumnis_available):
        """Test that characters with all zero Lumnis values are included if they have no refresh date."""
        strategy = WeeklyLumnis()

        # Create a character with all zero values
        character_zero = lumnis_available.model_copy()
        character_zero.lumnis.lumnis_2x = 0
        character_zero.lumnis.lumnis_3x = 0
        character_zero.lumnis.lumnis_4x = 0
        character_zero.lumnis.lumnis_5x = 0

        result = strategy.select([character_zero])

        # Character with no refresh date is included regardless of Lumnis status
        assert result == [character_zero]
