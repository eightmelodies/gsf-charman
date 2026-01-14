"""Login strategies package."""

from gsfcharman.daemon.strategies.base import LoginStrategy
from gsfcharman.daemon.strategies.daily_login import DailyLogin
from gsfcharman.daemon.strategies.favored_character import FavoredCharacter
from gsfcharman.daemon.strategies.weekly_lumnis import WeeklyLumnis

__all__ = ["LoginStrategy", "FavoredCharacter", "WeeklyLumnis", "DailyLogin"]
