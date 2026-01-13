"""Charman Daemon - Manages Gemstone character sessions."""

import subprocess
import time

from gsfcharman.daemon.config import API_URL, LICH_BIN, RUBY_BIN


class CharmanDaemon:
    """Daemon that manages Lich processes for characters."""

    def __init__(self, dryrun=True):
        self.processes: dict[str, subprocess.Popen] = {}
        self.api_url = API_URL
        self.dryrun = dryrun

    def start_lich(self, character_name: str, port: int = 9000) -> subprocess.Popen:
        """Start a Lich process for a character."""
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

    def run(self):
        """Main daemon loop."""

        while True:
            # TODO: poll the API server, get list of characters that should be logged in from our strategy, and process

            time.sleep(1)


def main():
    """Entry point for the daemon."""
    daemon = CharmanDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
