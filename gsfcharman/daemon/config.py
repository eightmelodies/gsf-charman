# Charman Daemon Configuration
# Edit these values directly for now
from dataclasses import dataclass

# Path to Ruby executable
RUBY_BIN = "/usr/bin/ruby"

# Path to Lich script
LICH_BIN = "/home/corgibutts/Lich5/lich.rb"

# API server URL
API_URL = "http://localhost:8000"


# Characters to manage (list of character names)
# Eventually we'll pull this from the API
@dataclass
class CharData:
    name: str
    account: str
    priority: int = 0


CHARACTERS = {"azurai": CharData("Azurai", "account1")}
