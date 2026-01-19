"""Weekly Lumnis login strategy."""

from datetime import UTC, datetime
from typing import List, Optional

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.base import LoginStrategy


class WeeklyLumnis(LoginStrategy):
    """Login strategy that orders characters by Lumnis priority.

    This strategy focuses on characters who haven't yet completed their weekly
    Lumnis experience bonus. It will return an empty list when all characters
    have completed their bonus, allowing the system to fall back to other strategies.

    Ranking logic:
    1. Characters with a refresh date of None are returned first. This means we need the character to sync their data
       or start their Lumnis cycle.
    2. Characters that have started but not completed are ranked by earliest refresh date
    3. Returns empty list if all characters have completed their bonus
    """

    def _get_lumnis_total(self, character) -> Optional[int]:
        if not character.lumnis:
            return None

        return (
            (character.lumnis.lumnis_2x or 0)
            + (character.lumnis.lumnis_3x or 0)
            + (character.lumnis.lumnis_4x or 0)
            + (character.lumnis.lumnis_5x or 0)
        )

    def _has_lumnis_remaining(self, character) -> bool:
        total = self._get_lumnis_total(character)
        return total is None or total > 0

    def _has_refresh(self, character) -> bool:
        return character.lumnis is not None and character.lumnis.refresh is not None

    def _get_refresh_date(self, character) -> datetime:
        return (
            datetime.min.replace(tzinfo=UTC)
            if character.lumnis is None or character.lumnis.refresh is None
            else character.lumnis.refresh
        )

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Order characters by Lumnis priority.

        Args:
            characters: List of CharacterData objects from the API.

        Returns:
            Characters who should be logged in according to the strategy.
        """
        not_refreshed = [c for c in characters if not self._has_refresh(c)]
        if not_refreshed:
            return not_refreshed

        need_lumnis = [c for c in characters if self._has_lumnis_remaining(c)]
        if need_lumnis:
            return sorted(need_lumnis, key=lambda c: self._get_refresh_date(c))

        return []
