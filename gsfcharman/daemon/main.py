"""Charman Daemon - Manages Gemstone character sessions."""

import time

from gsfcharman.daemon.config import API_URL, CHARACTERS
from gsfcharman.daemon.login_orchestrator import LoginOrchestrator
from gsfcharman.daemon.strategies.daily_login import DailyLogin
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter
from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis
from gsfcharman.daemon.strategies.weekly_resource import WeeklyResource


class CharmanDaemon:
    """Daemon that manages Lich processes for characters."""

    def __init__(self, dryrun: bool = True):
        self.dryrun = dryrun
        # Initialize login orchestrator with layered strategies
        self.login_orchestrator = LoginOrchestrator(
            strategies=[
                WeeklyLumnis(),
                WeeklyResource(),
                DailyLogin(),
                FavoredCharacter([char.name for char in CHARACTERS.values() if char.favored]),
            ],
            api_url=API_URL,
            dryrun=dryrun,
        )

    def run(self):
        """Main daemon loop."""
        print("Charman Daemon started. Press Ctrl+C to exit.")

        try:
            while True:
                try:
                    # Use orchestrator to handle the complete login workflow
                    action_performed = self.login_orchestrator.login_character()
                    if action_performed:
                        print("Login action performed")
                    else:
                        print("No login action needed")

                except Exception as e:
                    print(f"Error in daemon loop: {e}")

                # Poll every 30 seconds
                time.sleep(30)

        except KeyboardInterrupt:
            print("Shutting down daemon...")
            self.login_orchestrator.close()
            print("Daemon stopped.")


def main():
    """Entry point for the daemon."""
    daemon = CharmanDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
