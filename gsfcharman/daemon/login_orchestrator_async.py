"""Async Login Orchestrator - Manages character login/logout decisions using strategies with async support."""

import os
import shlex
import subprocess
from typing import Dict, Optional

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.data.characters import Characters
from gsfcharman.daemon.strategies.base import LoginStrategy

GAME_CODE_MAPPINGS = {"GS3": ["--gemstone"], "GST": ["--gemstone", "--test"], "GSF": ["--shattered"]}


class AsyncLoginOrchestrator:
    """Async orchestrator for character login decisions using layered strategies."""

    def __init__(
        self,
        strategies: list[LoginStrategy],
        account: str,
        characters: Characters,
        ruby_bin: Optional[str] = None,
        lich_bin: Optional[str] = None,
        dryrun: bool = True,
    ):
        self.strategies = strategies
        self.characters = characters
        self.account = account
        self.ruby_bin = ruby_bin or os.environ.get("RUBY_BIN", "/usr/bin/ruby")
        self.lich_bin = lich_bin or os.environ.get("LICH_BIN", "/opt/Lich5/lich.rbw")
        self.dryrun = dryrun
        self.processes: Dict[str, subprocess.Popen] = {}

    def get_game_code_argument(self, character: CharacterData) -> list[str]:
        character_entry_data = [
            c for c in self.characters.accounts[self.account].characters if c.name == character.name
        ]
        if not character_entry_data:
            raise RuntimeError(f"could not locate {character.name} in Lich entry data")
        game_code = character_entry_data[0].game_code.upper()
        if game_code not in GAME_CODE_MAPPINGS:
            raise RuntimeError(f"game code {game_code} not in known game code mappings: {GAME_CODE_MAPPINGS}")
        return GAME_CODE_MAPPINGS[game_code]

    def start_lich(self, character: CharacterData, port: int = 9000):
        """Start a Lich process for a character."""
        # TODO: this should be its own method
        if character.name in self.processes:
            proc = self.processes[character.name]
            rcode = proc.poll()
            if rcode is None:
                print(f"lich process still running with pid {proc.pid}")
            else:
                output, _ = proc.communicate()
                print(f"lich process completed with pid {proc.pid} and rcode {rcode}: {output}")
                del self.processes[character.name]
            return

        # TODO: dynamic ports
        cmd = [
            self.ruby_bin,
            self.lich_bin,
            "--login",
            character.name,
            *self.get_game_code_argument(character),
            "--detachable-client",
            str(port),
            "--without-frontend",
            "--start-scripts",
            "charman",
        ]
        print(f"spawning lich process with cmd: {shlex.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.processes[character.name] = process

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
            self.start_lich(target_character)

    async def close(self):
        """Clean up processes."""
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
