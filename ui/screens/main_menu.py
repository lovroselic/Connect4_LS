# ui/screens/main_menu.py

from __future__ import annotations

import pygame

from app.paths import ASSETS_DIR
from app.state import ScreenID
from ui.screens.base_screen import BaseScreen
from ui.theme import THEME
from ui.widgets.button import Button


class MainMenuScreen(BaseScreen):
    """
    Main application menu.

    The title illustration is loaded from assets/images/connect4_title.png.
    It is scaled proportionally for the current window size and the menu
    buttons are placed in a separate column on the right.
    """

    TITLE_IMAGE_PATH = (
        ASSETS_DIR
        / "images"
        / "connect4_title.webp"
    )

    def __init__(self, application) -> None:
        super().__init__(application)

        self.play_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Play",
            callback=self._open_match_setup,
        )

        self.settings_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Settings",
            callback=self._open_settings,
        )

        self.about_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="About",
            callback=self._open_about,
        )

        self.tests_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Tests",
            callback=self._open_test_menu,
            visible=self.config.show_test_menu,
        )

        self.quit_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Quit",
            callback=self.application.request_exit,
        )

        self.buttons = [
            self.play_button,
            self.settings_button,
            self.about_button,
            self.tests_button,
            self.quit_button,
        ]

        self.title_image_original: (
            pygame.Surface | None
        ) = None

        self.title_image_scaled: (
            pygame.Surface | None
        ) = None

        self.title_image_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self._load_title_image()
        self.refresh_layout()

    # ------------------------------------------------------------------
    # Asset loading
    # ------------------------------------------------------------------

    def _load_title_image(self) -> None:
        """
        Load the transparent title illustration.

        A missing or unreadable image does not prevent the menu from working.
        """
        try:
            image = pygame.image.load(
                str(self.TITLE_IMAGE_PATH)
            )

            self.title_image_original = (
                image.convert_alpha()
            )

        except (
            FileNotFoundError,
            pygame.error,
            OSError,
        ) as error:
            self.title_image_original = None
            self.title_image_scaled = None

            print(
                "[MainMenu] Could not load title image "
                f"{self.TITLE_IMAGE_PATH}: {error}"
            )

    # ------------------------------------------------------------------
    # Input and update
    # ------------------------------------------------------------------

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        """
        Process keyboard and mouse input.
        """
        super().handle_event(event)

        for button in self.buttons:
            if button.handle_event(event):
                break

    def update(
        self,
        delta_time: float,
    ) -> None:
        """
        Update button hover states.
        """
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(
                mouse_position
            )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        """
        Draw the main menu.
        """
        self.draw_background(surface)

        self.draw_title(
            surface,
            self.config.window_title,
            y=76,
        )

        self.draw_subtitle(
            surface,
            (
                "Human minds, neural networks, and brute force "
                "enter one board."
            ),
            y=126,
        )

        if self.title_image_scaled is not None:
            surface.blit(
                self.title_image_scaled,
                self.title_image_rect,
            )

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "(C) 2026 Lovro Selič, LaughingSkull",
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def refresh_layout(self) -> None:
        """
        Reposition and rescale all main-menu elements.
        """
        super().refresh_layout()

        visible_buttons = [
            button
            for button in self.buttons
            if button.visible
        ]

        content_top = 160
        content_bottom = (
            self.height
            - THEME.screen_margin
            - 38
        )

        content_height = max(
            220,
            content_bottom - content_top,
        )

        menu_center_x = int(
            self.width * 0.72
        )

        graphic_center_x = int(
            self.width * 0.31
        )

        if self.width <= 900:
            menu_center_x = int(
                self.width * 0.72
            )

            graphic_center_x = int(
                self.width * 0.28
            )

        if visible_buttons:
            total_height = (
                len(visible_buttons)
                * THEME.button_height
                + (
                    len(visible_buttons) - 1
                )
                * THEME.widget_spacing
            )

            start_y = (
                content_top
                + max(
                    0,
                    (
                        content_height
                        - total_height
                    )
                    // 2,
                )
            )

            for index, button in enumerate(
                visible_buttons
            ):
                button.set_center(
                    menu_center_x,
                    start_y
                    + index
                    * (
                        THEME.button_height
                        + THEME.widget_spacing
                    )
                    + THEME.button_height
                    // 2,
                )

        self._scale_title_image(
            graphic_center_x=graphic_center_x,
            content_top=content_top,
            content_height=content_height,
        )

    def _scale_title_image(
        self,
        *,
        graphic_center_x: int,
        content_top: int,
        content_height: int,
    ) -> None:
        """
        Scale the source image proportionally into the left-side region.
        """
        image = self.title_image_original

        if image is None:
            self.title_image_scaled = None
            self.title_image_rect = pygame.Rect(
                0,
                0,
                0,
                0,
            )
            return

        left_region_width = max(
            180,
            int(self.width * 0.48),
        )

        maximum_width = min(
            440,
            left_region_width
            - 2 * THEME.screen_margin,
        )

        maximum_height = min(
            440,
            content_height - 16,
        )

        maximum_width = max(
            120,
            maximum_width,
        )

        maximum_height = max(
            120,
            maximum_height,
        )

        source_width = image.get_width()
        source_height = image.get_height()

        scale = min(
            maximum_width / source_width,
            maximum_height / source_height,
        )

        scaled_width = max(
            1,
            round(source_width * scale),
        )

        scaled_height = max(
            1,
            round(source_height * scale),
        )

        self.title_image_scaled = (
            pygame.transform.smoothscale(
                image,
                (
                    scaled_width,
                    scaled_height,
                ),
            )
        )

        self.title_image_rect = (
            self.title_image_scaled.get_rect(
                center=(
                    graphic_center_x,
                    content_top
                    + content_height // 2,
                )
            )
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def handle_escape(self) -> None:
        """
        Escape from the main menu exits the application.
        """
        self.application.request_exit()

    def _open_match_setup(self) -> None:
        self.application.change_screen(
            ScreenID.MATCH_SETUP
        )

    def _open_settings(self) -> None:
        self.application.change_screen(
            ScreenID.SETTINGS
        )

    def _open_about(self) -> None:
        self.application.change_screen(
            ScreenID.ABOUT
        )

    def _open_test_menu(self) -> None:
        if self.config.show_test_menu:
            self.application.change_screen(
                ScreenID.TEST_MENU
            )
