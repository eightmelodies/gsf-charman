from datetime import datetime, time, timedelta, timezone
from typing import List, Optional
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

    def _get_character_last_active_time(self, character: CharacterData) -> Optional[datetime]:
        """Returns when a character was last logged in and active"""
        if not character.session:
            return None
        elif character.session.is_logged_in and character.session.last_update:
            return character.session.last_update
        elif character.session.last_logon:
            return character.session.last_logon
        else:
            return None

    def select(self, characters: List[CharacterData]) -> List[CharacterData]:
        return list(
            [
                c
                for c in characters
                if (self._get_character_last_active_time(c) or datetime.min.replace(tzinfo=timezone.utc))
                < self._get_when_login_reset()
            ]
        )
