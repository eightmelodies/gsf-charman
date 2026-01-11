"""Abstract base class for login strategies."""

from abc import ABC, abstractmethod
from typing import List

from gsfcharman.api.data import CharacterData


class LoginStrategy(ABC):
    """Abstract base class for character login strategies.

    A login strategy determines which character(s) should currently be logged in
    based on character data. Strategies can be combined or layered to create
    more complex decision-making logic.

    Strategies may return an empty list when no characters meet the strategy's
    criteria, which allows for layered strategy evaluation where subsequent
    strategies can be tried.
    """

    @abstractmethod
    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Order characters by preference based on strategy criteria.

        Strategies should return characters that meet the strategy's criteria,
        sorted by preference/rank. Characters earlier in the list are preferred
        for login. The first character in the list is the optimal choice.

        Args:
            characters: List of CharacterData objects from the API

        Returns:
            Characters that meet the strategy criteria, ordered by preference
            (highest preference first). May return an empty list if no characters
            meet the strategy's criteria, enabling layered strategy evaluation.
        """
        pass
