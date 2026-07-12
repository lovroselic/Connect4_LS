# app/application.py

from __future__ import annotations

import pygame

from app import __version__
from app.config import AppConfig
from app.state import AppState, ScreenID
from game.match import Connect4Match, StartingPlayerMode
from infrastructure import TaskManager
from players import PlayerConfig, PlayerFactory
from ui.screens.game_screen import GameScreen
from ui.screens.main_menu import MainMenuScreen
from ui.screens.match_setup import MatchSetupScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.test_menu import TestMenuScreen
from ui.theme import FONTS


class Application:
    """
    Main Connect4_LS application.

    Owns the Pygame window, screens, navigation, player factory,
    event loop, configuration, and application shutdown.
    """

    MINIMUM_WIDTH = 800
    MINIMUM_HEIGHT = 600

    def __init__(self) -> None:
        self.config = AppConfig.load()
        self.config.validate()

        self.state = AppState()

        pygame.init()

        self.task_manager = TaskManager(
            maximum_workers=1,
        )

        self.screen = self._create_display(
            self.config.window_width,
            self.config.window_height,
        )

        pygame.display.set_caption(
            f"{self.config.window_title} v{__version__}"
        )

        self.clock = pygame.time.Clock()
        self.player_factory = PlayerFactory()

        self.screens = {
            ScreenID.MAIN_MENU: MainMenuScreen(self),
            ScreenID.MATCH_SETUP: MatchSetupScreen(self),
            ScreenID.GAME: GameScreen(self),
            ScreenID.SETTINGS: SettingsScreen(self),
        }

        if self.config.show_test_menu:
            self.screens[ScreenID.TEST_MENU] = (
                TestMenuScreen(self)
            )

        self.active_screen = self.screens[
            self.state.current_screen
        ]

        self.active_screen.on_enter()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Run the application until exit is requested.
        """
        try:
            while self.state.running:
                delta_time = (
                    self.clock.tick(
                        self.config.target_fps
                    )
                    / 1000.0
                )

                self._process_events()

                if not self.state.running:
                    break

                self.active_screen.update(
                    delta_time
                )

                self.active_screen.draw(
                    self.screen
                )

                pygame.display.flip()

        finally:
            self.shutdown()

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.request_exit()
                return

            if (
                event.type == pygame.VIDEORESIZE
                and not self.config.fullscreen
            ):
                self._handle_resize(
                    event.w,
                    event.h,
                )
                continue

            self.active_screen.handle_event(
                event
            )

    # ------------------------------------------------------------------
    # Match creation
    # ------------------------------------------------------------------

    def start_match(
        self,
        player_one_config: PlayerConfig,
        player_two_config: PlayerConfig,
        *,
        starting_player: int = 1,
        starting_mode: StartingPlayerMode | None = None,
    ) -> None:
        """
        Construct and open a new Connect Four match.
        """
        player_one, player_two = (
            self.player_factory.create_pair(
                player_one_config,
                player_two_config,
            )
        )
    
        match = Connect4Match(
            player_one,
            player_two,
            starting_player=starting_player,
            starting_mode=starting_mode,
        )
    
        game_screen = self.screens[
            ScreenID.GAME
        ]
    
        if not isinstance(
            game_screen,
            GameScreen,
        ):
            raise RuntimeError(
                "Registered GAME screen is not a GameScreen."
            )
    
        game_screen.set_match(
            match,
            start_immediately=True,
        )
    
        self.change_screen(
            ScreenID.GAME
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def change_screen(
        self,
        screen_id: ScreenID,
        *,
        remember_current: bool = True,
    ) -> None:
        """
        Change the visible application screen.
        """
        if screen_id not in self.screens:
            raise ValueError(
                f"Screen is not registered: {screen_id}"
            )

        if screen_id is self.state.current_screen:
            return

        self.active_screen.on_exit()

        self.state.change_screen(
            screen_id,
            remember_current=remember_current,
        )

        self.active_screen = self.screens[
            self.state.current_screen
        ]

        self.active_screen.on_enter()

    def go_back(self) -> None:
        """
        Return to the previous screen.
        """
        self.active_screen.on_exit()

        changed = self.state.go_back()

        if not changed:
            self.state.go_to_main_menu()

        self.active_screen = self.screens[
            self.state.current_screen
        ]

        self.active_screen.on_enter()

    def go_to_main_menu(self) -> None:
        """
        Return directly to the main menu.
        """
        if (
            self.state.current_screen
            is ScreenID.MAIN_MENU
        ):
            return

        self.active_screen.on_exit()

        self.state.go_to_main_menu()

        self.active_screen = self.screens[
            ScreenID.MAIN_MENU
        ]

        self.active_screen.on_enter()

    def request_exit(self) -> None:
        self.state.request_exit()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def apply_config(
        self,
        new_config: AppConfig,
        *,
        save: bool = True,
    ) -> None:
        """
        Apply a validated configuration to the running application.

        Display size, fullscreen state, target FPS, analysis visibility,
        animation speed, and AI delay take effect immediately.

        Test Menu visibility is persisted but takes effect on the next launch,
        because the menu and its worker task are registered during startup.
        """
        new_config.validate()

        display_changed = (
            new_config.window_width
            != self.config.window_width
            or new_config.window_height
            != self.config.window_height
            or new_config.fullscreen
            != self.config.fullscreen
        )

        self.config.show_test_menu = (
            new_config.show_test_menu
        )

        self.config.show_analysis_panel = (
            new_config.show_analysis_panel
        )

        self.config.window_width = (
            new_config.window_width
        )

        self.config.window_height = (
            new_config.window_height
        )

        self.config.fullscreen = (
            new_config.fullscreen
        )

        self.config.target_fps = (
            new_config.target_fps
        )

        self.config.animation_speed = (
            new_config.animation_speed
        )

        self.config.ai_move_delay_ms = (
            new_config.ai_move_delay_ms
        )

        self.config.window_title = (
            new_config.window_title
        )

        self.config.validate()

        if display_changed:
            self._recreate_display()

        pygame.display.set_caption(
            f"{self.config.window_title} v{__version__}"
        )

        if save:
            self.config.save()

    def restore_default_config(
        self,
    ) -> AppConfig:
        """
        Return a new configuration containing application defaults.
        """
        return AppConfig()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_flags(self) -> int:
        if self.config.fullscreen:
            return pygame.FULLSCREEN

        return pygame.RESIZABLE

    def _create_display(
        self,
        width: int,
        height: int,
    ) -> pygame.Surface:
        width = max(
            self.MINIMUM_WIDTH,
            int(width),
        )

        height = max(
            self.MINIMUM_HEIGHT,
            int(height),
        )

        return pygame.display.set_mode(
            (
                width,
                height,
            ),
            self._display_flags(),
        )

    def _recreate_display(self) -> None:
        """
        Recreate the Pygame display from the current configuration.
        """
        self.screen = self._create_display(
            self.config.window_width,
            self.config.window_height,
        )

        actual_width, actual_height = (
            self.screen.get_size()
        )

        if not self.config.fullscreen:
            self.config.window_width = (
                actual_width
            )

            self.config.window_height = (
                actual_height
            )

        self._refresh_all_screen_layouts()

    def _handle_resize(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Resize the window and refresh every screen layout.
        """
        if self.config.fullscreen:
            return

        width = max(
            self.MINIMUM_WIDTH,
            int(width),
        )

        height = max(
            self.MINIMUM_HEIGHT,
            int(height),
        )

        self.screen = pygame.display.set_mode(
            (
                width,
                height,
            ),
            pygame.RESIZABLE,
        )

        self.config.window_width = width
        self.config.window_height = height

        self._refresh_all_screen_layouts()

    def _refresh_all_screen_layouts(
        self,
    ) -> None:
        for application_screen in (
            self.screens.values()
        ):
            application_screen.screen = (
                self.screen
            )

            application_screen.refresh_layout()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """
        Save configuration and release application resources.
        """
        try:
            self.config.save()
        except Exception as error:
            print(
                "[Config] Could not save settings "
                f"during shutdown: {error}"
            )

        try:
            self.active_screen.on_exit()
        except Exception:
            pass

        try:
            self.task_manager.shutdown(
                wait=True,
            )
        except Exception:
            pass

        FONTS.clear()
        pygame.quit()