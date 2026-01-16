"""Charman Daemon - Manages Gemstone character sessions with async multi-account support."""

import asyncio
import time

from gsfcharman.daemon.config import CHARACTERS
from gsfcharman.daemon.login_orchestrator_async import AsyncLoginOrchestrator
from gsfcharman.daemon.strategies.daily_login import DailyLogin
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter
from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis
from gsfcharman.daemon.strategies.weekly_resource import WeeklyResource


class CharmanDaemon:
    """Daemon that manages Lich processes for characters across multiple accounts."""

    def __init__(self, dryrun: bool = True):
        self.dryrun = dryrun
        self.account_orchestrators = self._create_account_orchestrators()

    def _create_account_orchestrators(self):
        """Create orchestrators for each account by grouping characters."""
        # Group characters by account
        accounts = {}
        for char_name, char_data in CHARACTERS.items():
            if char_data.account not in accounts:
                accounts[char_data.account] = []
            accounts[char_data.account].append(char_name)

        # Create orchestrator per account
        orchestrators = {}
        for account, characters in accounts.items():
            # Get favored characters for this account
            favored_chars = [c for c in characters if CHARACTERS[c].favored]

            orchestrators[account] = AsyncLoginOrchestrator(
                strategies=[
                    WeeklyLumnis(),
                    WeeklyResource(),
                    DailyLogin(),
                    FavoredCharacter(favored_chars),
                ],
                characters=characters,
                account=account,
                dryrun=self.dryrun,
            )

        print(f"Created {len(orchestrators)} account orchestrators:")
        for account, orchestrator in orchestrators.items():
            print(f"  - Account {account}: {len(orchestrator.characters)} characters")

        return orchestrators

    async def run(self):
        """Main daemon loop using async/await for concurrent account processing."""
        print("Charman Daemon started. Press Ctrl+C to exit.")

        try:
            while True:
                start_time = time.time()

                print(f"\n--- Daemon cycle started at {time.strftime('%H:%M:%S')} ---")

                # Run all account orchestrators concurrently
                tasks = [orchestrator.login_character() for orchestrator in self.account_orchestrators.values()]

                # Execute all tasks concurrently with error handling
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Report results
                for account, result in zip(self.account_orchestrators.keys(), results):
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
        """Clean up all account orchestrators."""
        print("Cleaning up account orchestrators...")

        # Clean up all orchestrators concurrently
        cleanup_tasks = [orchestrator.close() for orchestrator in self.account_orchestrators.values()]

        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        print("All account orchestrators cleaned up.")


def main():
    """Entry point for the daemon."""
    daemon = CharmanDaemon()
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
