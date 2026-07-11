
# ui/screens/test_menu.py

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import pygame

from app.lookahead_config import LOOKAHEAD_CONFIG
from game.headless import HeadlessMatchRunner
from game.match import Connect4Match
from game.tournament import TournamentResult, TournamentRunner
from players import PlayerConfig, PlayerType
from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button


@dataclass(frozen=True, slots=True)
class SingleMatchTestResult:
    """
    Display data from one headless match.
    """

    winner_name: str
    reason: str
    move_count: int
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class DepthSweepEntry:
    """
    Result of one lookahead depth against PPO.
    """

    depth: int
    games: int
    lookahead_wins: int
    ppo_wins: int
    draws: int
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class DepthSweepResult:
    """
    Aggregate depth-sweep result.
    """

    entries: tuple[DepthSweepEntry, ...]
    elapsed_seconds: float


class TestMenuScreen(BaseScreen):
    """
    Development and benchmarking menu.

    Expensive tests run through the application's TaskManager so the Pygame
    event loop remains responsive.
    """

    BENCHMARK_GAMES = 10
    DEPTH_SWEEP_GAMES_PER_DEPTH = 2

    def __init__(self, application) -> None:
        super().__init__(application)

        self.task = self.application.task_manager.create_task()

        self.headless_match_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Headless Match",
            callback=self._start_headless_match,
        )

        self.agent_benchmark_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Agent Benchmark",
            callback=self._start_agent_benchmark,
        )

        self.depth_test_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Lookahead Depth Test",
            callback=self._start_depth_test,
        )

        self.ppo_validation_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="PPO Validation",
            callback=self._start_ppo_validation,
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
            self.headless_match_button,
            self.agent_benchmark_button,
            self.depth_test_button,
            self.ppo_validation_button,
            self.back_button,
        ]

        self.status_text = "Choose a test."
        self.result_lines: list[str] = []
        self.error_text = ""

        self._task_kind: str | None = None
        self._task_result_consumed = True
        self._activity_phase = 0.0

        self.refresh_layout()
        self.test_description = (
            "Select a test to see what it checks."
        )

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        super().on_enter()
        self._refresh_button_states()

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_ESCAPE
        ):
            if not self.task.is_running:
                self.application.go_back()

            return

        for button in self.buttons:
            if button.handle_event(event):
                return

    def update(
        self,
        delta_time: float,
    ) -> None:
        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(mouse_position)

        if self.task.is_running:
            self._activity_phase += delta_time
            self.status_text = self._running_status()
            self._refresh_button_states()
            return

        if (
            self.task.is_done
            and not self._task_result_consumed
        ):
            self._consume_task_result()

        self._refresh_button_states()

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
            "Test Menu",
            y=58,
        )

        self.draw_subtitle(
            surface,
            "Headless matches, benchmarks, and assorted machine arguments. Are you sure you want to do that?",
            y=105,
        )

        for button in self.buttons:
            button.draw(surface)

        self._draw_status_panel(surface)

        self.draw_footer(
            surface,
            "Tests use one worker thread so the interface remains responsive.",
        )

    # ------------------------------------------------------------------
    # Test commands
    # ------------------------------------------------------------------

   
    def _start_headless_match(self) -> None:
        self.test_description = (
            "Runs one complete Lookahead 5 vs PPO game without rendering."
        )
    
        self._start_task(
            kind="headless",
            status="Preparing one Lookahead 5 vs PPO match...",
            function=self._run_headless_match,
        )



    def _start_agent_benchmark(self) -> None:
        
        self.test_description = (
           f"Runs {self.BENCHMARK_GAMES} games between the default "
           "Lookahead depth and PPO, alternating who starts."
       )
        
        self._start_task(
            kind="benchmark",
            status=(
                f"Preparing {self.BENCHMARK_GAMES} benchmark games..."
            ),
            function=self._run_agent_benchmark,
        )

    def _start_depth_test(self) -> None:
        depth_count = (
            LOOKAHEAD_CONFIG.maximum_depth
            - LOOKAHEAD_CONFIG.minimum_depth
            + 1
        )

        total_games = (
            depth_count
            * self.DEPTH_SWEEP_GAMES_PER_DEPTH
        )
        
        self.test_description = (
           "Tests every configured Lookahead depth against PPO and "
           "compares wins, draws, and runtime."
       )


        self._start_task(
            kind="depth",
            status=(
                f"Preparing depth sweep: {total_games} games..."
            ),
            function=self._run_depth_test,
        )

    def _start_ppo_validation(self) -> None:
        self.test_description = (
           "Runs one PPO inference and verifies legal output, "
           "probabilities, value estimate, and inference time."
       )
        
        self._start_task(
            kind="ppo",
            status="Validating PPO inference...",
            function=self._run_ppo_validation,
        )

    def _start_task(
        self,
        *,
        kind: str,
        status: str,
        function,
    ) -> None:
        if self.task.is_running:
            return

        if self.task.is_done:
            self.task.clear()

        self._task_kind = kind
        self._task_result_consumed = False

        self.status_text = status
        self.result_lines.clear()
        self.error_text = ""
        self._activity_phase = 0.0

        started = self.task.start(function)

        if not started:
            self.error_text = "Could not start the background task."
            self._task_result_consumed = True

        self._refresh_button_states()

    # ------------------------------------------------------------------
    # Worker functions
    # ------------------------------------------------------------------

    def _run_headless_match(self) -> SingleMatchTestResult:
        player_one, player_two = (
            self.application.player_factory.create_pair(
                PlayerConfig(
                    player_type=PlayerType.LOOKAHEAD,
                    name="Lookahead 5",
                    lookahead_depth=5,
                ),
                PlayerConfig(
                    player_type=PlayerType.PPO,
                    name="PPO 2004",
                    deterministic=True,
                ),
            )
        )

        match = Connect4Match(
            player_one,
            player_two,
            starting_player=1,
        )

        run_result = HeadlessMatchRunner().run(
            match
        )

        result = run_result.match_result

        if result.winner is None:
            winner_name = "Draw"
        else:
            winner_name = match.player_for_id(
                result.winner
            ).name

        return SingleMatchTestResult(
            winner_name=winner_name,
            reason=result.reason,
            move_count=result.move_count,
            elapsed_seconds=run_result.elapsed_seconds,
        )

    def _run_agent_benchmark(
        self,
    ) -> TournamentResult:
        runner = TournamentRunner(
            self.application.player_factory
        )

        return runner.run(
            PlayerConfig(
                player_type=PlayerType.LOOKAHEAD,
                name=(
                    f"Lookahead "
                    f"{LOOKAHEAD_CONFIG.default_depth}"
                ),
                lookahead_depth=(
                    LOOKAHEAD_CONFIG.default_depth
                ),
            ),
            PlayerConfig(
                player_type=PlayerType.PPO,
                name="PPO 2004",
                deterministic=True,
            ),
            games=self.BENCHMARK_GAMES,
            alternate_starting_player=True,
            verbose=False,
        )

    def _run_depth_test(self) -> DepthSweepResult:
        started_at = perf_counter()
        entries: list[DepthSweepEntry] = []

        runner = TournamentRunner(
            self.application.player_factory
        )

        for depth in LOOKAHEAD_CONFIG.selectable_depths:
            tournament = runner.run(
                PlayerConfig(
                    player_type=PlayerType.LOOKAHEAD,
                    name=f"Lookahead {depth}",
                    lookahead_depth=depth,
                ),
                PlayerConfig(
                    player_type=PlayerType.PPO,
                    name="PPO 2004",
                    deterministic=True,
                ),
                games=self.DEPTH_SWEEP_GAMES_PER_DEPTH,
                alternate_starting_player=True,
                verbose=False,
            )

            entries.append(
                DepthSweepEntry(
                    depth=depth,
                    games=tournament.games_played,
                    lookahead_wins=(
                        tournament.player_one_wins
                    ),
                    ppo_wins=(
                        tournament.player_two_wins
                    ),
                    draws=tournament.draws,
                    elapsed_seconds=(
                        tournament.elapsed_seconds
                    ),
                )
            )

        return DepthSweepResult(
            entries=tuple(entries),
            elapsed_seconds=(
                perf_counter() - started_at
            ),
        )

    def _run_ppo_validation(
        self,
    ) -> dict[str, Any]:
        from game import Connect4Board
        from players import PPOPlayer

        player = self.application.player_factory.create(
            player_id=1,
            config=PlayerConfig(
                player_type=PlayerType.PPO,
                name="PPO Validation",
                deterministic=True,
            ),
        )

        if not isinstance(player, PPOPlayer):
            raise RuntimeError(
                "PlayerFactory did not create a PPOPlayer."
            )

        board = Connect4Board()

        result = player.choose_move(board)

        if result is None or result.analysis is None:
            raise RuntimeError(
                "PPO returned no move or analysis."
            )

        probabilities = (
            result.analysis.policy_probabilities
        )

        if probabilities is None:
            raise RuntimeError(
                "PPO returned no policy probabilities."
            )

        probability_sum = float(
            sum(probabilities)
        )

        legal = board.legal_moves()

        if result.column not in legal:
            raise RuntimeError(
                f"PPO selected illegal column {result.column}."
            )

        if not (
            0.999 <= probability_sum <= 1.001
        ):
            raise RuntimeError(
                "PPO probabilities do not sum to one: "
                f"{probability_sum}"
            )

        return {
            "column": result.column,
            "probability": probabilities[
                result.column
            ],
            "probability_sum": probability_sum,
            "value": result.analysis.value_estimate,
            "elapsed_seconds": (
                result.analysis.elapsed_seconds
            ),
        }

    # ------------------------------------------------------------------
    # Result handling
    # ------------------------------------------------------------------

    def _consume_task_result(self) -> None:
        self._task_result_consumed = True

        exception = self.task.exception()

        if exception is not None:
            self.status_text = "Test failed."
            self.error_text = (
                f"{type(exception).__name__}: {exception}"
            )
            return

        try:
            result = self.task.result()
        except Exception as error:
            self.status_text = "Test failed."
            self.error_text = (
                f"{type(error).__name__}: {error}"
            )
            return

        self.error_text = ""

        if isinstance(
            result,
            SingleMatchTestResult,
        ):
            self._show_single_match_result(result)

        elif isinstance(
            result,
            TournamentResult,
        ):
            self._show_tournament_result(result)

        elif isinstance(
            result,
            DepthSweepResult,
        ):
            self._show_depth_sweep_result(result)

        elif isinstance(result, dict):
            self._show_ppo_result(result)

        else:
            self.status_text = "Test completed."
            self.result_lines = [
                repr(result)
            ]

    def _show_single_match_result(
        self,
        result: SingleMatchTestResult,
    ) -> None:
        self.status_text = "Headless match completed."

        self.result_lines = [
            f"Result: {result.reason}",
            f"Winner: {result.winner_name}",
            f"Moves: {result.move_count}",
            f"Runtime: {result.elapsed_seconds:.3f} seconds",
        ]

    def _show_tournament_result(
        self,
        result: TournamentResult,
    ) -> None:
        self.status_text = "Agent benchmark completed."

        self.result_lines = [
            (
                f"Games: {result.games_played}  ·  "
                f"Lookahead wins: {result.player_one_wins}  ·  "
                f"PPO wins: {result.player_two_wins}  ·  "
                f"Draws: {result.draws}"
            ),
            (
                f"Lookahead: {result.player_one_win_rate:.1%}  ·  "
                f"PPO: {result.player_two_win_rate:.1%}  ·  "
                f"Draws: {result.draw_rate:.1%}"
            ),
            (
                f"Average moves: {result.average_moves:.1f}  ·  "
                f"Runtime: {result.elapsed_seconds:.2f} seconds"
            ),
        ]


    def _show_depth_sweep_result(
        self,
        result: DepthSweepResult,
    ) -> None:
        """
        Display the depth sweep in two columns so every configured depth fits
        inside the result panel.
        """
        self.status_text = "Lookahead depth sweep completed."
    
        entries = list(result.entries)
    
        split_index = (
            len(entries) + 1
        ) // 2
    
        left_entries = entries[:split_index]
        right_entries = entries[split_index:]
    
        lines = [
            (
                "Depth  LA  PPO  D   Time"
                "          "
                "Depth  LA  PPO  D   Time"
            )
        ]
    
        row_count = max(
            len(left_entries),
            len(right_entries),
        )
    
        for index in range(row_count):
            if index < len(left_entries):
                left = left_entries[index]
    
                left_text = (
                    f"{left.depth:>5}"
                    f"{left.lookahead_wins:>4}"
                    f"{left.ppo_wins:>5}"
                    f"{left.draws:>3}"
                    f"{left.elapsed_seconds:>7.2f}s"
                )
            else:
                left_text = " " * 24
    
            if index < len(right_entries):
                right = right_entries[index]
    
                right_text = (
                    f"{right.depth:>5}"
                    f"{right.lookahead_wins:>4}"
                    f"{right.ppo_wins:>5}"
                    f"{right.draws:>3}"
                    f"{right.elapsed_seconds:>7.2f}s"
                )
            else:
                right_text = ""
    
            lines.append(
                f"{left_text}          {right_text}"
            )
    
        lines.append(
            (
                f"Depths tested: "
                f"{LOOKAHEAD_CONFIG.minimum_depth}"
                f"–{LOOKAHEAD_CONFIG.maximum_depth}"
                f"  ·  Total runtime: "
                f"{result.elapsed_seconds:.2f} seconds"
            )
        )
    
        self.result_lines = lines



    def _show_ppo_result(
        self,
        result: dict[str, Any],
    ) -> None:
        self.status_text = "PPO validation passed."

        value = result.get("value")

        value_text = (
            "None"
            if value is None
            else f"{float(value):.4f}"
        )

        self.result_lines = [
            f"Selected column: {int(result['column']) + 1}",
            (
                "Selected probability: "
                f"{float(result['probability']):.3%}"
            ),
            (
                "Probability sum: "
                f"{float(result['probability_sum']):.6f}"
            ),
            f"Value estimate: {value_text}",
            (
                "Inference time: "
                f"{float(result['elapsed_seconds']):.4f} seconds"
            ),
        ]

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_status_panel(
        self,
        surface: pygame.Surface,
    ) -> None:
        panel_width = min(
            720,
            self.width - 2 * THEME.screen_margin,
        )

        panel_height = min(
            260,
            max(
                180,
                self.height - 515,
            ),
        )

        panel_rect = pygame.Rect(
            0,
            0,
            panel_width,
            panel_height,
        )

        panel_rect.midtop = (
            self.width // 2,
            430,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_background,
            panel_rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            panel_rect,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

        status_font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        status_surface = status_font.render(
            self.status_text,
            True,
            (
                THEME.accent_hover
                if self.task.is_running
                else THEME.text_primary
            ),
        )

        status_rect = status_surface.get_rect(
            midtop=(
                panel_rect.centerx,
                panel_rect.top + 22,
            )
        )

        surface.blit(
            status_surface,
            status_rect,
        )
        
        description_font = FONTS.get(
            THEME.font_small,
        )
        
        description_surface = description_font.render(
            self.test_description,
            True,
            THEME.text_muted,
        )
        
        description_rect = description_surface.get_rect(
            midtop=(
                panel_rect.centerx,
                panel_rect.top + 52,
            )
        )
        
        surface.blit(
            description_surface,
            description_rect,
        )

        if self.error_text:
            self._draw_wrapped_lines(
                surface,
                panel_rect,
                [self.error_text],
                start_y=panel_rect.top + 88,
                color=THEME.danger,
                monospace=False,
            )

        elif self.result_lines:
            self._draw_wrapped_lines(
                surface,
                panel_rect,
                self.result_lines,
                start_y=panel_rect.top + 88,
                color=THEME.text_secondary,
                monospace=(
                    self._task_kind == "depth"
                ),
            )

        elif self.task.is_running:
            self._draw_activity_indicator(
                surface,
                panel_rect,
            )

    def _draw_wrapped_lines(
        self,
        surface: pygame.Surface,
        panel_rect: pygame.Rect,
        lines: list[str],
        *,
        start_y: int,
        color: tuple[int, int, int],
        monospace: bool,
    ) -> None:
        font_name = (
            "consolas"
            if monospace
            else None
        )

        if font_name is None:
            font = FONTS.get(
                THEME.font_small,
            )
        else:
            font = pygame.font.SysFont(
                font_name,
                THEME.font_small,
            )

        y = start_y

        for line in lines:
            text_surface = font.render(
                line,
                True,
                color,
            )

            text_rect = text_surface.get_rect(
                midtop=(
                    panel_rect.centerx,
                    y,
                )
            )

            surface.blit(
                text_surface,
                text_rect,
            )

            y += font.get_linesize() + 5

            if y > panel_rect.bottom - 15:
                break

    def _draw_activity_indicator(
        self,
        surface: pygame.Surface,
        panel_rect: pygame.Rect,
    ) -> None:
        center = (
            panel_rect.centerx,
            panel_rect.centery + 25,
        )

        radius = 22
        angle = self._activity_phase * 5.0

        for index in range(8):
            phase = (
                angle
                + index
                * (2.0 * 3.141592653589793 / 8.0)
            )

            x = center[0] + int(
                radius * pygame.math.Vector2(
                    1,
                    0,
                ).rotate_rad(phase).x
            )

            y = center[1] + int(
                radius * pygame.math.Vector2(
                    1,
                    0,
                ).rotate_rad(phase).y
            )

            brightness = (
                70 + index * 20
            )

            pygame.draw.circle(
                surface,
                (
                    min(255, brightness),
                    min(255, brightness + 25),
                    min(255, brightness + 55),
                ),
                (x, y),
                4,
            )

    # ------------------------------------------------------------------
    # Layout and state
    # ------------------------------------------------------------------

    def refresh_layout(self) -> None:
        super().refresh_layout()

        center_x = self.width // 2
        first_y = 160
        spacing = THEME.button_height + 16

        self.headless_match_button.set_center(
            center_x,
            first_y,
        )

        self.agent_benchmark_button.set_center(
            center_x,
            first_y + spacing,
        )

        self.depth_test_button.set_center(
            center_x,
            first_y + spacing * 2,
        )

        self.ppo_validation_button.set_center(
            center_x,
            first_y + spacing * 3,
        )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    def _refresh_button_states(self) -> None:
        enabled = not self.task.is_running

        self.headless_match_button.set_enabled(
            enabled
        )

        self.agent_benchmark_button.set_enabled(
            enabled
        )

        self.depth_test_button.set_enabled(
            enabled
        )

        self.ppo_validation_button.set_enabled(
            enabled
        )

        self.back_button.set_enabled(
            enabled
        )

    def _running_status(self) -> str:
        dots = (
            int(self._activity_phase * 2.0)
            % 4
        )

        suffix = "." * dots

        labels = {
            "headless": "Running headless match",
            "benchmark": "Running agent benchmark",
            "depth": "Running lookahead depth sweep",
            "ppo": "Validating PPO model",
        }

        label = labels.get(
            self._task_kind,
            "Running test",
        )

        return f"{label}{suffix}"

