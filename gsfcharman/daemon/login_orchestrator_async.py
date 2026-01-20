"""Async Login Orchestrator - Manages character login/logout decisions using strategies with async support."""

import subprocess
from typing import Dict

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.config import LICH_BIN, RUBY_BIN
from gsfcharman.daemon.data.characters import Characters
from gsfcharman.daemon.strategies.base import LoginStrategy


class AsyncLoginOrchestrator:
    """Async orchestrator for character login decisions using layered strategies."""

    def __init__(
        self,
        strategies: list[LoginStrategy],
        account: str,
        characters: Characters,
        dryrun: bool = True,
    ):
        self.strategies = strategies
        self.characters = characters
        self.account = account
        self.dryrun = dryrun
        self.processes: Dict[str, subprocess.Popen] = {}

    def start_lich(self, character_name: str, port: int = 9000) -> subprocess.Popen:
        """Start a Lich process for a character."""
        # TODO: dynamic ports
        cmd = [
            RUBY_BIN,
            LICH_BIN,
            "--login",
            character_name,
            "--shattered",
            "--detachable-client",
            str(port),
            "--without-frontend",
            "--start-scripts",
            "charman",
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.processes[character_name] = process
        return process

    def stop_lich(self, character_name: str) -> bool:
        """Stop a Lich process for a character."""
        process = self.processes.get(character_name)
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes[character_name]
            return True
        return False

    def get_character_selected_for_login(self) -> CharacterData:
        characters = self.characters.get_characters_for_account(self.account)
        print(f"evaluating strategies for account {self.account} and characters {characters}")
        for strategy in self.strategies:
            selected_characters = strategy.select(characters)
            print(f"  {strategy.__class__.__name__} selected {[c.name for c in selected_characters]}")
            if selected_characters:
                print(f"  selected {selected_characters[0].name}")
                return selected_characters[0]

        raise RuntimeError("No characters selected by any strategy")

    async def login_character(self):
        """Handle the complete login workflow.

        Gets the currently logged in character, determines who should be logged in,
        and handles the transition if needed.

        Returns:
            True if a login action was performed, False if no action was needed
        """
        current_character = self.characters.get_character_logged_in_for_account(self.account)
        target_character = self.get_character_selected_for_login()

        if current_character != target_character:
            if current_character:
                print(f"current logged in character is {current_character.name} and selected {target_character.name}")
                if self.dryrun:
                    print(f"[DRYRUN] Account {self.account}: Would log out {current_character.name}...")
                else:
                    print(f"Account {self.account}: Logging out {current_character.name}...")
                    self.stop_lich(current_character.name)

        if self.dryrun:
            print(f"[DRYRUN] Account {self.account}: Would log in {target_character.name}...")
        else:
            print(f"Account {self.account}: Logging in {target_character.name}...")
            self.start_lich(target_character.name)

    async def close(self):
        """Close the HTTP client and clean up processes."""
        # Clean up any running processes
        for char_name, process in self.processes.items():
            print(f"Account {self.account}: Stopping Lich process for {char_name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close the client."""
        await self.close()
