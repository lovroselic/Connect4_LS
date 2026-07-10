# ui/screens/test_menu.py

from __future__ import annotations

import pygame

from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button


class TestMenuScreen(BaseScreen):
    """
    Development and diagnostic tools menu.

    This screen is shown only when config.show_test_menu is enabled.
    The test actions are placeholders for now and will later launch
    headless matches, benchmarks, depth tests, and PPO validation.
    """

    def __init__(self, application) -> None:
        super().__init__(application)

        self.headless_match_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Headless Match",
            callback=self._run_headless_match,
            enabled=False,
        )

        self.agent_benchmark_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Agent Benchmark",
            callback=self._run_agent_benchmark,
            enabled=False,
        )

        self.depth_test_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="Lookahead Depth Test",
            callback=self._run_depth_test,
            enabled=False,
        )

        self.ppo_validation_button = Button(
            rect=(0, 0, THEME.button_width, THEME.button_height),
            text="PPO Validation",
            callback=self._run_ppo_validation,
            enabled=False,
        )

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

        self.test_buttons = [
            self.headless_match_button,
            self.agent_benchmark_button,
            self.depth_test_button,
            self.ppo_validation_button,
        ]

        self.buttons = [
            *self.test_buttons,
            self.back_button,
        ]

        self.info_panel = pygame.Rect(0, 0, 0, 0)

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
        Draw the test menu.
        """
        self.draw_background(
            surface,
            THEME.background_secondary,
        )

        self.draw_title(
            surface,
            "Tests",
            y=75,
        )

        self.draw_subtitle(
            surface,
            "Development tools, benchmarks, and controlled AI violence.",
            y=125,
        )

        self._draw_info_panel(surface)

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "This menu can be hidden in release builds through configuration.",
        )

    def refresh_layout(self) -> None:
        """
        Recalculate panel and button positions.
        """
        super().refresh_layout()

        panel_width = min(
            440,
            self.width - 2 * THEME.screen_margin,
        )

        panel_height = 390

        self.info_panel = pygame.Rect(
            (self.width - panel_width) // 2,
            165,
            panel_width,
            panel_height,
        )

        start_y = self.info_panel.top + 105
        spacing = THEME.widget_spacing

        for index, button in enumerate(self.test_buttons):
            button.set_center(
                self.width // 2,
                start_y
                + index * (
                    THEME.button_height
                    + spacing
                ),
            )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    def _draw_info_panel(
        self,
        surface: pygame.Surface,
    ) -> None:
        """
        Draw the development-tools panel.
        """
        pygame.draw.rect(
            surface,
            THEME.panel_background,
            self.info_panel,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            self.info_panel,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

        heading_font = FONTS.get(
            THEME.font_subheading,
            bold=True,
        )

        heading_surface = heading_font.render(
            "Available test modules",
            True,
            THEME.text_primary,
        )

        heading_rect = heading_surface.get_rect(
            midtop=(
                self.info_panel.centerx,
                self.info_panel.top + 28,
            )
        )

        surface.blit(
            heading_surface,
            heading_rect,
        )

        note_font = FONTS.get(
            THEME.font_small,
        )

        note_surface = note_font.render(
            "Test actions will be enabled as their systems are implemented.",
            True,
            THEME.text_secondary,
        )

        note_rect = note_surface.get_rect(
            midbottom=(
                self.info_panel.centerx,
                self.info_panel.bottom - 22,
            )
        )

        surface.blit(
            note_surface,
            note_rect,
        )

    def _run_headless_match(self) -> None:
        print("Headless Match requested")

    def _run_agent_benchmark(self) -> None:
        print("Agent Benchmark requested")

    def _run_depth_test(self) -> None:
        print("Lookahead Depth Test requested")

    def _run_ppo_validation(self) -> None:
        print("PPO Validation requested")

