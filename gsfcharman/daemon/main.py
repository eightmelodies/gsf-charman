"""Charman Daemon - Manages Gemstone character sessions with async multi-account support."""

import asyncio
import logging
import os
import signal
import sys
import time

import httpx

from gsfcharman.daemon.config import API_URL
from gsfcharman.daemon.data.characters import Characters
from gsfcharman.daemon.data.entries import Entries
from gsfcharman.daemon.login_orchestrator_async import AsyncLoginOrchestrator
from gsfcharman.daemon.strategies.daily_login import DailyLogin
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter
from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis
from gsfcharman.daemon.strategies.weekly_resource import WeeklyResource

logger = logging.getLogger(__name__)


class ContextualFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "account"):
            record.account = "unknown"
        if not hasattr(record, "character"):
            record.character = "N/A"
        return super().format(record)


formatter = ContextualFormatter("[%(account)s %(character)s] %(levelname)s: %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

PORTS = ["9000", "9001", "9002", "9003", "9004", "9005", "9006", "9007", "9008", "9009"]


class CharmanDaemon:
    """Daemon that manages Lich processes for characters across multiple accounts."""

    def __init__(self, entry_file_path: str):
        """
        Initialize the CharmanDaemon.

        Args:
            dryrun: If True, run in dry-run mode without actually starting Lich processes
            entry_file_path: Path to the entry.yaml file
        """
        self.api_client: httpx.Client = httpx.Client(base_url=API_URL)
        self.entries: Entries = Entries(entry_file_path)
        self.characters: Characters = Characters(self.api_client, self.entries)
        self.login_orchestrators: dict[str, AsyncLoginOrchestrator] = self._create_login_orchestrators()

        self._init_api_data()

    def _init_api_data(self):
        for account in self.entries.accounts:
            for character in self.characters.get_characters_for_account(account.name):
                try:
                    self.characters.delete_logout_request(character.name)
                except Exception as e:
                    logger.error(f"could not init logout request data for {character.name}: {e}")

                try:
                    self.characters.set_logged_out(character.name)
                except Exception as e:
                    logger.error(f"could not init is_logged_out data for {character.name}: {e}")

    def _create_login_orchestrators(self) -> dict[str, AsyncLoginOrchestrator]:
        port_mappings = dict(zip([a.name for a in self.entries.accounts], PORTS))
        logger.info(f"assigning account:port mappings as follows: {port_mappings}")
        return {
            a.name: AsyncLoginOrchestrator(
                [
                    DailyLogin(),
                    WeeklyLumnis(),
                    WeeklyResource(),
                    FavoredCharacter([c for c in self.characters.get_favorite_characters()]),
                ],
                a.name,
                self.characters,
                port_mappings[a.name],
            )
            for a in self.entries.accounts
        }

    async def run(self):
        """Main daemon loop using async/await for concurrent account processing."""
        logger.info("Charman Daemon started. Press Ctrl+C to exit.")

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _handle_signal(sig):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            stop_event.set()

        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))
        except NotImplementedError:
            # Windows does not support add_signal_handler
            pass

        try:
            while not stop_event.is_set():
                start_time = time.time()
                logger.debug(f"--- Daemon cycle started at {time.strftime('%H:%M:%S')} ---")

                tasks = [orchestrator.orchestrate() for orchestrator in self.login_orchestrators.values()]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for account, result in zip(self.login_orchestrators.keys(), results):
                    if isinstance(result, Exception):
                        logger.error(f"Error during daemon cycle: {result}", extra={"account": account})

                cycle_time = time.time() - start_time
                logger.debug(f"--- Daemon cycle completed in {cycle_time:.2f} seconds ---")

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=30)
                except asyncio.TimeoutError:
                    pass  # Timeout reached, continue loop

        except KeyboardInterrupt:
            # Fallback for Windows or if signal handling fails
            logger.info("KeyboardInterrupt received...")
        finally:
            logger.info("Shutting down daemon...")
            await self._cleanup()
            logger.info("Daemon stopped.")

    async def _cleanup(self):
        """Clean up all account orchestrators and the httpx client."""
        logger.info("Cleaning up account orchestrators...")

        # Clean up all orchestrators concurrently
        cleanup_tasks = [orchestrator.close() for orchestrator in self.login_orchestrators.values()]

        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        logger.info("All account orchestrators cleaned up.")


def main():
    """Entry point for the daemon."""
    lich_path = os.environ.get("LICH_PATH", "/opt/Lich5")
    daemon = CharmanDaemon(entry_file_path=f"{lich_path}/data/entry.yaml")
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
