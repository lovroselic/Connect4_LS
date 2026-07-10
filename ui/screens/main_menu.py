# ui/screens/main_menu.py

from __future__ import annotations

import pygame

from app.state import ScreenID
from ui.screens.base_screen import BaseScreen
from ui.theme import THEME
from ui.widgets.button import Button


class MainMenuScreen(BaseScreen):
    """
    Main application menu.

    The menu provides navigation to match setup, settings, development tests,
    and application shutdown.
    """

    def __init__(self, application) -> None:
        super().__init__(application)

        self.play_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Play",
            callback=self._open_match_setup,
        )

        self.settings_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Settings",
            callback=self._open_settings,
        )

        self.tests_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Tests",
            callback=self._open_test_menu,
            visible=self.config.show_test_menu,
        )

        self.quit_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Quit",
            callback=self.application.request_exit,
        )

        self.buttons = [
            self.play_button,
            self.settings_button,
            self.tests_button,
            self.quit_button,
        ]

        self.refresh_layout()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Process keyboard and mouse input.
        """
        super().handle_event(event)

        for button in self.buttons:
            if button.handle_event(event):
                break

    def update(self, delta_time: float) -> None:
        """
        Update button hover states.
        """
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(mouse_position)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the main menu.
        """
        self.draw_background(surface)

        self.draw_title(
            surface,
            self.config.window_title,
            y=115,
        )

        self.draw_subtitle(
            surface,
            "Human minds, neural networks, and brute force enter one board.",
            y=175,
        )

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "Standard 6 × 7 Connect Four",
        )

    def refresh_layout(self) -> None:
        """
        Reposition buttons for the current window dimensions.
        """
        super().refresh_layout()

        visible_buttons = [
            button
            for button in self.buttons
            if button.visible
        ]

        if not visible_buttons:
            return

        total_height = (
            len(visible_buttons) * THEME.button_height
            + (len(visible_buttons) - 1) * THEME.widget_spacing
        )

        start_y = max(
            235,
            (self.height - total_height) // 2,
        )

        center_x = self.width // 2

        for index, button in enumerate(visible_buttons):
            button.set_center(
                center_x,
                start_y
                + index * (
                    THEME.button_height
                    + THEME.widget_spacing
                )
                + THEME.button_height // 2,
            )

    def handle_escape(self) -> None:
        """
        Escape from the main menu exits the application.
        """
        self.application.request_exit()

    def _open_match_setup(self) -> None:
        self.application.change_screen(ScreenID.MATCH_SETUP)

    def _open_settings(self) -> None:
        self.application.change_screen(ScreenID.SETTINGS)

    def _open_test_menu(self) -> None:
        if self.config.show_test_menu:
            self.application.change_screen(ScreenID.TEST_MENU)

