
# ui/screens/game_screen.py

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.match import (
    Connect4Match,
    MatchStatus,
    TurnResult,
)
from players.base import MoveResult
from rendering import BoardRenderer
from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button


@dataclass(frozen=True, slots=True)
class AIWorkerResult:
    """
    Result calculated by an AI worker thread.
    """

    match_identity: int
    generation: int
    player_id: int
    expected_move_count: int
    move_result: MoveResult | None


class GameScreen(BaseScreen):
    """
    Graphical screen for one Connect Four match.

    AI move selection runs on the application's worker thread. The worker
    receives a board copy and never modifies the live match.
    """

    def __init__(self, application) -> None:
        super().__init__(application)

        self.match: Connect4Match | None = None

        self.board_renderer = BoardRenderer()

        self.ai_task = (
            self.application
            .task_manager
            .create_task()
        )

        self.back_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Main Menu",
            callback=self._return_to_main_menu,
        )

        self.restart_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Restart",
            callback=self._restart_match,
        )

        self.buttons = [
            self.back_button,
            self.restart_button,
        ]

        self.left_panel_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.right_panel_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.board_area = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self._ai_delay_elapsed_ms = 0.0
        self._last_move: TurnResult | None = None
        self._error_message = ""

        self._generation = 0
        self._ai_result_consumed = True

        self.refresh_layout()

    # ------------------------------------------------------------------
    # Match setup
    # ------------------------------------------------------------------

    def set_match(
        self,
        match: Connect4Match,
        *,
        start_immediately: bool = True,
    ) -> None:
        """
        Assign the match displayed by this screen.
        """
        self._invalidate_ai_result()

        if (
            self.match is not None
            and self.match.is_running
        ):
            self.match.abort(
                "Match replaced by a new match."
            )

        self.match = match
        self._last_move = None
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

        if start_immediately:
            self.match.start()

    def on_enter(self) -> None:
        super().on_enter()

        self._ai_delay_elapsed_ms = 0.0
        self._error_message = ""

        self._discard_stale_completed_task()

        if (
            self.match is not None
            and self.match.status
            is MatchStatus.NOT_STARTED
        ):
            self.match.start()

    def on_exit(self) -> None:
        self.board_renderer.hovered_column = None
        self._invalidate_ai_result()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._return_to_main_menu()
                return

            if event.key == pygame.K_r:
                self._restart_match()
                return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self._handle_board_click(
                event.pos
            )

    def _handle_board_click(
        self,
        position: tuple[int, int],
    ) -> None:
        if self.match is None:
            return

        if not self.match.is_running:
            return

        if self.ai_task.is_running:
            return

        if not self.match.current_player.is_human:
            return

        column = (
            self.board_renderer
            .column_at(position)
        )

        if column is None:
            return

        accepted = self.match.submit_move(
            column
        )

        if not accepted:
            self._error_message = (
                f"Column {column + 1} "
                "cannot be played."
            )
            return

        self._error_message = ""

        turn = self.match.update()

        if turn is not None:
            self._on_turn_completed(
                turn
            )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        delta_time: float,
    ) -> None:
        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(
                mouse_position
            )

        self._consume_ai_task_if_ready()

        if self.match is None:
            self.board_renderer.hovered_column = None
            return

        interactive = (
            self.match.is_running
            and self.match.current_player.is_human
            and not self.ai_task.is_running
        )

        self.board_renderer.update_hover(
            mouse_position,
            self.match.board,
            interactive=interactive,
        )

        if not self.match.is_running:
            return

        if self.match.current_player.is_human:
            self._ai_delay_elapsed_ms = 0.0
            return

        if self.ai_task.is_running:
            return

        if (
            self.ai_task.is_done
            and not self._ai_result_consumed
        ):
            return

        self._ai_delay_elapsed_ms += (
            delta_time * 1000.0
        )

        delay_ms = max(
            0,
            int(
                self.config.ai_move_delay_ms
            ),
        )

        if (
            self._ai_delay_elapsed_ms
            < delay_ms
        ):
            return

        self._ai_delay_elapsed_ms = 0.0
        self._start_ai_task()

    # ------------------------------------------------------------------
    # AI worker
    # ------------------------------------------------------------------

    def _start_ai_task(self) -> None:
        if self.match is None:
            return

        if not self.match.is_running:
            return

        if self.match.current_player.is_human:
            return

        if self.ai_task.is_running:
            return

        if self.ai_task.is_done:
            self.ai_task.clear()

        match = self.match
        player = match.current_player
        board_copy = match.board.copy()

        match_identity = id(match)
        generation = self._generation
        player_id = player.player_id
        expected_move_count = (
            match.board.move_count
        )

        def calculate_move() -> AIWorkerResult:
            move_result = player.choose_move(
                board_copy
            )

            return AIWorkerResult(
                match_identity=match_identity,
                generation=generation,
                player_id=player_id,
                expected_move_count=(
                    expected_move_count
                ),
                move_result=move_result,
            )

        self._ai_result_consumed = False

        started = self.ai_task.start(
            calculate_move
        )

        if not started:
            self._ai_result_consumed = True
            self._error_message = (
                "Could not start AI calculation."
            )

    def _consume_ai_task_if_ready(
        self,
    ) -> None:
        if not self.ai_task.is_done:
            return

        if self._ai_result_consumed:
            return

        self._ai_result_consumed = True

        exception = self.ai_task.exception()

        if exception is not None:
            self._error_message = (
                "AI move failed: "
                f"{type(exception).__name__}: "
                f"{exception}"
            )

            if (
                self.match is not None
                and self.match.is_running
            ):
                self.match.abort(
                    self._error_message
                )

            self.ai_task.clear()
            return

        try:
            worker_result = (
                self.ai_task.result()
            )

        except Exception as error:
            self._error_message = (
                "AI move failed: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            if (
                self.match is not None
                and self.match.is_running
            ):
                self.match.abort(
                    self._error_message
                )

            self.ai_task.clear()
            return

        self.ai_task.clear()

        if worker_result is None:
            return

        if self.match is None:
            return

        if (
            worker_result.match_identity
            != id(self.match)
        ):
            return

        if (
            worker_result.generation
            != self._generation
        ):
            return

        if worker_result.move_result is None:
            self._error_message = (
                "AI returned no move."
            )

            if self.match.is_running:
                self.match.abort(
                    self._error_message
                )

            return

        try:
            turn = (
                self.match
                .commit_move_result(
                    player_id=(
                        worker_result.player_id
                    ),
                    expected_move_count=(
                        worker_result
                        .expected_move_count
                    ),
                    move_result=(
                        worker_result.move_result
                    ),
                )
            )

        except Exception as error:
            self._error_message = (
                "AI move failed: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            if self.match.is_running:
                self.match.abort(
                    self._error_message
                )

            return

        if turn is not None:
            self._on_turn_completed(
                turn
            )

    def _discard_stale_completed_task(
        self,
    ) -> None:
        if self.ai_task.is_done:
            self._ai_result_consumed = True
            self.ai_task.clear()

    def _invalidate_ai_result(self) -> None:
        self._generation += 1
        self._ai_delay_elapsed_ms = 0.0

        if self.ai_task.is_done:
            self._ai_result_consumed = True
            self.ai_task.clear()

    def _on_turn_completed(
        self,
        turn: TurnResult,
    ) -> None:
        self._last_move = turn
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        self.draw_background(
            surface,
            THEME.background_secondary,
        )

        self.draw_title(
            surface,
            "Connect Four",
            y=42,
        )

        if self.match is None:
            self._draw_missing_match(
                surface
            )

            for button in self.buttons:
                button.draw(surface)

            return

        self._draw_player_panel(
            surface,
            self.left_panel_rect,
            player_id=1,
        )

        self._draw_player_panel(
            surface,
            self.right_panel_rect,
            player_id=2,
        )

        preview_player = None

        if (
            self.match.is_running
            and self.match.current_player.is_human
            and not self.ai_task.is_running
        ):
            preview_player = (
                self.match.board.current_player
            )

        self.board_renderer.draw(
            surface,
            self.match.board,
            preview_player=preview_player,
            show_column_numbers=True,
        )

        self._draw_status(surface)
        self._draw_analysis(surface)

        for button in self.buttons:
            button.draw(surface)

        if self._error_message:
            self._draw_error(surface)

    def _draw_player_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        player_id: int,
    ) -> None:
        assert self.match is not None

        player = self.match.player_for_id(
            player_id
        )

        is_current = (
            self.match.is_running
            and self.match.board.current_player
            == player_id
        )

        border_color = (
            THEME.accent_hover
            if is_current
            else THEME.panel_border
        )

        pygame.draw.rect(
            surface,
            THEME.panel_background,
            rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=(
                3
                if is_current
                else THEME.panel_border_width
            ),
            border_radius=THEME.panel_radius,
        )

        piece_color = (
            THEME.player_one
            if player_id == 1
            else THEME.player_two
        )

        pygame.draw.circle(
            surface,
            piece_color,
            (
                rect.centerx,
                rect.top + 45,
            ),
            20,
        )

        name_font = FONTS.get(
            THEME.font_subheading,
            bold=True,
        )

        name_surface = name_font.render(
            player.name,
            True,
            THEME.text_primary,
        )

        name_rect = name_surface.get_rect(
            center=(
                rect.centerx,
                rect.top + 92,
            )
        )

        surface.blit(
            name_surface,
            name_rect,
        )

        type_font = FONTS.get(
            THEME.font_small,
        )

        type_surface = type_font.render(
            player.player_type.display_name,
            True,
            THEME.text_secondary,
        )

        type_rect = type_surface.get_rect(
            center=(
                rect.centerx,
                rect.top + 125,
            )
        )

        surface.blit(
            type_surface,
            type_rect,
        )

        if is_current:
            turn_text = (
                "THINKING"
                if (
                    not player.is_human
                    and self.ai_task.is_running
                )
                else "CURRENT TURN"
            )

            turn_surface = type_font.render(
                turn_text,
                True,
                THEME.accent_hover,
            )

            turn_rect = turn_surface.get_rect(
                center=(
                    rect.centerx,
                    rect.bottom - 30,
                )
            )

            surface.blit(
                turn_surface,
                turn_rect,
            )

    def _draw_status(
        self,
        surface: pygame.Surface,
    ) -> None:
        assert self.match is not None

        font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        if (
            self.match.status
            is MatchStatus.FINISHED
        ):
            assert self.match.result is not None
            text = self.match.result.reason
            color = THEME.success

        elif (
            self.match.status
            is MatchStatus.ABORTED
        ):
            assert self.match.result is not None
            text = self.match.result.reason
            color = THEME.danger

        elif (
            self.match.current_player
            .is_human
        ):
            text = (
                f"{self.match.current_player.name}, "
                "choose a column."
            )
            color = THEME.text_primary

        else:
            text = (
                f"{self.match.current_player.name} "
                "is thinking..."
            )
            color = THEME.text_secondary

        text_surface = font.render(
            text,
            True,
            color,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.height - 108,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _draw_analysis(
        self,
        surface: pygame.Surface,
    ) -> None:
        if not self.config.show_analysis_panel:
            return

        if self._last_move is None:
            return

        analysis = self._last_move.analysis

        if analysis is None:
            return

        lines: list[str] = []

        if analysis.search_depth is not None:
            lines.append(
                f"Depth: "
                f"{analysis.search_depth}"
            )

        if analysis.elapsed_seconds > 0.0:
            lines.append(
                "Time: "
                f"{analysis.elapsed_seconds:.3f} s"
            )

        if analysis.value_estimate is not None:
            lines.append(
                "Value: "
                f"{analysis.value_estimate:.3f}"
            )

        if (
            analysis.policy_probabilities
            is not None
        ):
            probability = (
                analysis.policy_probabilities[
                    self._last_move.move.column
                ]
            )

            lines.append(
                "Policy: "
                f"{probability:.1%}"
            )

        if not lines:
            return

        font = FONTS.get(
            THEME.font_small,
        )

        text = "  ·  ".join(lines)

        text_surface = font.render(
            text,
            True,
            THEME.text_muted,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.height - 78,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _draw_error(
        self,
        surface: pygame.Surface,
    ) -> None:
        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        error_surface = font.render(
            self._error_message,
            True,
            THEME.danger,
        )

        error_rect = error_surface.get_rect(
            center=(
                self.width // 2,
                self.height - 48,
            )
        )

        surface.blit(
            error_surface,
            error_rect,
        )

    def _draw_missing_match(
        self,
        surface: pygame.Surface,
    ) -> None:
        font = FONTS.get(
            THEME.font_body,
        )

        text_surface = font.render(
            "No match has been configured.",
            True,
            THEME.warning,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.height // 2,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def refresh_layout(self) -> None:
        super().refresh_layout()

        side_panel_width = max(
            160,
            min(
                220,
                (self.width - 700) // 2,
            ),
        )

        panel_height = 180
        panel_y = 130

        self.left_panel_rect = pygame.Rect(
            THEME.screen_margin,
            panel_y,
            side_panel_width,
            panel_height,
        )

        self.right_panel_rect = pygame.Rect(
            self.width
            - THEME.screen_margin
            - side_panel_width,
            panel_y,
            side_panel_width,
            panel_height,
        )

        board_left = (
            self.left_panel_rect.right
            + THEME.section_spacing
        )

        board_right = (
            self.right_panel_rect.left
            - THEME.section_spacing
        )

        board_top = 105
        board_bottom = self.height - 150

        self.board_area = pygame.Rect(
            board_left,
            board_top,
            max(
                100,
                board_right - board_left,
            ),
            max(
                100,
                board_bottom - board_top,
            ),
        )

        self.board_renderer.set_area(
            self.board_area
        )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

        self.restart_button.set_position(
            self.width
            - THEME.screen_margin
            - THEME.small_button_width,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _restart_match(self) -> None:
        if self.match is None:
            return

        self._invalidate_ai_result()

        starting_player = (
            self.match.board.starting_player
        )

        self.match.start(
            starting_player=starting_player,
        )

        self._last_move = None
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

    def _return_to_main_menu(self) -> None:
        self._invalidate_ai_result()

        if (
            self.match is not None
            and self.match.is_running
        ):
            self.match.abort(
                "Match left by the user."
            )

        self.application.go_to_main_menu()

