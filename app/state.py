# app/state.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ScreenID(Enum):
    """
    Identifiers for all application screens.

    Screens are referenced through these values instead of importing
    screen classes into one another.
    """

    MAIN_MENU = auto()
    MATCH_SETUP = auto()
    SETTINGS = auto()
    TEST_MENU = auto()


@dataclass(slots=True)
class AppState:
    """
    Shared application navigation state.

    This state describes which screen is active and which screen should be
    returned to when the user presses Back or Escape.
    """

    current_screen: ScreenID = ScreenID.MAIN_MENU
    previous_screen: Optional[ScreenID] = None
    screen_history: list[ScreenID] = field(default_factory=list)
    running: bool = True

    def change_screen(
        self,
        screen_id: ScreenID,
        *,
        remember_current: bool = True,
    ) -> None:
        """
        Change the active screen.

        Parameters
        ----------
        screen_id:
            Screen that should become active.

        remember_current:
            When True, the current screen is added to the navigation history.
            This allows go_back() to return to it later.
        """
        if not isinstance(screen_id, ScreenID):
            raise TypeError(
                "screen_id must be an instance of ScreenID, "
                f"got {type(screen_id).__name__}"
            )

        if screen_id == self.current_screen:
            return

        if remember_current:
            self.screen_history.append(self.current_screen)

        self.previous_screen = self.current_screen
        self.current_screen = screen_id

    def go_back(self) -> bool:
        """
        Return to the most recently visited screen.

        Returns
        -------
        bool
            True when navigation occurred, otherwise False.
        """
        if not self.screen_history:
            return False

        destination = self.screen_history.pop()

        self.previous_screen = self.current_screen
        self.current_screen = destination

        return True

    def go_to_main_menu(self) -> None:
        """
        Return directly to the main menu and clear navigation history.
        """
        self.previous_screen = self.current_screen
        self.current_screen = ScreenID.MAIN_MENU
        self.screen_history.clear()

    def request_exit(self) -> None:
        """
        Signal that the application main loop should stop.
        """
        self.running = False

