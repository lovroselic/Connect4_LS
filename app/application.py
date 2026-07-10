# app/application.py

from __future__ import annotations

import pygame

from app import __version__
from app.config import AppConfig
from app.state import AppState, ScreenID
from ui.screens.base_screen import BaseScreen
from ui.screens.main_menu import MainMenuScreen
from ui.screens.match_setup import MatchSetupScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.test_menu import TestMenuScreen
from ui.theme import FONTS, THEME


class Application:
    """
    Main Connect4_LS application controller.

    The Application owns the Pygame lifecycle, window, clock, navigation
    state, screen registry, and main loop.
    """

    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.load()
        self.state = AppState()

        self.screen: pygame.Surface
        self.clock: pygame.time.Clock

        self.screens: dict[ScreenID, BaseScreen] = {}
        self.active_screen: BaseScreen | None = None

        self._pygame_initialized = False

        self._initialize_pygame()
        self._create_screens()
        self._activate_initial_screen()

    def run(self) -> None:
        """
        Run the main application loop.

        Pygame events, screen updates, drawing, and frame limiting are all
        coordinated here.
        """
        try:
            while self.state.running:
                delta_time = self.clock.tick(
                    self.config.target_fps
                ) / 1000.0

                self._process_events()

                if not self.state.running:
                    break

                if self.active_screen is None:
                    raise RuntimeError(
                        "Application has no active screen."
                    )

                self.active_screen.update(delta_time)
                self.active_screen.draw(self.screen)

                pygame.display.flip()

        finally:
            self.shutdown()

    def change_screen(
        self,
        screen_id: ScreenID,
        *,
        remember_current: bool = True,
    ) -> None:
        """
        Change to another registered screen.

        Parameters
        ----------
        screen_id:
            Destination screen.

        remember_current:
            When True, store the current screen in navigation history.
        """
        if screen_id not in self.screens:
            raise KeyError(
                f"Screen is not registered: {screen_id.name}"
            )

        if screen_id == self.state.current_screen:
            return

        if self.active_screen is not None:
            self.active_screen.on_exit()

        self.state.change_screen(
            screen_id,
            remember_current=remember_current,
        )

        self.active_screen = self.screens[screen_id]
        self.active_screen.on_enter()

    def go_back(self) -> None:
        """
        Return to the previously visited screen.

        When no previous screen exists, return to the main menu. Escape from
        the main menu itself is handled by MainMenuScreen and exits instead.
        """
        if self.active_screen is not None:
            self.active_screen.on_exit()

        if not self.state.go_back():
            self.state.go_to_main_menu()

        self.active_screen = self.screens[
            self.state.current_screen
        ]

        self.active_screen.on_enter()

    def go_to_main_menu(self) -> None:
        """
        Return directly to the main menu and clear navigation history.
        """
        if self.active_screen is not None:
            self.active_screen.on_exit()

        self.state.go_to_main_menu()

        self.active_screen = self.screens[
            ScreenID.MAIN_MENU
        ]

        self.active_screen.on_enter()

    def request_exit(self) -> None:
        """
        Request that the main loop stop after the current event cycle.
        """
        self.state.request_exit()

    def shutdown(self) -> None:
        """
        Release Pygame resources cleanly.

        Safe to call more than once.
        """
        if not self._pygame_initialized:
            return

        if self.active_screen is not None:
            self.active_screen.on_exit()

        FONTS.clear()
        pygame.quit()

        self._pygame_initialized = False

    def _initialize_pygame(self) -> None:
        """
        Initialize Pygame and create the application window.
        """
        pygame.init()

        if not pygame.get_init():
            raise RuntimeError(
                "Pygame failed to initialize."
            )

        self._pygame_initialized = True

        display_flags = pygame.RESIZABLE

        if self.config.fullscreen:
            display_flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode(
            (
                self.config.window_width,
                self.config.window_height,
            ),
            display_flags,
        )

        pygame.display.set_caption(
            f"{self.config.window_title} v{__version__}"
        )

        self.clock = pygame.time.Clock()

    def _create_screens(self) -> None:
        """
        Construct and register all application screens.
        """
        self.screens = {
            ScreenID.MAIN_MENU: MainMenuScreen(self),
            ScreenID.MATCH_SETUP: MatchSetupScreen(self),
            ScreenID.SETTINGS: SettingsScreen(self),
        }

        if self.config.show_test_menu:
            self.screens[
                ScreenID.TEST_MENU
            ] = TestMenuScreen(self)

    def _activate_initial_screen(self) -> None:
        """
        Activate the screen defined by the initial AppState.
        """
        initial_screen_id = self.state.current_screen

        if initial_screen_id not in self.screens:
            initial_screen_id = ScreenID.MAIN_MENU
            self.state.go_to_main_menu()

        self.active_screen = self.screens[
            initial_screen_id
        ]

        self.active_screen.on_enter()

    def _process_events(self) -> None:
        """
        Process all pending Pygame events.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.request_exit()
                continue

            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(
                    event.w,
                    event.h,
                )
                continue

            if self.active_screen is not None:
                self.active_screen.handle_event(event)

    def _handle_resize(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Resize the application window and refresh all screen layouts.
        """
        width = max(
            self.MIN_WINDOW_WIDTH,
            int(width),
        )

        height = max(
            self.MIN_WINDOW_HEIGHT,
            int(height),
        )

        self.screen = pygame.display.set_mode(
            (width, height),
            pygame.RESIZABLE,
        )

        self.config.window_width = width
        self.config.window_height = height

        for screen in self.screens.values():
            screen.screen = self.screen
            screen.refresh_layout()

