from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class CharacterEntry:
    """Represents a character entry from entry.yaml."""

    name: str
    game_code: str  # TODO: support different game modes?
    is_favorite: bool = False


@dataclass
class AccountEntry:
    """Represents an account entry from entry.yaml."""

    name: str
    characters: list[CharacterEntry] = field(default_factory=list)


class Entries:
    """Reads entry.yaml and loads game/account/character data."""

    def __init__(
        self,
        entry_file_path: str = "entry.yaml",
    ):
        """
        Initialize the CharacterDataManager.

        Args:
            entry_file_path: Path to the entry.yaml file (relative to project root)
        """
        self.entry_file_path = Path(entry_file_path)
        self.accounts: list[AccountEntry] = []
        self.load()

    def load(self):
        """Load and parse the entry.yaml file.

        Raises:
            ValueError: If the entry file does not exist or results in invalid data.
        """
        if not self.entry_file_path.exists():
            raise ValueError(f"Entry file not found: {self.entry_file_path}")

        with open(self.entry_file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not data or "accounts" not in data:
            raise ValueError("Invalid entry.yaml format: missing accounts section")

        self.accounts = [a for a in data["accounts"].values()]
        print(f"Successfully loaded {len(self.accounts)} accounts")
