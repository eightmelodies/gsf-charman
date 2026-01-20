import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel, StringConstraints


class LumnisData(BaseModel):
    lumnis_5x: Optional[int] = None
    lumnis_4x: Optional[int] = None
    lumnis_3x: Optional[int] = None
    lumnis_2x: Optional[int] = None
    donations: Optional[int] = None
    weekly_resource: Optional[int] = None
    refresh: Optional[datetime] = None
    last_update: Optional[datetime] = None


class PendingLogoutRequest(BaseModel):
    logout_requested: bool
    when_requested: datetime


class HeartbeatData(BaseModel):
    last_update: Optional[datetime] = None


class SessionData(BaseModel):
    last_update: Optional[datetime] = None
    last_logon: Optional[datetime] = None
    is_logged_in: Optional[bool] = None


class CharacterData(BaseModel):
    name: Annotated[str, StringConstraints(to_lower=True)]
    lumnis: Optional[LumnisData] = None
    pending_logout_request: Optional[PendingLogoutRequest] = None
    session: Optional[SessionData] = None


type CharData = dict[str, CharacterData]


def now():
    return datetime.now(timezone.utc)


class Database:
    FILE_LOCATION = "/var/lib/gsfcharman/chardata/"
    PERIODIC_WRITE_INTERVAL_SECONDS = 10

    data: CharData
    lastSaved: dict[str, datetime]
    file_location: str

    def __init__(self, data: Optional[CharData] = None, file_location: Optional[str] = None):
        self.data = data if data else {}
        self.lastSaved = {}
        self.file_location = file_location if file_location else self.FILE_LOCATION

    def load(self):
        self.data = {}
        directory = Path(self.file_location)
        for file_path in [p for p in directory.iterdir() if p.is_file() and p.suffix == ".json"]:
            with open(file_path, "r") as file:
                self.data[file_path.stem] = CharacterData(**json.load(file))

    def save(self):
        for char, char_data in self.data.items():
            if (
                self.lastSaved.get(char, datetime.min.replace(tzinfo=timezone.utc))
                + timedelta(seconds=self.PERIODIC_WRITE_INTERVAL_SECONDS)
            ) <= now():
                with open(f"{self.file_location}/{char}.json", "w") as file:
                    file.write(char_data.model_dump_json(by_alias=True, indent=2))
                    self.lastSaved[char] = now()

    def characters(self) -> set[str]:
        return set(self.data.keys())
