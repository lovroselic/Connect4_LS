# ui/screens/settings_screen.py

from __future__ import annotations

import pygame

from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button


class SettingsScreen(BaseScreen):
    """
    Application settings screen.

    This initial scaffold displays the currently loaded configuration.
    Interactive controls will be added later.
    """

    def __init__(self, application) -> None:
        super().__init__(application)

        self.back_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Back",
            callback=self.application.go_back,
        )

        self.buttons = [
            self.back_button,
        ]

        self.settings_panel = pygame.Rect(0, 0, 0, 0)

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
        Update button hover state.
        """
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(mouse_position)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the settings screen.
        """
        self.draw_background(
            surface,
            THEME.background_secondary,
        )

        self.draw_title(
            surface,
            "Settings",
            y=75,
        )

        self.draw_subtitle(
            surface,
            "Current application configuration",
            y=125,
        )

        self._draw_settings_panel(surface)

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "Interactive settings will be added later.",
        )

    def refresh_layout(self) -> None:
        """
        Recalculate panel and button positions.
        """
        super().refresh_layout()

        panel_width = min(
            700,
            self.width - 2 * THEME.screen_margin,
        )

        panel_height = min(
            430,
            self.height - 260,
        )

        self.settings_panel = pygame.Rect(
            (self.width - panel_width) // 2,
            170,
            panel_width,
            panel_height,
        )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    def _draw_settings_panel(
        self,
        surface: pygame.Surface,
    ) -> None:
        """
        Draw the settings summary panel.
        """
        pygame.draw.rect(
            surface,
            THEME.panel_background,
            self.settings_panel,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            self.settings_panel,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

        rows = [
            (
                "Resolution",
                f"{self.config.window_width} × "
                f"{self.config.window_height}",
            ),
            (
                "Fullscreen",
                self._format_bool(
                    self.config.fullscreen
                ),
            ),
            (
                "Target FPS",
                str(self.config.target_fps),
            ),
            (
                "Analysis panel",
                self._format_bool(
                    self.config.show_analysis_panel
                ),
            ),
            (
                "Test menu",
                self._format_bool(
                    self.config.show_test_menu
                ),
            ),
            (
                "Animation speed",
                f"{self.config.animation_speed:.2f}",
            ),
            (
                "AI move delay",
                f"{self.config.ai_move_delay_ms} ms",
            ),
        ]

        label_font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        value_font = FONTS.get(
            THEME.font_body,
        )

        row_height = 46

        start_y = (
            self.settings_panel.top
            + THEME.panel_padding
        )

        label_x = (
            self.settings_panel.left
            + THEME.panel_padding
        )

        value_x = (
            self.settings_panel.right
            - THEME.panel_padding
        )

        for index, (label, value) in enumerate(rows):
            y = start_y + index * row_height

            if index > 0:
                separator_y = y - 10

                pygame.draw.line(
                    surface,
                    THEME.panel_border,
                    (
                        self.settings_panel.left
                        + THEME.panel_padding,
                        separator_y,
                    ),
                    (
                        self.settings_panel.right
                        - THEME.panel_padding,
                        separator_y,
                    ),
                    width=1,
                )

            label_surface = label_font.render(
                label,
                True,
                THEME.text_primary,
            )

            label_rect = label_surface.get_rect(
                midleft=(label_x, y),
            )

            surface.blit(
                label_surface,
                label_rect,
            )

            value_surface = value_font.render(
                value,
                True,
                THEME.text_secondary,
            )

            value_rect = value_surface.get_rect(
                midright=(value_x, y),
            )

            surface.blit(
                value_surface,
                value_rect,
            )

    @staticmethod
    def _format_bool(value: bool) -> str:
        """
        Return a user-facing representation of a boolean value.
        """
        return "Enabled" if value else "Disabled"

