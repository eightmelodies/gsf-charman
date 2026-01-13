from datetime import datetime, time, timedelta, timezone
from typing import List
from zoneinfo import ZoneInfo

from gsfcharman.api.data import CharacterData
from gsfcharman.daemon.strategies.base import LoginStrategy


class DailyLogin(LoginStrategy):
    """Given a list of characters, returns all characters that have not logged in before midnight Eastern time.

    Since it's likely other people might be doing this around the same time and to give ourselves a bit of wiggle
    room for character heartbeat updates, we delay the daily login for a bit.

    Note: order doesn't matter as all characters share the same deadline for getting their daily bonus.
    """

    LOGIN_OFFSET = timedelta(minutes=27)

    def _get_when_login_reset(self) -> datetime:
        today_midnight = datetime.combine(datetime.now(ZoneInfo("America/New_York")), time.min)
        return (today_midnight + self.LOGIN_OFFSET).astimezone(timezone.utc)

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        return list(
            [
                c
                for c in characters
                if c.heartbeat and c.heartbeat.last_update and c.heartbeat.last_update < self._get_when_login_reset()
            ]
        )
