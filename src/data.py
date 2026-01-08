import json
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel


class LumnisData(BaseModel):
    lumnis_3x: int
    lumnis_2x: int
    weekly_resource: int
    refresh: datetime
    last_update: datetime


class SafeToLogoutData(BaseModel):
    safe_to_logout: bool
    last_update: datetime


class CharacterData(BaseModel):
    name: str
    lumnis: LumnisData
    logout_safety: SafeToLogoutData


type CharData = dict[str, CharacterData]


def now():
    return datetime.now(datetime.timezone.utc)


class Database:
    FILE_LOCATION = "chardata/"
    PERIODIC_WRITE_INTERVAL_SECONDS = 10

    data: CharData
    lastSaved: dict[str, datetime]

    def __init__(self, data: CharData = None):
        self.data = data if data else {}
        self.lastSaved = {}

    def load(self):
        self.data = {}
        directory = Path(self.FILE_LOCATION)
        for file_path in [p for p in directory.iterdir() if p.is_file() and p.suffix == ".json"]:
            with open(file_path, "r") as file:
                self.data[file_path.stem] = CharacterData(**json.load(file))

    def save(self):
        for char, char_data in self.data.items():
            with open(f"{self.FILE_LOCATION}/{char}.json", "w") as file:
                if self.lastSaved[char] + timedelta.seconds(self.PERIODIC_WRITE_INTERVAL_SECONDS) <= now():
                    json.dump(char_data.model_dump_json(indent=2, by_alias=True), file)
                    self.lastSaved[char] = now()

    def characters(self) -> list[str]:
        return self.data.keys()
