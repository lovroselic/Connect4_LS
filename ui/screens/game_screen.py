
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


@dataclass(frozen=True, slots=True)
class HintWorkerResult:
    """
    LA13 hint calculated from an immutable board copy.
    """

    match_identity: int
    generation: int
    player_id: int
    expected_move_count: int
    move_result: MoveResult | None


@dataclass(slots=True)
class SessionScore:
    """
    Score accumulated across replays of the current match setup.
    """

    player_one_wins: int = 0
    player_two_wins: int = 0
    draws: int = 0

    @property
    def games_played(self) -> int:
        return (
            self.player_one_wins
            + self.player_two_wins
            + self.draws
        )

    def reset(self) -> None:
        self.player_one_wins = 0
        self.player_two_wins = 0
        self.draws = 0

    def record_result(
        self,
        winner: int | None,
        *,
        is_draw: bool,
    ) -> None:
        if is_draw or winner is None:
            self.draws += 1
            return

        if winner == 1:
            self.player_one_wins += 1
            return

        if winner == 2:
            self.player_two_wins += 1


class GameScreen(BaseScreen):
    """
    Graphical screen for one Connect Four match.

    AI move selection runs on the application's worker thread. The worker
    receives a board copy and never modifies the live match.

    Committed moves are displayed using a short falling-disc animation.
    A completed match displays a compact result panel beside the board.

    A session score is preserved across Restart and Play Again, while a new
    match created from Match Setup starts a fresh session.
    """

    OVERLAY_WIDTH = 280
    OVERLAY_HEIGHT = 250

    def __init__(self, application) -> None:
        super().__init__(application)

        self.match: Connect4Match | None = None

        self.board_renderer = BoardRenderer()

        self.ai_task = (
            self.application
            .task_manager
            .create_task()
        )

        self.hint_task = (
            self.application
            .task_manager
            .create_task()
        )

        self.session_score = SessionScore()
        self._current_result_recorded = False

        self._ai_paused = False
        self._step_requested = False

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

        self.reset_score_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Reset Score",
            callback=self._reset_session_score,
        )

        self.pause_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Pause",
            callback=self._toggle_ai_pause,
            visible=False,
        )

        self.step_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Step",
            callback=self._request_ai_step,
            enabled=False,
            visible=False,
        )

        self.hint_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Hint (LA13)",
            callback=self._request_hint,
            visible=False,
        )

        self.play_again_button = Button(
            rect=(
                0,
                0,
                210,
                THEME.small_button_height,
            ),
            text="Play Again",
            callback=self._restart_match,
            visible=False,
        )

        self.overlay_main_menu_button = Button(
            rect=(
                0,
                0,
                210,
                THEME.small_button_height,
            ),
            text="Main Menu",
            callback=self._return_to_main_menu,
            visible=False,
        )

        self.game_buttons = [
            self.back_button,
            self.restart_button,
            self.pause_button,
            self.step_button,
            self.hint_button,
            self.reset_score_button,
        ]

        self.overlay_buttons = [
            self.play_again_button,
            self.overlay_main_menu_button,
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

        self.overlay_rect = pygame.Rect(
            0,
            0,
            self.OVERLAY_WIDTH,
            self.OVERLAY_HEIGHT,
        )

        self._ai_delay_elapsed_ms = 0.0
        self._last_move: TurnResult | None = None
        self._error_message = ""

        self._generation = 0
        self._ai_result_consumed = True
        self._hint_result_consumed = True

        self._hint_column: int | None = None
        self._hint_analysis = None
        self._pending_win_sound = False

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
        Assign a newly configured match and reset the session score.
        """
        self._invalidate_ai_result()
        self._invalidate_hint_result()
        self.board_renderer.cancel_animation()
        self._set_overlay_visible(False)

        if (
            self.match is not None
            and self.match.is_running
        ):
            self.match.abort(
                "Match replaced by a new match."
            )

        self.match = match

        self.session_score.reset()
        self._current_result_recorded = False

        self._ai_paused = False
        self._step_requested = False
        self._refresh_ai_control_state()

        self._last_move = None
        self._clear_hint()
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

        if start_immediately:
            self.match.start()

        self._ensure_human_column_selection()

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

        self._refresh_overlay_state()
        self._refresh_ai_control_state()
        self._refresh_hint_button_state()
        self._ensure_human_column_selection()

    def on_exit(self) -> None:
        self.board_renderer.clear_selection()
        self.board_renderer.cancel_animation()
        self._invalidate_ai_result()
        self._invalidate_hint_result()
        self._set_overlay_visible(False)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        if self._game_over_overlay_visible():
            for button in self.overlay_buttons:
                if button.handle_event(event):
                    return

            if event.type == pygame.KEYDOWN:
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_r,
                ):
                    self._restart_match()
                    return

                if event.key == pygame.K_ESCAPE:
                    self._return_to_main_menu()
                    return

            return

        for button in self.game_buttons:
            if button.handle_event(event):
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._return_to_main_menu()
                return

            if event.key == pygame.K_r:
                self._restart_match()
                return

            if event.key == pygame.K_p:
                self._toggle_ai_pause()
                return

            if event.key in (
                pygame.K_n,
                pygame.K_PERIOD,
            ):
                self._request_ai_step()
                return

            if self._handle_human_keyboard(
                event.key
            ):
                return

        if event.type == pygame.MOUSEMOTION:
            if (
                self.match is not None
                and self._human_input_available()
            ):
                self.board_renderer.update_hover(
                    event.pos,
                    self.match.board,
                    interactive=True,
                )
            else:
                self.board_renderer.hovered_column = None

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

        if self.board_renderer.is_animating:
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

        self.board_renderer.set_selected_column(
            column,
            self.match.board,
        )

        self._play_human_column(
            column
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        delta_time: float,
    ) -> None:
        mouse_position = pygame.mouse.get_pos()

        was_animating = (
            self.board_renderer.is_animating
        )

        self.board_renderer.update(
            delta_time
            * self.config.animation_speed
        )

        if (
            was_animating
            and not self.board_renderer.is_animating
            and self._pending_win_sound
        ):
            self.application.audio.play_win()
            self._pending_win_sound = False

        self._consume_ai_task_if_ready()
        self._consume_hint_task_if_ready()
        self._refresh_overlay_state()
        self._refresh_ai_control_state()
        self._refresh_hint_button_state()

        if self._game_over_overlay_visible():
            for button in self.overlay_buttons:
                button.update(
                    mouse_position
                )

            return

        for button in self.game_buttons:
            button.update(
                mouse_position
            )

        if self.match is None:
            self.board_renderer.hovered_column = None
            return

        interactive = (
            self.match.is_running
            and self.match.current_player.is_human
            and not self.ai_task.is_running
            and not self.hint_task.is_running
            and not self.board_renderer.is_animating
        )

        if not interactive:
            self.board_renderer.hovered_column = None
         
        if interactive:
            self._ensure_human_column_selection()

        if not self.match.is_running:
            return

        if self.board_renderer.is_animating:
            self._ai_delay_elapsed_ms = 0.0
            return

        if self.match.current_player.is_human:
            self._ai_delay_elapsed_ms = 0.0
            return

        if self._is_ai_vs_ai() and self._ai_paused:
            self._ai_delay_elapsed_ms = 0.0

            if not self._step_requested:
                return

            if self.ai_task.is_running:
                return

            self._step_requested = False
            self._start_ai_task()
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

        if self.board_renderer.is_animating:
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
        self._clear_hint()
        self._invalidate_hint_result()

        self._last_move = turn
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

        self.board_renderer.start_drop(
            row=turn.move.row,
            column=turn.move.column,
            player=turn.move.player,
        )

        self.application.audio.play_disc_drop()

        self.board_renderer.selected_column = None

        if turn.match_finished:
            self._record_finished_match()

            self._pending_win_sound = (
                self.match is not None
                and self.match.result is not None
                and self.match.result.winner is not None
            )

    # ------------------------------------------------------------------
    # LA13 hint
    # ------------------------------------------------------------------

    def _hint_available(self) -> bool:
        return (
            self.match is not None
            and self.match.is_running
            and self.match.current_player.is_human
            and not self.ai_task.is_running
            and not self.hint_task.is_running
            and not self.board_renderer.is_animating
            and not self._game_over_overlay_visible()
        )

    def _request_hint(self) -> None:
        if not self._hint_available():
            return

        assert self.match is not None

        if self.hint_task.is_done:
            self.hint_task.clear()

        self._clear_hint()

        match = self.match
        board_copy = match.board.copy()

        match_identity = id(match)
        generation = self._generation
        player_id = match.board.current_player
        expected_move_count = (
            match.board.move_count
        )

        analyzer = (
            self.application
            .player_factory
            .create_lookahead_analyzer(
                player_id=player_id,
                depth=13,
            )
        )

        def calculate_hint() -> HintWorkerResult:
            move_result = analyzer.choose_move(
                board_copy
            )

            return HintWorkerResult(
                match_identity=match_identity,
                generation=generation,
                player_id=player_id,
                expected_move_count=(
                    expected_move_count
                ),
                move_result=move_result,
            )

        self._hint_result_consumed = False

        started = self.hint_task.start(
            calculate_hint
        )

        if not started:
            self._hint_result_consumed = True
            self._error_message = (
                "Could not start LA13 hint."
            )

    def _consume_hint_task_if_ready(
        self,
    ) -> None:
        if not self.hint_task.is_done:
            return

        if self._hint_result_consumed:
            return

        self._hint_result_consumed = True

        exception = self.hint_task.exception()

        if exception is not None:
            self._error_message = (
                "Hint failed: "
                f"{type(exception).__name__}: "
                f"{exception}"
            )

            self.hint_task.clear()
            return

        try:
            worker_result = (
                self.hint_task.result()
            )
        except Exception as error:
            self._error_message = (
                "Hint failed: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            self.hint_task.clear()
            return

        self.hint_task.clear()

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

        if not self.match.is_running:
            return

        if (
            self.match.board.move_count
            != worker_result.expected_move_count
        ):
            return

        if (
            self.match.board.current_player
            != worker_result.player_id
        ):
            return

        move_result = (
            worker_result.move_result
        )

        if move_result is None:
            self._error_message = (
                "LA13 returned no hint."
            )
            return

        if not self.match.board.can_play(
            move_result.column
        ):
            self._error_message = (
                "LA13 returned an illegal hint."
            )
            return

        self._hint_column = int(
            move_result.column
        )

        self._hint_analysis = (
            move_result.analysis
        )

        self.board_renderer.set_selected_column(
            self._hint_column,
            self.match.board,
        )

        self._error_message = ""

    def _refresh_hint_button_state(
        self,
    ) -> None:
        visible = (
            self.match is not None
            and self.match.is_running
            and self.match.current_player.is_human
            and not self._game_over_overlay_visible()
        )

        self.hint_button.set_visible(
            visible
        )

        self.hint_button.set_enabled(
            visible
            and not self.ai_task.is_running
            and not self.hint_task.is_running
            and not self.board_renderer.is_animating
        )

        self.hint_button.set_text(
            "Thinking..."
            if self.hint_task.is_running
            else "Hint (LA13)"
        )

    def _clear_hint(self) -> None:
        self._hint_column = None
        self._hint_analysis = None

    def _invalidate_hint_result(self) -> None:
        self._clear_hint()

        if self.hint_task.is_done:
            self._hint_result_consumed = True
            self.hint_task.clear()

    # ------------------------------------------------------------------
    # Human keyboard controls
    # ------------------------------------------------------------------

    def _human_input_available(self) -> bool:
        return (
            self.match is not None
            and self.match.is_running
            and self.match.current_player.is_human
            and not self.ai_task.is_running
            and not self.hint_task.is_running
            and not self.board_renderer.is_animating
            and not self._game_over_overlay_visible()
        )

    def _ensure_human_column_selection(self) -> None:
        if not self._human_input_available():
            if (
                self.match is None
                or not self.match.is_running
                or not self.match.current_player.is_human
            ):
                self.board_renderer.selected_column = None

            return

        selected = self.board_renderer.selected_column

        if (
            selected is None
            or not self.match.board.can_play(
                selected
            )
        ):
            self.board_renderer.select_first_legal_column(
                self.match.board,
                preferred=selected,
            )

    def _handle_human_keyboard(
        self,
        key: int,
    ) -> bool:
        if not self._human_input_available():
            return False

        assert self.match is not None

        number_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
            pygame.K_6: 5,
            pygame.K_7: 6,
            pygame.K_KP1: 0,
            pygame.K_KP2: 1,
            pygame.K_KP3: 2,
            pygame.K_KP4: 3,
            pygame.K_KP5: 4,
            pygame.K_KP6: 5,
            pygame.K_KP7: 6,
        }

        if key in number_keys:
            column = number_keys[key]

            self.board_renderer.set_selected_column(
                column,
                self.match.board,
            )

            self._play_human_column(
                column
            )

            return True

        if key in (
            pygame.K_LEFT,
            pygame.K_a,
        ):
            self.board_renderer.move_selection(
                self.match.board,
                -1,
            )
            return True

        if key in (
            pygame.K_RIGHT,
            pygame.K_d,
        ):
            self.board_renderer.move_selection(
                self.match.board,
                1,
            )
            return True

        if key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
        ):
            column = (
                self.board_renderer
                .selected_column
            )

            if column is None:
                self._ensure_human_column_selection()
                column = (
                    self.board_renderer
                    .selected_column
                )

            if column is not None:
                self._play_human_column(
                    column
                )

            return True

        return False

    def _play_human_column(
        self,
        column: int,
    ) -> None:
        if not self._human_input_available():
            return

        assert self.match is not None

        if not self.match.board.can_play(
            column
        ):
            self._error_message = (
                f"Column {column + 1} "
                "cannot be played."
            )
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
    # AI-vs-AI playback controls
    # ------------------------------------------------------------------

    def _is_ai_vs_ai(self) -> bool:
        return (
            self.match is not None
            and not self.match.player_one.is_human
            and not self.match.player_two.is_human
        )

    def _toggle_ai_pause(self) -> None:
        if self.match is None:
            return

        if not self.match.is_running:
            return

        if not self._is_ai_vs_ai():
            return

        self._ai_paused = not self._ai_paused
        self._step_requested = False
        self._ai_delay_elapsed_ms = 0.0

        if self._ai_paused:
            self._invalidate_ai_result()

        self._refresh_ai_control_state()

    def _request_ai_step(self) -> None:
        if self.match is None:
            return

        if not self.match.is_running:
            return

        if not self._is_ai_vs_ai():
            return

        if not self._ai_paused:
            return

        if self.board_renderer.is_animating:
            return

        if self.ai_task.is_running:
            return

        self._step_requested = True
        self._ai_delay_elapsed_ms = 0.0

    def _refresh_ai_control_state(self) -> None:
        visible = (
            self.match is not None
            and self._is_ai_vs_ai()
        )

        self.pause_button.set_visible(
            visible
        )

        self.step_button.set_visible(
            visible
        )

        if not visible:
            self._ai_paused = False
            self._step_requested = False

        self.pause_button.set_text(
            "Resume"
            if self._ai_paused
            else "Pause"
        )

        controls_enabled = (
            visible
            and self.match is not None
            and self.match.is_running
            and not self._game_over_overlay_visible()
        )

        self.pause_button.set_enabled(
            controls_enabled
        )

        self.step_button.set_enabled(
            controls_enabled
            and self._ai_paused
            and not self.ai_task.is_running
            and not self.board_renderer.is_animating
        )

    # ------------------------------------------------------------------
    # Session score
    # ------------------------------------------------------------------

    def _record_finished_match(self) -> None:
        """
        Record the completed game exactly once.
        """
        if self._current_result_recorded:
            return

        if self.match is None:
            return

        if self.match.result is None:
            return

        if (
            self.match.status
            is not MatchStatus.FINISHED
        ):
            return

        self.session_score.record_result(
            self.match.result.winner,
            is_draw=self.match.result.is_draw,
        )

        self._current_result_recorded = True

    def _reset_session_score(self) -> None:
        """
        Clear the score without restarting the active game.
        """
        self.session_score.reset()

        if (
            self.match is not None
            and self.match.status
            is MatchStatus.FINISHED
        ):
            self._current_result_recorded = True
        else:
            self._current_result_recorded = False

    # ------------------------------------------------------------------
    # Overlay state
    # ------------------------------------------------------------------

    def _game_over_overlay_visible(
        self,
    ) -> bool:
        return (
            self.match is not None
            and self.match.status
            is MatchStatus.FINISHED
            and not self.board_renderer.is_animating
        )

    def _refresh_overlay_state(
        self,
    ) -> None:
        self._set_overlay_visible(
            self._game_over_overlay_visible()
        )

    def _set_overlay_visible(
        self,
        visible: bool,
    ) -> None:
        for button in self.overlay_buttons:
            button.set_visible(
                visible
            )

        for button in self.game_buttons:
            button.set_enabled(
                not visible
            )

        if visible:
            self.board_renderer.hovered_column = None

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

            for button in self.game_buttons:
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
            and not self.board_renderer.is_animating
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
        self._draw_session_summary(surface)
        if (
            self.hint_task.is_running
            or self._hint_column is not None
        ):
            self._draw_hint_analysis(surface)
        else:
            self._draw_analysis(surface)

        for button in self.game_buttons:
            button.draw(surface)

        if self._error_message:
            self._draw_error(surface)

        if self._game_over_overlay_visible():
            self._draw_game_over_overlay(
                surface
            )

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
                rect.top + 40,
            ),
            18,
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
                rect.top + 84,
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
                rect.top + 113,
            )
        )

        surface.blit(
            type_surface,
            type_rect,
        )

        wins = (
            self.session_score.player_one_wins
            if player_id == 1
            else self.session_score.player_two_wins
        )

        score_font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        score_surface = score_font.render(
            f"Wins: {wins}",
            True,
            piece_color,
        )

        score_rect = score_surface.get_rect(
            center=(
                rect.centerx,
                rect.top + 143,
            )
        )

        surface.blit(
            score_surface,
            score_rect,
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
                    rect.bottom - 18,
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
            if self.board_renderer.is_animating:
                text = "Dropping final piece..."
                color = THEME.text_secondary
            else:
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
            self._is_ai_vs_ai()
            and self._ai_paused
        ):
            text = "AI match paused. Press Step or Resume."
            color = THEME.warning

        elif self.board_renderer.is_animating:
            text = "Dropping piece..."
            color = THEME.text_secondary

        elif self.match.current_player.is_human:
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
                self.height - 114,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _draw_session_summary(
        self,
        surface: pygame.Surface,
    ) -> None:
        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        text = (
            f"Games: {self.session_score.games_played}"
            f"  ·  Draws: {self.session_score.draws}"
        )

        text_surface = font.render(
            text,
            True,
            THEME.text_secondary,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.height - 94,
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

        if analysis.selected_column is not None:
            lines.append(
                "Column: "
                f"{analysis.selected_column + 1}"
            )

        if analysis.evaluation is not None:
            lines.append(
                "Score: "
                f"{analysis.evaluation:,.1f}"
            )

        if analysis.search_depth is not None:
            lines.append(
                f"Depth: {analysis.search_depth}"
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
                self.board_renderer.layout.board_rect.bottom + 34,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _draw_hint_analysis(
        self,
        surface: pygame.Surface,
    ) -> None:
        if self.hint_task.is_running:
            text = "LA13 is calculating a hint..."
            color = THEME.warning

        elif (
            self._hint_column is not None
            and self._hint_analysis is not None
        ):
            analysis = self._hint_analysis

            parts = [
                "Hint: column "
                f"{self._hint_column + 1}",
            ]

            if analysis.evaluation is not None:
                parts.append(
                    "score "
                    f"{analysis.evaluation:,.1f}"
                )

            if analysis.search_depth is not None:
                parts.append(
                    f"depth {analysis.search_depth}"
                )

            if analysis.elapsed_seconds > 0.0:
                parts.append(
                    f"{analysis.elapsed_seconds:.3f} s"
                )

            text = "  ·  ".join(parts)
            color = THEME.success

        else:
            return

        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        text_surface = font.render(
            text,
            True,
            color,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.board_renderer.layout.board_rect.bottom + 34,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def _draw_game_over_overlay(
        self,
        surface: pygame.Surface,
    ) -> None:
        assert self.match is not None
        assert self.match.result is not None

        shadow_rect = self.overlay_rect.move(
            8,
            10,
        )

        pygame.draw.rect(
            surface,
            THEME.shadow,
            shadow_rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_background,
            self.overlay_rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.accent_hover,
            self.overlay_rect,
            width=3,
            border_radius=THEME.panel_radius,
        )

        title_font = FONTS.get(
            THEME.font_subheading,
            bold=True,
        )

        result_font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        detail_font = FONTS.get(
            THEME.font_small,
        )

        title_surface = title_font.render(
            "Game Over",
            True,
            THEME.text_primary,
        )

        title_rect = title_surface.get_rect(
            center=(
                self.overlay_rect.centerx,
                self.overlay_rect.top + 30,
            )
        )

        surface.blit(
            title_surface,
            title_rect,
        )

        result_surface = result_font.render(
            self.match.result.reason,
            True,
            THEME.success,
        )

        result_rect = result_surface.get_rect(
            center=(
                self.overlay_rect.centerx,
                self.overlay_rect.top + 63,
            )
        )

        surface.blit(
            result_surface,
            result_rect,
        )

        details = (
            f"Moves: {self.match.result.move_count}"
            f"  ·  "
            f"{self.match.result.elapsed_seconds:.2f} s"
        )

        detail_surface = detail_font.render(
            details,
            True,
            THEME.text_secondary,
        )

        detail_rect = detail_surface.get_rect(
            center=(
                self.overlay_rect.centerx,
                self.overlay_rect.top + 91,
            )
        )

        surface.blit(
            detail_surface,
            detail_rect,
        )

        series_text = (
            f"Series: "
            f"{self.session_score.player_one_wins}"
            f" – "
            f"{self.session_score.player_two_wins}"
            f"  ·  Draws {self.session_score.draws}"
        )

        series_surface = detail_font.render(
            series_text,
            True,
            THEME.text_muted,
        )

        series_rect = series_surface.get_rect(
            center=(
                self.overlay_rect.centerx,
                self.overlay_rect.top + 116,
            )
        )

        surface.blit(
            series_surface,
            series_rect,
        )

        for button in self.overlay_buttons:
            button.draw(surface)

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
                self.height - 42,
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
        board_bottom = self.height - 160

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

        bottom_button_y = (
            self.height
            - THEME.screen_margin
            - THEME.small_button_height
        )

        self.back_button.set_position(
            THEME.screen_margin,
            bottom_button_y,
        )

        self.restart_button.set_position(
            self.width
            - THEME.screen_margin
            - THEME.small_button_width,
            bottom_button_y,
        )

        control_center_y = (
            bottom_button_y
            + THEME.small_button_height // 2
        )

        control_gap = 12
        control_width = THEME.small_button_width

        total_control_width = (
            control_width * 3
            + control_gap * 2
        )

        controls_left = (
            self.width // 2
            - total_control_width // 2
        )

        self.pause_button.set_position(
            controls_left,
            bottom_button_y,
        )

        self.step_button.set_position(
            controls_left
            + control_width
            + control_gap,
            bottom_button_y,
        )

        self.hint_button.set_position(
            self.width // 2
            - control_width
            - control_gap // 2,
            bottom_button_y,
        )

        self.reset_score_button.set_position(
            self.width // 2
            + control_gap // 2,
            bottom_button_y,
        )

        overlay_width = min(
            self.OVERLAY_WIDTH,
            self.width
            - 2 * THEME.screen_margin,
        )

        overlay_height = min(
            self.OVERLAY_HEIGHT,
            self.height
            - 2 * THEME.screen_margin,
        )

        self.overlay_rect = pygame.Rect(
            0,
            0,
            overlay_width,
            overlay_height,
        )

        preferred_x = (
            self.board_renderer
            .layout
            .board_rect
            .right
            + THEME.section_spacing
        )

        maximum_x = (
            self.width
            - THEME.screen_margin
            - overlay_width
        )

        overlay_x = min(
            preferred_x,
            maximum_x,
        )

        overlay_x = max(
            THEME.screen_margin,
            overlay_x,
        )

        overlay_y = (
            self.right_panel_rect.bottom
            + THEME.section_spacing
        )

        overlay_y = max(
            90,
            min(
                overlay_y,
                self.height
                - THEME.screen_margin
                - overlay_height
                - THEME.small_button_height,
            ),
        )

        self.overlay_rect.topleft = (
            overlay_x,
            overlay_y,
        )

        button_y = (
            self.overlay_rect.top + 147
        )

        self.play_again_button.set_center(
            self.overlay_rect.centerx,
            button_y,
        )

        self.overlay_main_menu_button.set_center(
            self.overlay_rect.centerx,
            button_y
            + THEME.small_button_height
            + 12,
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _restart_match(self) -> None:
        if self.match is None:
            return

        self._invalidate_ai_result()
        self._invalidate_hint_result()
        self.board_renderer.cancel_animation()
        self.board_renderer.clear_selection()
        self._set_overlay_visible(False)

        self.match.restart()

        self._ai_paused = False
        self._step_requested = False
        self._refresh_ai_control_state()
        self._refresh_hint_button_state()

        self._current_result_recorded = False
        self._pending_win_sound = False
        self._last_move = None
        self._error_message = ""
        self._ai_delay_elapsed_ms = 0.0

        self._ensure_human_column_selection()

    def _return_to_main_menu(self) -> None:
        self._invalidate_ai_result()
        self.board_renderer.cancel_animation()
        self.board_renderer.clear_selection()
        self._set_overlay_visible(False)

        self._ai_paused = False
        self._step_requested = False
        self._pending_win_sound = False
        self._refresh_ai_control_state()
        self._refresh_hint_button_state()

        if (
            self.match is not None
            and self.match.is_running
        ):
            self.match.abort(
                "Match left by the user."
            )

        self.application.go_to_main_menu()

