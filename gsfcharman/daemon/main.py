"""Charman Daemon - Manages Gemstone character sessions with async multi-account support."""

import asyncio
import time

import httpx

from gsfcharman.daemon.data.characters import Characters
from gsfcharman.daemon.data.entries import Entries
from gsfcharman.daemon.login_orchestrator_async import AsyncLoginOrchestrator
from gsfcharman.daemon.strategies.daily_login import DailyLogin
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter
from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis
from gsfcharman.daemon.strategies.weekly_resource import WeeklyResource


class CharmanDaemon:
    """Daemon that manages Lich processes for characters across multiple accounts."""

    def __init__(self, dryrun: bool = True, entry_file_path: str = "entry.yaml"):
        """
        Initialize the CharmanDaemon.

        Args:
            dryrun: If True, run in dry-run mode without actually starting Lich processes
            entry_file_path: Path to the entry.yaml file
        """
        self.dryrun: bool = dryrun
        self.api_client: httpx.Client = httpx.Client()
        self.entries: Entries = Entries(entry_file_path)
        self.characters: Characters = Characters(self.api_client, self.entries)
        self.login_orchestrators: dict[str, AsyncLoginOrchestrator] = self._create_login_orchestrators()

    def _create_login_orchestrators(self) -> dict[str, AsyncLoginOrchestrator]:
        favorite_characters = [c for c in self.characters.get_favorite_characters()]
        return {
            a.name: AsyncLoginOrchestrator(
                [DailyLogin(), WeeklyLumnis(), WeeklyResource(), FavoredCharacter(favorite_characters)],
                a.name,
                self.characters,
            )
            for a in self.entries.accounts
        }

    async def run(self):
        """Main daemon loop using async/await for concurrent account processing."""
        print("Charman Daemon started. Press Ctrl+C to exit.")

        try:
            while True:
                start_time = time.time()

                print(f"\n--- Daemon cycle started at {time.strftime('%H:%M:%S')} ---")

                # Run all account orchestrators concurrently
                tasks = [orchestrator.login_character() for orchestrator in self.login_orchestrators.values()]

                # Execute all tasks concurrently with error handling
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Report results
                for account, result in zip(self.login_orchestrators.keys(), results):
                    if isinstance(result, Exception):
                        print(f"Account {account}: Error - {result}")
                    elif result:
                        print(f"Account {account}: Login action performed")
                    else:
                        print(f"Account {account}: No action needed")

                # Calculate and report cycle time
                cycle_time = time.time() - start_time
                print(f"--- Daemon cycle completed in {cycle_time:.2f} seconds ---")

                # Wait for next cycle
                await asyncio.sleep(30)

        except KeyboardInterrupt:
            print("\nShutting down daemon...")
            await self._cleanup()
            print("Daemon stopped.")

    async def _cleanup(self):
        """Clean up all account orchestrators and the httpx client."""
        print("Cleaning up account orchestrators...")

        # Clean up all orchestrators concurrently
        cleanup_tasks = [orchestrator.close() for orchestrator in self.login_orchestrators.values()]

        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        print("All account orchestrators and httpx client cleaned up.")


def main():
    """Entry point for the daemon."""
    daemon = CharmanDaemon()
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
