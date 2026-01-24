from datetime import UTC, datetime
from typing import Optional

import httpx

from gsfcharman.api.data import CharacterData, PendingLogoutRequest, SessionData
from gsfcharman.daemon.data.entries import AccountEntry, Entries


class MultipleCharactersLoggedIn(Exception):
    """Raised when multiple characters in the same account are marked as logged in by the API"""

    def __init__(
        self, account: str, characters: list[CharacterData], message: str = "Multiple characters logged into API"
    ):
        self.account = account
        self.characters = characters
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"Multiple characters logged in for account {self.account}: {[c.name for c in self.characters]}"


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
        return self.client.post(f"/characters/{data.name}", json=data.model_dump(mode="json"))

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
            raise MultipleCharactersLoggedIn(account, logged_in)

    def get_favorite_characters(self) -> list[str]:
        return [c.name for a in self.accounts.values() for c in a.characters if c.is_favorite]

    def put_logout_request(self, character: CharacterData, when_requested: Optional[datetime] = None):
        self.client.put(
            f"/characters/{character.name}/pending-logout-request",
            json=PendingLogoutRequest(
                logout_requested=True, when_requested=when_requested or datetime.now(UTC)
            ).model_dump(mode="json"),
        )

    def set_logged_out(self, character: str):
        # TODO: I think we can just drop the is_logged_in field..
        char_data = CharacterData(**self.client.get(f"/characters/{character}").json())
        if char_data.session and char_data.session.is_logged_in:
            self.client.put(
                f"characters/{character}/session",
                json=SessionData(
                    is_logged_in=False,
                    last_update=char_data.session.last_update,
                    last_logon=char_data.session.last_logon,
                ).model_dump(mode="json"),
            )

    def delete_logout_request(self, character: str):
        self.client.delete(f"/characters/{character}/pending-logout-request")
