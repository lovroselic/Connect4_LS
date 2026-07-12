
# players/lookahead.py

from __future__ import annotations

from time import perf_counter

import numpy as np

from agents.lookahead import Connect4Lookahead
from game import Connect4Board
from players.base import (
    MoveAnalysis,
    MoveResult,
    Player,
    PlayerConfig,
    PlayerType,
)


class LookaheadPlayer(Player):
    """
    Player controlled by the Numba Connect Four lookahead engine.

    The main move search uses the configured depth. Optional per-column action
    scores are disabled by default because calculating them performs several
    additional searches and becomes very expensive at high depths.
    """

    def __init__(
        self,
        player_id: int,
        config: PlayerConfig,
        *,
        engine: Connect4Lookahead | None = None,
        include_action_scores: bool = False,
        action_score_depth: int | None = None,
    ) -> None:
        if config.player_type is not PlayerType.LOOKAHEAD:
            raise ValueError(
                "LookaheadPlayer requires PlayerType.LOOKAHEAD."
            )

        super().__init__(
            player_id=player_id,
            config=config,
        )

        self.engine = (
            engine
            if engine is not None
            else Connect4Lookahead()
        )

        self.include_action_scores = bool(
            include_action_scores
        )

        self.action_score_depth = (
            None
            if action_score_depth is None
            else max(1, int(action_score_depth))
        )

        self._cancel_requested = False

    @property
    def depth(self) -> int:
        return self.config.lookahead_depth

    def begin_match(self) -> None:
        self._cancel_requested = False

    def end_match(self) -> None:
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def choose_move(
        self,
        board: Connect4Board,
    ) -> MoveResult | None:
        if self._cancel_requested:
            return None

        if board.is_terminal:
            return None

        if board.current_player != self.player_id:
            return None

        legal_moves = board.legal_moves()

        if not legal_moves:
            return None

        numpy_board = board.to_numpy(
            dtype=np.int8,
        )

        started_at = perf_counter()

        column = self.engine.n_step_lookahead(
            numpy_board,
            player=self.player_id,
            depth=self.depth,
        )

        if self._cancel_requested:
            return None

        column = int(column)

        if column not in legal_moves:
            raise RuntimeError(
                "Lookahead engine returned an illegal move: "
                f"{column}. Legal moves: {legal_moves}"
            )

        action_scores: tuple[float, ...] | None = None

        if self.include_action_scores:
            score_depth = (
                self.action_score_depth
                if self.action_score_depth is not None
                else self.depth
            )

            raw_scores = self.engine.n_step_action_scores(
                numpy_board,
                player=self.player_id,
                depth=score_depth,
            )

            action_scores = tuple(
                float(score)
                for score in raw_scores
            )

        elapsed_seconds = (
            perf_counter() - started_at
        )

        evaluation = None

        if action_scores is not None:
            selected_score = action_scores[
                column
            ]

            if np.isfinite(selected_score):
                evaluation = float(
                    selected_score
                )

        analysis = MoveAnalysis(
            selected_column=column,
            elapsed_seconds=elapsed_seconds,
            evaluation=evaluation,
            search_depth=self.depth,
            action_scores=action_scores,
            message=(
                f"Lookahead depth {self.depth} "
                f"selected column {column}."
            ),
        )

        return MoveResult(
            column=column,
            analysis=analysis,
        )

