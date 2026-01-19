"""Weekly Lumnis login strategy."""

from datetime import datetime
from typing import List, Optional

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.base import LoginStrategy


def _get_lumnis_3x(char: CharacterData) -> int:
    """Get lumnis_3x value, defaulting to 0 if None."""
    if not char.lumnis:
        return 0
    return char.lumnis.lumnis_3x if char.lumnis.lumnis_3x is not None else 0


def _get_lumnis_2x(char: CharacterData) -> int:
    """Get lumnis_2x value, defaulting to 0 if None."""
    if not char.lumnis:
        return 0
    return char.lumnis.lumnis_2x if char.lumnis.lumnis_2x is not None else 0


def _get_refresh(char: CharacterData) -> Optional[datetime]:
    """Get refresh datetime, or None if not set."""
    if not char.lumnis:
        return None
    return char.lumnis.refresh


def _has_completed_lumnis_bonus(char: CharacterData) -> bool:
    """Check if character has completed their weekly Lumnis bonus.

    A character has completed their bonus when both lumnis_2x and lumnis_3x are 0.
    """
    if not char.lumnis:
        return False
    lumnis_2x = _get_lumnis_2x(char)
    lumnis_3x = _get_lumnis_3x(char)
    return lumnis_2x == 0 and lumnis_3x == 0


class WeeklyLumnis(LoginStrategy):
    """Login strategy that orders characters by Lumnis refresh priority.

    This strategy focuses on characters who haven't yet completed their weekly
    Lumnis experience bonus. It will return an empty list when all characters
    have completed their bonus, allowing the system to fall back to other strategies.

    Ranking logic:
    1. Characters with Lumnis available (7300/7300, refresh=None) are equally viable
    2. Characters that have started but not completed are ranked by earliest refresh date
    3. Characters that have completed their bonus are excluded
    4. Returns empty list if all characters have completed their bonus
    """

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Order characters by Lumnis refresh priority.

        Args:
            characters: List of CharacterData objects from the API

        Returns:
            Characters who haven't completed their weekly Lumnis bonus, sorted by
            priority. Characters with available Lumnis come first (equally ranked),
            then characters who have started but not completed (sorted by refresh date).
            Returns empty list if all characters have completed their bonus.
        """
        # Filter to only characters who have Lumnis data and haven't completed their bonus
        incomplete_chars = [
            char for char in characters if char.lumnis is not None and not _has_completed_lumnis_bonus(char)
        ]

        if not incomplete_chars:
            # All characters have completed their bonus or have no data, return empty list
            # to allow fallback to other strategies
            return []

        # Sort by priority:
        # 1. Characters with Lumnis available (refresh=None) come first
        # 2. Characters who have started (refresh is set) come after, sorted by refresh date
        return sorted(
            incomplete_chars,
            key=lambda char: (
                _get_refresh(char) is not None,  # has_refresh: False (0) sorts before True (1)
                _get_refresh(char) if _get_refresh(char) is not None else datetime.min,
            ),
        )


# TODO: update this for 4x/5x
# and eventually cash'lo'nae!
