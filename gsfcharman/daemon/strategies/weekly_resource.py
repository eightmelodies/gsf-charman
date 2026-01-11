"""Weekly resource login strategy."""

from datetime import datetime, timezone
from typing import List

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.base import LoginStrategy

WEEKLY_RESOURCE_CAP = 50000


class WeeklyResource(LoginStrategy):
    """Login strategy that orders characters by weekly resource priority.

    This strategy focuses on characters who can earn weekly resource but haven't
    yet reached their cap.
    """

    def _can_earn_resource(self, character: CharacterData) -> bool:
        """Returns whether or not the chracter is capable of earning weekly resource."""
        return (
            character.lumnis is not None
            and character.lumnis.lumnis_2x is not None
            and character.lumnis.weekly_resource is not None
            and character.lumnis.weekly_resource > 0
        )

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Order characters by weekly resource priority.

        Args:
            characters: List of CharacterData objects from the API

        Returns:
            Characters who can earn weekly resource, sorted by priority.
            Characters with weekly_resource=0 and refresh=None come first (equally ranked),
            then characters with refresh dates (sorted by earliest first).
            Returns empty list if no characters meet the criteria.
        """
        # Filter to characters that can earn weekly resource
        eligible_chars = [
            c
            for c in characters
            if c.lumnis and c.lumnis.weekly_resource is not None and c.lumnis.weekly_resource < WEEKLY_RESOURCE_CAP
        ]

        # Sort by upcoming refresh date (ie., the earlier the refresh date the higher the priority)
        date_max = datetime.max.replace(tzinfo=timezone.utc)
        date_min = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(eligible_chars, key=lambda c: c.lumnis.refresh or date_min if c.lumnis else date_max)
