
# app/state.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class ScreenID(Enum):
    """
    Identifiers for application screens.
    """

    MAIN_MENU = auto()
    MATCH_SETUP = auto()
    GAME = auto()
    SETTINGS = auto()
    ABOUT = auto()
    TEST_MENU = auto()


@dataclass(slots=True)
class AppState:
    """
    Mutable application navigation state.
    """

    current_screen: ScreenID = ScreenID.MAIN_MENU
    previous_screen: ScreenID | None = None

    screen_history: list[ScreenID] = field(
        default_factory=list
    )

    running: bool = True

    def change_screen(
        self,
        screen_id: ScreenID,
        *,
        remember_current: bool = True,
    ) -> None:
        """
        Change the active screen and optionally store navigation history.
        """
        if screen_id is self.current_screen:
            return

        if remember_current:
            self.screen_history.append(
                self.current_screen
            )

        self.previous_screen = self.current_screen
        self.current_screen = screen_id

    def go_back(self) -> bool:
        """
        Return to the most recently visited screen.

        Returns False when no previous screen exists.
        """
        if not self.screen_history:
            return False

        target = self.screen_history.pop()

        self.previous_screen = self.current_screen
        self.current_screen = target

        return True

    def go_to_main_menu(self) -> None:
        """
        Return directly to the main menu and clear navigation history.
        """
        self.previous_screen = self.current_screen
        self.current_screen = ScreenID.MAIN_MENU
        self.screen_history.clear()

    def request_exit(self) -> None:
        self.running = False

