# Charman Daemon Configuration
# Edit these values directly for now
from dataclasses import dataclass

# Path to Ruby executable
RUBY_BIN = "/usr/bin/ruby"

# Path to Lich script
LICH_BIN = "/home/corgibutts/Lich5/lich.rb"

# API server URL
API_URL = "http://api:8000"


# Characters to manage (list of character names)
# Eventually we'll pull this from the API
@dataclass
class CharData:
    name: str
    account: str  # We don't need to put the actual account name here because Lich handles the login
    favored: bool = False


CHARACTERS = {
    "grahl": CharData("grahl", "account1", True),
    "saero": CharData("saero", "account1"),
    "halgrin": CharData("halgrin", "account1"),
    "khaor": CharData("khaor", "account2", True),
    "moroha": CharData("moroha", "account2"),
    "telidar": CharData("telidar", "account2"),
    "virelda": CharData("virelda", "account3"),
    "thaurin": CharData("thaurin", "account3", True),
    "umbrik": CharData("umbrik", "account3"),
    "azurai": CharData("azurai", "account3"),
}
