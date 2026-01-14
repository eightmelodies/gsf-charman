"""Favored character login strategy."""

from typing import List, Set

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.base import LoginStrategy


class FavoredCharacter(LoginStrategy):
    """Login strategy that returns favored characters.

    This is a fallback strategy that selects favored characters to receive
    the remainder of login time when other strategies don't return results.
    Favored characters are defined in the daemon's configuration and passed
    to this strategy's constructor.

    The strategy preserves the original order of characters from the input list
    rather than imposing its own sorting, as the order may have significance
    from previous strategy evaluations.
    """

    def __init__(self, favored_characters: List[str]):
        """Initialize the strategy with a list of favored character names.

        Args:
            favored_characters: List of character names that should be favored

        Raises:
            ValueError: If no favored characters are provided (empty list or None)
        """
        if not favored_characters:
            raise ValueError("At least one favored character must be defined")
        self.favored_characters: Set[str] = {name.lower() for name in favored_characters}

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Select favored characters from the input list.

        Returns characters whose names are in the favored list, preserving
        their original order from the input. This ensures that any ordering
        significance from previous strategy evaluations is maintained.

        Args:
            characters: List of CharacterData objects from the API

        Returns:
            List of favored characters in their original input order.
            Returns empty list if no characters match the favored list.
        """
        return [char for char in characters if char.name in self.favored_characters]
