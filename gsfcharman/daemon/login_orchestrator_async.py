"""Async Login Orchestrator - Manages character login/logout decisions using strategies with async support."""

import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, MutableMapping, Optional

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.data.characters import Characters, MultipleCharactersLoggedIn
from gsfcharman.daemon.strategies.base import LoginStrategy


class AccountLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(logger, extra)

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:
        extra = {**(self.extra or {}), **kwargs.get("extra", {})}
        kwargs["extra"] = extra
        return msg, kwargs


GAME_CODE_MAPPINGS = {"GS3": ["--gemstone"], "GST": ["--gemstone", "--test"], "GSF": ["--shattered"]}


@dataclass
class ProcessInfo:
    when_started: datetime
    p_open: subprocess.Popen
    character: str
    when_logoff_requested: Optional[datetime] = None


class AsyncLoginOrchestrator:
    """Async orchestrator for character login decisions using layered strategies."""

    def __init__(
        self,
        strategies: list[LoginStrategy],
        account: str,
        characters: Characters,
        port: str,
        ruby_bin: Optional[str] = None,
        lich_bin: Optional[str] = None,
    ):
        self.strategies = strategies
        self.characters = characters
        self.account = account
        self.port = port
        self.ruby_bin = ruby_bin or os.environ.get("RUBY_BIN", "/usr/bin/ruby")
        self.lich_bin = lich_bin or os.environ.get("LICH_BIN", "/opt/Lich5/lich.rbw")
        self.process: Optional[ProcessInfo] = None
        self.logger = AccountLoggerAdapter(logging.getLogger(__name__), {"account": self.account})

    def _log_extra(self):
        return {"character": self.process.character if self.process else "N/A"}

    def _get_game_code_argument(self, character: CharacterData) -> list[str]:
        character_entry_data = [
            c for c in self.characters.accounts[self.account].characters if c.name == character.name
        ]
        if not character_entry_data:
            raise RuntimeError(f"could not locate {character.name} in Lich entry data")
        game_code = character_entry_data[0].game_code.upper()
        if game_code not in GAME_CODE_MAPPINGS:
            raise RuntimeError(f"game code {game_code} not in known game code mappings: {GAME_CODE_MAPPINGS}")
        return GAME_CODE_MAPPINGS[game_code]

    def _check_process(self):
        if not self.process:
            return

        p_open = self.process.p_open
        rcode = p_open.poll()
        pid = p_open.pid
        if rcode is None:
            self.logger.debug(f"lich process still running with pid {pid}", extra=self._log_extra())
        else:
            try:
                self.characters.delete_logout_request(self.process.character)
            except Exception as e:
                self.logger.error(
                    f"could not delete pending logout request for {self.process.character}: {e}",
                    extra=self._log_extra(),
                )

            self.process = None

            try:
                output, _ = p_open.communicate(timeout=10)
                self.logger.info(
                    f"lich process with pid {pid} completed with rcode {rcode}: {output}", extra=self._log_extra()
                )
            except subprocess.TimeoutExpired:
                self.logger.warning(
                    f"lich process with pid {pid} timed out and is getting killed", extra=self._log_extra()
                )
                p_open.kill()
                output, _ = p_open.communicate()
                self.logger.warning(
                    f"lich process with pid {pid} killed with rcode {rcode}: {output}", extra=self._log_extra()
                )

    def start_lich(self, character: CharacterData):
        """Start a Lich process for a character."""
        if self.process:
            raise RuntimeError(f"cannot start lich: lich is already running for {self.process.character}")

        cmd = [
            self.ruby_bin,
            self.lich_bin,
            "--login",
            character.name,
            *self._get_game_code_argument(character),
            f"--detachable-client=0.0.0.0:{self.port}",
            "--without-frontend",
            "--start-scripts=charman",
        ]
        self.logger.info(f"spawning lich process with cmd: {shlex.join(cmd)}", extra=self._log_extra())
        p_open = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.process = ProcessInfo(when_started=datetime.now(UTC), p_open=p_open, character=character.name)

    def stop_lich(self):
        """Stop a Lich process."""
        if not self.process:
            raise RuntimeError("cannot stop lich: process does not exist")

        self.logger.info(
            f"Account {self.account}: Stopping Lich process for {self.process.character}...", extra=self._log_extra()
        )
        p_open = self.process.p_open
        self.process = None
        p_open.terminate()
        try:
            p_open.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p_open.kill()

    def get_character_selected_for_login(self) -> CharacterData:
        characters = self.characters.get_characters_for_account(self.account)
        self.logger.debug(
            f"evaluating strategies for account {self.account} and characters {characters}", extra=self._log_extra()
        )
        for strategy in self.strategies:
            selected_characters = strategy.select(characters)
            self.logger.info(
                f"{strategy.__class__.__name__} selected {[c.name for c in selected_characters]}",
                extra=self._log_extra(),
            )
            if selected_characters:
                self.logger.info(f"selected {selected_characters[0].name}", extra=self._log_extra())
                return selected_characters[0]

        raise RuntimeError("No characters selected by any strategy")

    def get_character_currently_logged_in(self) -> Optional[CharacterData]:
        try:
            api_character = [self.characters.get_character_logged_in_for_account(self.account)]
        except MultipleCharactersLoggedIn as e:
            self.logger.warning(f"{e}", extra=self._log_extra())
            # TODO: We need to eventually reconcile the API with what the process running currently is
            # For now, warn about any abnormalities and just use what reflects our process
            # We might even just switch to having the daemon update the logged_in field instead of the lich script
            # with the downside being we lose "logged in" from the perspective that lich is running with our script
            if self.process and self.process.character not in e.characters:
                self.logger.warning(
                    f"lich process open for {self.process.character}, but API shows {e.characters} logged in",
                    extra=self._log_extra(),
                )
        else:
            if not api_character and self.process:
                self.logger.warning(
                    f"API shows no logins but we have a running process for {self.process.character}",
                    extra=self._log_extra(),
                )

        return self.characters.get_character(self.process.character) if self.process else None

    def send_logout_request_if_needed(self, current_character: CharacterData, target_character: CharacterData):
        if (
            (current_character.name != target_character.name)
            and self.process
            and not self.process.when_logoff_requested
        ):
            self.process.when_logoff_requested = datetime.now(UTC)
            self.characters.put_logout_request(current_character)
            self.logger.info(f"sending logout request for {current_character.name}", extra=self._log_extra())
        elif self.process and self.process.when_logoff_requested:
            request_duration = datetime.now(UTC) - self.process.when_logoff_requested
            self.logger.info(
                f"pending logout request for {current_character.name} active for {request_duration}",
                extra=self._log_extra(),
            )

    async def orchestrate(self):
        current_character = self.get_character_currently_logged_in()
        target_character = self.get_character_selected_for_login()

        if current_character:
            self.send_logout_request_if_needed(current_character, target_character)

        self._check_process()
        if self.process:
            self.logger.info(f"currently running lich: {self.process}", extra=self._log_extra())
            return

        current_character = self.get_character_currently_logged_in()
        self.logger.info(
            f"current character is {current_character.name if current_character else None} and target character is {target_character.name}",
            extra=self._log_extra(),
        )
        self.logger.info(f"starting lich process for {target_character.name}", extra=self._log_extra())
        self.start_lich(target_character)

    async def close(self):
        """Clean up process."""
        if self.process:
            self.stop_lich()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close the client."""
        await self.close()
