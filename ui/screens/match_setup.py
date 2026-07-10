# ui/screens/match_setup.py

from __future__ import annotations

import pygame

from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button


class MatchSetupScreen(BaseScreen):
    """
    Match setup screen.

    This initial scaffold displays placeholder panels for Player 1 and
    Player 2, plus Start Match and Back buttons. Player selectors and AI
    configuration will be added later.
    """

    def __init__(self, application) -> None:
        super().__init__(application)

        self.start_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Start Match",
            callback=self._start_match,
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
            callback=self._go_back,
        )

        self.buttons = [
            self.start_button,
            self.back_button,
        ]

        self.player_one_panel = pygame.Rect(0, 0, 0, 0)
        self.player_two_panel = pygame.Rect(0, 0, 0, 0)

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
        Draw the match setup screen.
        """
        self.draw_background(
            surface,
            THEME.background_secondary,
        )

        self.draw_title(
            surface,
            "Match Setup",
            y=75,
        )

        self.draw_subtitle(
            surface,
            "Choose who plays, then let poor strategic decisions begin.",
            y=125,
        )

        self._draw_player_panel(
            surface,
            self.player_one_panel,
            title="Player 1",
            subtitle="Player selection will be added next.",
            accent_color=THEME.player_one,
        )

        self._draw_player_panel(
            surface,
            self.player_two_panel,
            title="Player 2",
            subtitle="Human, PPO, or depth-based lookahead.",
            accent_color=THEME.player_two,
        )

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "Escape or Back returns to the previous screen.",
        )

    def refresh_layout(self) -> None:
        """
        Recalculate panel and button positions.
        """
        super().refresh_layout()

        content_width = min(
            self.width - 2 * THEME.screen_margin,
            1050,
        )

        panel_gap = THEME.section_spacing

        panel_width = (
            content_width - panel_gap
        ) // 2

        panel_height = min(
            360,
            max(260, self.height - 330),
        )

        start_x = (
            self.width - content_width
        ) // 2

        panel_y = 170

        self.player_one_panel = pygame.Rect(
            start_x,
            panel_y,
            panel_width,
            panel_height,
        )

        self.player_two_panel = pygame.Rect(
            start_x + panel_width + panel_gap,
            panel_y,
            panel_width,
            panel_height,
        )

        button_y = min(
            self.height - 125,
            self.player_one_panel.bottom + 40,
        )

        self.start_button.set_center(
            self.width // 2,
            button_y,
        )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    def _draw_player_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        title: str,
        subtitle: str,
        accent_color: tuple[int, int, int],
    ) -> None:
        """
        Draw one player configuration placeholder panel.
        """
        pygame.draw.rect(
            surface,
            THEME.panel_background,
            rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            rect,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

        accent_rect = pygame.Rect(
            rect.left,
            rect.top,
            10,
            rect.height,
        )

        pygame.draw.rect(
            surface,
            accent_color,
            accent_rect,
            border_top_left_radius=THEME.panel_radius,
            border_bottom_left_radius=THEME.panel_radius,
        )

        title_font = FONTS.get(
            THEME.font_heading,
            bold=True,
        )

        title_surface = title_font.render(
            title,
            True,
            THEME.text_primary,
        )

        title_rect = title_surface.get_rect(
            midtop=(
                rect.centerx,
                rect.top + 32,
            )
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        subtitle_font = FONTS.get(
            THEME.font_body,
        )

        subtitle_surface = subtitle_font.render(
            subtitle,
            True,
            THEME.text_secondary,
        )

        subtitle_rect = subtitle_surface.get_rect(
            midtop=(
                rect.centerx,
                title_rect.bottom + 18,
            )
        )

        surface.blit(
            subtitle_surface,
            subtitle_rect,
        )

        placeholder_font = FONTS.get(
            THEME.font_subheading,
            bold=True,
        )

        placeholder_surface = placeholder_font.render(
            "Not configured",
            True,
            THEME.text_muted,
        )

        placeholder_rect = placeholder_surface.get_rect(
            center=(
                rect.centerx,
                rect.centery + 35,
            )
        )

        surface.blit(
            placeholder_surface,
            placeholder_rect,
        )

    def _start_match(self) -> None:
        """
        Placeholder callback.

        The button remains disabled until player configuration exists.
        """
        print("Start Match requested")

    def _go_back(self) -> None:
        self.application.go_back()

