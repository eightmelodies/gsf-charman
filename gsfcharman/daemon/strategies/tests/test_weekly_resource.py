"""Tests for WeeklyResource strategy."""

from gsfcharman.daemon.strategies.weekly_resource import WeeklyResource


class TestWeeklyResourceStrategy:
    """Test cases for WeeklyResource strategy."""

    def test_resource_available_no_refresh_ranked_highest(
        self, resource_available_no_refresh, resource_available_has_refreshed
    ):
        result = WeeklyResource().select([resource_available_has_refreshed, resource_available_no_refresh])

        assert result == [resource_available_no_refresh, resource_available_has_refreshed]

    def test_resource_capped_excluded(self, resource_capped, resource_available_no_refresh):
        result = WeeklyResource().select([resource_capped, resource_available_no_refresh])

        assert result == [resource_available_no_refresh]

    def test_empty_result_when_no_eligible(self, resource_capped, no_lumnis_data):
        result = WeeklyResource().select([resource_capped, no_lumnis_data])

        assert result == []

    def test_resource_with_refresh_ranked_by_date(
        self,
        resource_available_has_refreshed,
        resource_available_has_refreshed_later,
    ):
        result = WeeklyResource().select([resource_available_has_refreshed_later, resource_available_has_refreshed])

        assert result == [resource_available_has_refreshed, resource_available_has_refreshed_later]

    def test_no_lumnis_data_excluded(self, no_lumnis_data, resource_available_no_refresh):
        result = WeeklyResource().select([no_lumnis_data, resource_available_no_refresh])

        assert result == [resource_available_no_refresh]

    def test_non_zero_resource_excluded(self, resource_incapable):
        result = WeeklyResource().select([resource_incapable])

        assert result == []

    def test_complex_mixed_scenario(
        self,
        resource_available_no_refresh,
        resource_available_has_refreshed,
        resource_available_has_refreshed_later,
        resource_capped,
        no_lumnis_data,
    ):
        characters = [
            resource_capped,
            resource_available_has_refreshed,
            no_lumnis_data,
            resource_available_no_refresh,
            resource_available_has_refreshed_later,
        ]
        result = WeeklyResource().select(characters)

        expected = [
            resource_available_no_refresh,
            resource_available_has_refreshed,
            resource_available_has_refreshed_later,
        ]
        assert result == expected
