"""Tests for FavoredCharacter strategy."""

import pytest

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter


class TestFavoredCharacterStrategy:
    """Test cases for FavoredCharacter strategy."""

    def test_constructor_validation_empty_list(self):
        """Constructor should raise ValueError when empty list provided."""
        with pytest.raises(ValueError, match="At least one favored character must be defined"):
            FavoredCharacter([])

    def test_constructor_valid_list(self):
        """Constructor should accept valid non-empty list."""
        favored_chars = ["char1", "char2"]
        strategy = FavoredCharacter(favored_chars)
        assert strategy.favored_characters == {"char1", "char2"}

    def test_select_favored_characters(self):
        """Should return only favored characters from input list."""
        strategy = FavoredCharacter(["char1", "char2"])

        characters = [
            CharacterData(name="char1"),
            CharacterData(name="char3"),
            CharacterData(name="char2"),
            CharacterData(name="char4"),
        ]

        result = strategy.select(characters)
        assert len(result) == 2
        assert result[0].name == "char1"
        assert result[1].name == "char2"

    def test_select_preserves_order(self):
        """Should preserve original order of characters from input."""
        strategy = FavoredCharacter(["char1", "char2", "char3"])

        characters = [
            CharacterData(name="char2"),
            CharacterData(name="char1"),
            CharacterData(name="char3"),
            CharacterData(name="char4"),
        ]

        result = strategy.select(characters)
        assert len(result) == 3
        assert result[0].name == "char2"  # First in input
        assert result[1].name == "char1"  # Second in input
        assert result[2].name == "char3"  # Third in input

    def test_select_no_favored_characters(self):
        """Should return empty list when no favored characters in input."""
        strategy = FavoredCharacter(["char1", "char2"])

        characters = [
            CharacterData(name="char3"),
            CharacterData(name="char4"),
        ]

        result = strategy.select(characters)
        assert result == []

    def test_select_empty_input_list(self):
        """Should return empty list when input is empty."""
        strategy = FavoredCharacter(["char1", "char2"])
        result = strategy.select([])
        assert result == []

    def test_select_single_favored_character(self):
        """Should work correctly with single favored character."""
        strategy = FavoredCharacter(["char1"])

        characters = [
            CharacterData(name="char1"),
            CharacterData(name="char2"),
        ]

        result = strategy.select(characters)
        assert len(result) == 1
        assert result[0].name == "char1"

    def test_select_all_characters_favored(self):
        """Should return all characters when all are favored."""
        strategy = FavoredCharacter(["char1", "char2", "char3"])

        characters = [
            CharacterData(name="char1"),
            CharacterData(name="char2"),
            CharacterData(name="char3"),
        ]

        result = strategy.select(characters)
        assert len(result) == 3
        assert result[0].name == "char1"
        assert result[1].name == "char2"
        assert result[2].name == "char3"
