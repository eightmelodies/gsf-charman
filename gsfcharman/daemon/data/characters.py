from typing import Optional

import httpx

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.data.entries import AccountEntry, Entries


class Characters:
    """Character data access via the API."""

    def __init__(self, client: httpx.Client, entries: Entries):
        self.client: httpx.Client = client
        self.client.event_hooks["response"].append(lambda r: r.raise_for_status())
        self.accounts: dict[str, AccountEntry] = {a.name: a for a in entries.accounts}

        self._sync_entries()

    def _sync_entries(self):
        """Do the initial character creation on the API for any characters in our entry data that don't exist"""
        for account in self.accounts.values():
            for character in account.characters:
                try:
                    self.get_character(character.name)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        self.create_character(CharacterData(name=character.name))
                    else:
                        raise exc

    def create_character(self, data: CharacterData) -> httpx.Response:
        return self.client.post(f"/characters/{data.name}", json=data)

    def get_character(self, name: str) -> CharacterData:
        return CharacterData(**self.client.get(f"/characters/{name}").json())

    def get_characters_for_account(self, account: str) -> list[CharacterData]:
        if account not in self.accounts.keys():
            raise KeyError(f"account {account} not found in accounts {self.accounts}")
        return [self.get_character(c.name) for c in self.accounts[account].characters]

    def get_character_logged_in_for_account(self, account: str) -> Optional[CharacterData]:
        if account not in self.accounts.keys():
            raise KeyError(f"account {account} not found in accounts {self.accounts}")

        logged_in = [c for c in self.get_characters_for_account(account) if c.session and c.session.is_logged_in]
        if len(logged_in) == 0:
            return None
        elif len(logged_in) == 1:
            return logged_in[0]
        else:
            raise RuntimeError("expected only one character to be logged into account {account}, but got: {logged_in}")

    def get_favorite_characters(self) -> list[str]:
        return [c.name for a in self.accounts.values() for c in a.characters]
