
# ui/screens/match_setup.py

from __future__ import annotations

import pygame

from players import PlayerConfig, PlayerType
from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button
from ui.widgets.selector import Selector
from ui.widgets.text_input import TextInput
from app.lookahead_config import LOOKAHEAD_CONFIG


class MatchSetupScreen(BaseScreen):
    """
    Match setup screen.

    Allows independent configuration of Player 1 and Player 2 as Human,
    Lookahead, or PPO players.
    """

    LOOKAHEAD_DEPTHS = (
        LOOKAHEAD_CONFIG.selectable_depths
    )

    def __init__(self, application) -> None:
        super().__init__(application)

        # --------------------------------------------------------
        # Player configuration
        # --------------------------------------------------------

        self.player_one_config = PlayerConfig(
            player_type=PlayerType.HUMAN,
            name="Player 1",
            lookahead_depth=(
                LOOKAHEAD_CONFIG.default_depth
            ),
        )

        self.player_two_config = PlayerConfig(
            player_type=PlayerType.LOOKAHEAD,
            name=(
                f"Lookahead "
                f"{LOOKAHEAD_CONFIG.default_depth}"
            ),
            lookahead_depth=(
                LOOKAHEAD_CONFIG.default_depth
            ),
        )

        self.player_one_human_name = "Player 1"
        self.player_two_human_name = "Player 2"

        # --------------------------------------------------------
        # Player type selectors
        # --------------------------------------------------------

        player_type_options = [
            PlayerType.HUMAN,
            PlayerType.LOOKAHEAD,
            PlayerType.PPO,
        ]

        self.player_one_type_selector = Selector(
            rect=(0, 0, 320, THEME.button_height),
            options=player_type_options,
            selected_index=player_type_options.index(
                self.player_one_config.player_type
            ),
            on_change=self._on_player_one_type_changed,
            formatter=lambda value: value.display_name,
        )

        self.player_two_type_selector = Selector(
            rect=(0, 0, 320, THEME.button_height),
            options=player_type_options,
            selected_index=player_type_options.index(
                self.player_two_config.player_type
            ),
            on_change=self._on_player_two_type_changed,
            formatter=lambda value: value.display_name,
        )

        # --------------------------------------------------------
        # Lookahead depth selectors
        # --------------------------------------------------------

        self.player_one_depth_selector = Selector(
            rect=(0, 0, 240, THEME.button_height),
            options=self.LOOKAHEAD_DEPTHS,
            selected_index=self.LOOKAHEAD_DEPTHS.index(
                self.player_one_config.lookahead_depth
            ),
            on_change=self._on_player_one_depth_changed,
            formatter=lambda depth: f"Depth {depth}",
            visible=False,
        )

        self.player_two_depth_selector = Selector(
            rect=(0, 0, 240, THEME.button_height),
            options=self.LOOKAHEAD_DEPTHS,
            selected_index=self.LOOKAHEAD_DEPTHS.index(
                self.player_two_config.lookahead_depth
            ),
            on_change=self._on_player_two_depth_changed,
            formatter=lambda depth: f"Depth {depth}",
            visible=True,
        )

        self.selectors = [
            self.player_one_type_selector,
            self.player_two_type_selector,
            self.player_one_depth_selector,
            self.player_two_depth_selector,
        ]

        # --------------------------------------------------------
        # Human name inputs
        # --------------------------------------------------------

        self.player_one_name_input = TextInput(
            rect=(0, 0, 320, THEME.button_height),
            text=self.player_one_human_name,
            placeholder="Player 1 name",
            on_change=self._on_player_one_name_changed,
            max_length=24,
            visible=True,
        )

        self.player_two_name_input = TextInput(
            rect=(0, 0, 320, THEME.button_height),
            text=self.player_two_human_name,
            placeholder="Player 2 name",
            on_change=self._on_player_two_name_changed,
            max_length=24,
            visible=False,
        )

        self.text_inputs = [
            self.player_one_name_input,
            self.player_two_name_input,
        ]

        # --------------------------------------------------------
        # Buttons
        # --------------------------------------------------------

        self.start_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Start Match",
            callback=self._start_match,
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

        self.buttons = [
            self.start_button,
            self.back_button,
        ]

        # --------------------------------------------------------
        # Layout rectangles
        # --------------------------------------------------------

        self.player_one_panel = pygame.Rect(0, 0, 0, 0)
        self.player_two_panel = pygame.Rect(0, 0, 0, 0)

        self.refresh_layout()
        self._refresh_player_controls()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Process keyboard and mouse input.
        """

        # Focused text inputs get first chance to consume keyboard input.
        for text_input in self.text_inputs:
            if text_input.handle_event(event):
                return

        super().handle_event(event)

        for button in self.buttons:
            if button.handle_event(event):
                return

        # Mouse interaction only for selectors.
        if event.type in (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
        ):
            for selector in self.selectors:
                if selector.handle_event(event):
                    return

    def update(self, delta_time: float) -> None:
        """
        Update hover states.
        """
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(mouse_position)

        for selector in self.selectors:
            selector.update(mouse_position)

        for text_input in self.text_inputs:
            text_input.update(mouse_position)

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
            y=70,
        )

        self.draw_subtitle(
            surface,
            "Choose two players and permit the strategic disagreement.",
            y=118,
        )

        self._draw_player_panel(
            surface,
            self.player_one_panel,
            title="Player 1",
            config=self.player_one_config,
            accent_color=THEME.player_one,
            type_selector=self.player_one_type_selector,
            depth_selector=self.player_one_depth_selector,
            name_input=self.player_one_name_input,
        )

        self._draw_player_panel(
            surface,
            self.player_two_panel,
            title="Player 2",
            config=self.player_two_config,
            accent_color=THEME.player_two,
            type_selector=self.player_two_type_selector,
            depth_selector=self.player_two_depth_selector,
            name_input=self.player_two_name_input,
        )

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(
            surface,
            "Human vs Human, Human vs AI, and AI vs AI are all permitted.",
        )

    def refresh_layout(self) -> None:
        """
        Recalculate player-panel and control positions.
        """
        super().refresh_layout()

        content_width = min(
            self.width - 2 * THEME.screen_margin,
            1080,
        )

        panel_gap = THEME.section_spacing

        panel_width = (
            content_width - panel_gap
        ) // 2

        panel_height = min(
            410,
            max(320, self.height - 315),
        )

        start_x = (
            self.width - content_width
        ) // 2

        panel_y = 150

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

        self._layout_panel_controls(
            self.player_one_panel,
            self.player_one_type_selector,
            self.player_one_depth_selector,
            self.player_one_name_input,
        )

        self._layout_panel_controls(
            self.player_two_panel,
            self.player_two_type_selector,
            self.player_two_depth_selector,
            self.player_two_name_input,
        )

        button_y = min(
            self.height - 105,
            self.player_one_panel.bottom + 36,
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

    def _layout_panel_controls(
        self,
        panel_rect: pygame.Rect,
        type_selector: Selector[PlayerType],
        depth_selector: Selector[int],
        name_input: TextInput,
    ) -> None:
        """
        Position controls inside one player panel.
        """
        control_width = min(
            340,
            panel_rect.width - 2 * THEME.panel_padding,
        )

        type_selector.set_size(
            control_width,
            THEME.button_height,
        )

        type_selector.set_center(
            panel_rect.centerx,
            panel_rect.top + 145,
        )

        depth_selector.set_size(
            min(240, control_width),
            THEME.button_height,
        )

        depth_selector.set_center(
            panel_rect.centerx,
            panel_rect.top + 245,
        )

        name_input.set_size(
            control_width,
            THEME.button_height,
        )

        name_input.set_center(
            panel_rect.centerx,
            panel_rect.top + 245,
        )

    def _draw_player_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        title: str,
        config: PlayerConfig,
        accent_color: tuple[int, int, int],
        type_selector: Selector[PlayerType],
        depth_selector: Selector[int],
        name_input: TextInput,
    ) -> None:
        """
        Draw one player configuration panel.
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
                rect.top + 24,
            )
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        label_font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        type_label_surface = label_font.render(
            "PLAYER TYPE",
            True,
            THEME.text_secondary,
        )

        type_label_rect = type_label_surface.get_rect(
            center=(
                rect.centerx,
                rect.top + 98,
            )
        )

        surface.blit(
            type_label_surface,
            type_label_rect,
        )

        type_selector.draw(surface)

        if config.player_type is PlayerType.LOOKAHEAD:
            depth_label_surface = label_font.render(
                "SEARCH DEPTH",
                True,
                THEME.text_secondary,
            )

            depth_label_rect = depth_label_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.top + 198,
                )
            )

            surface.blit(
                depth_label_surface,
                depth_label_rect,
            )

            depth_selector.draw(surface)

            self._draw_player_summary(
                surface,
                rect,
                f"Depth-based Numba lookahead: {config.lookahead_depth}",
            )

        elif config.player_type is PlayerType.PPO:
            self._draw_player_summary(
                surface,
                rect,
                f"Model: {config.model_name}",
            )

        else:
            name_label_surface = label_font.render(
                "PLAYER NAME",
                True,
                THEME.text_secondary,
            )

            name_label_rect = name_label_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.top + 198,
                )
            )

            surface.blit(
                name_label_surface,
                name_label_rect,
            )

            name_input.draw(surface)

            self._draw_player_summary(
                surface,
                rect,
                f"Playing as: {config.name}",
            )

    def _draw_player_summary(
        self,
        surface: pygame.Surface,
        panel_rect: pygame.Rect,
        text: str,
    ) -> None:
        """
        Draw a short description near the bottom of a player panel.
        """
        font = FONTS.get(
            THEME.font_small,
        )

        text_surface = font.render(
            text,
            True,
            THEME.text_muted,
        )

        text_rect = text_surface.get_rect(
            center=(
                panel_rect.centerx,
                panel_rect.bottom - 42,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _refresh_player_controls(self) -> None:
        """
        Update conditional controls and generated player names.
        """
        player_one_is_human = (
            self.player_one_config.player_type
            is PlayerType.HUMAN
        )

        player_two_is_human = (
            self.player_two_config.player_type
            is PlayerType.HUMAN
        )

        self.player_one_depth_selector.set_visible(
            self.player_one_config.player_type
            is PlayerType.LOOKAHEAD
        )

        self.player_two_depth_selector.set_visible(
            self.player_two_config.player_type
            is PlayerType.LOOKAHEAD
        )

        self.player_one_name_input.set_visible(
            player_one_is_human
        )

        self.player_two_name_input.set_visible(
            player_two_is_human
        )

        if player_one_is_human:
            self.player_one_config.name = (
                self.player_one_human_name
            )
        else:
            self.player_one_config.name = (
                self._make_player_name(
                    config=self.player_one_config,
                )
            )

        if player_two_is_human:
            self.player_two_config.name = (
                self.player_two_human_name
            )
        else:
            self.player_two_config.name = (
                self._make_player_name(
                    config=self.player_two_config,
                )
            )

        self.player_one_config.validate()
        self.player_two_config.validate()

    @staticmethod
    def _make_player_name(
        *,
        config: PlayerConfig,
    ) -> str:
        """
        Generate a useful default AI player name.
        """
        if config.player_type is PlayerType.LOOKAHEAD:
            return f"Lookahead {config.lookahead_depth}"

        if config.player_type is PlayerType.PPO:
            return "PPO 2004"

        return "Human"

    def _on_player_one_type_changed(
        self,
        player_type: PlayerType,
    ) -> None:
        self.player_one_config.player_type = player_type

        if player_type is PlayerType.HUMAN:
            self.player_one_name_input.set_text(
                self.player_one_human_name,
                notify=False,
            )

        self._refresh_player_controls()

    def _on_player_two_type_changed(
        self,
        player_type: PlayerType,
    ) -> None:
        self.player_two_config.player_type = player_type

        if player_type is PlayerType.HUMAN:
            self.player_two_name_input.set_text(
                self.player_two_human_name,
                notify=False,
            )

        self._refresh_player_controls()

    def _on_player_one_depth_changed(
        self,
        depth: int,
    ) -> None:
        self.player_one_config.lookahead_depth = int(depth)
        self._refresh_player_controls()

    def _on_player_two_depth_changed(
        self,
        depth: int,
    ) -> None:
        self.player_two_config.lookahead_depth = int(depth)
        self._refresh_player_controls()

    def _on_player_one_name_changed(
        self,
        name: str,
    ) -> None:
        cleaned = name.strip()

        self.player_one_human_name = (
            cleaned or "Player 1"
        )

        self.player_one_config.name = (
            self.player_one_human_name
        )

    def _on_player_two_name_changed(
        self,
        name: str,
    ) -> None:
        cleaned = name.strip()

        self.player_two_human_name = (
            cleaned or "Player 2"
        )

        self.player_two_config.name = (
            self.player_two_human_name
        )


    def _start_match(self) -> None:
        """
        Validate the selected configurations and open the game screen.
        """
        self.player_one_config.validate()
        self.player_two_config.validate()
    
        self.application.start_match(
            self.player_one_config,
            self.player_two_config,
            starting_player=1,
        )



