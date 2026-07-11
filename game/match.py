
# game/match.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from time import perf_counter

from game.board import Connect4Board, MoveRecord
from players.base import MoveAnalysis, MoveResult, Player


class MatchStatus(Enum):
    """
    Current lifecycle state of a match.
    """

    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    FINISHED = auto()
    ABORTED = auto()


@dataclass(frozen=True, slots=True)
class MatchResult:
    """
    Final outcome of a completed or aborted match.
    """

    winner: int | None
    is_draw: bool
    move_count: int
    elapsed_seconds: float
    reason: str


@dataclass(frozen=True, slots=True)
class TurnResult:
    """
    Information about one committed move.
    """

    move: MoveRecord
    analysis: MoveAnalysis | None
    match_finished: bool
    match_result: MatchResult | None


class Connect4Match:
    """
    Controls one Connect Four match.

    The board is authoritative and must only be changed through this
    controller.
    """

    def __init__(
        self,
        player_one: Player,
        player_two: Player,
        *,
        starting_player: int = Connect4Board.PLAYER_ONE,
    ) -> None:
        if player_one.player_id != Connect4Board.PLAYER_ONE:
            raise ValueError(
                "player_one must have player_id 1."
            )

        if player_two.player_id != Connect4Board.PLAYER_TWO:
            raise ValueError(
                "player_two must have player_id 2."
            )

        if player_one is player_two:
            raise ValueError(
                "Player 1 and Player 2 must be separate objects."
            )

        self.players: dict[int, Player] = {
            Connect4Board.PLAYER_ONE: player_one,
            Connect4Board.PLAYER_TWO: player_two,
        }

        self.board = Connect4Board(
            starting_player=starting_player,
        )

        self.status = MatchStatus.NOT_STARTED
        self.result: MatchResult | None = None

        self.latest_analysis: MoveAnalysis | None = None
        self.analysis_history: list[
            MoveAnalysis | None
        ] = []

        self._started_at: float | None = None
        self._finished_at: float | None = None

    # ------------------------------------------------------------------
    # Match properties
    # ------------------------------------------------------------------

    @property
    def player_one(self) -> Player:
        return self.players[
            Connect4Board.PLAYER_ONE
        ]

    @property
    def player_two(self) -> Player:
        return self.players[
            Connect4Board.PLAYER_TWO
        ]

    @property
    def current_player(self) -> Player:
        return self.players[
            self.board.current_player
        ]

    @property
    def is_running(self) -> bool:
        return (
            self.status
            is MatchStatus.IN_PROGRESS
        )

    @property
    def is_finished(self) -> bool:
        return self.status in (
            MatchStatus.FINISHED,
            MatchStatus.ABORTED,
        )

    @property
    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0

        end_time = (
            self._finished_at
            if self._finished_at is not None
            else perf_counter()
        )

        return max(
            0.0,
            end_time - self._started_at,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(
        self,
        *,
        starting_player: int | None = None,
    ) -> None:
        """
        Start a fresh match.
        """
        if starting_player is None:
            starting_player = (
                self.board.starting_player
            )

        self.board.reset(
            starting_player=starting_player,
        )

        self.latest_analysis = None
        self.analysis_history.clear()
        self.result = None

        self._started_at = perf_counter()
        self._finished_at = None

        self.player_one.begin_match()
        self.player_two.begin_match()

        self.status = MatchStatus.IN_PROGRESS

    def abort(
        self,
        reason: str = "Match aborted.",
    ) -> MatchResult:
        """
        Abort the current match.
        """
        if self.status is MatchStatus.ABORTED:
            assert self.result is not None
            return self.result

        if self.status is MatchStatus.FINISHED:
            assert self.result is not None
            return self.result

        self.player_one.cancel()
        self.player_two.cancel()

        self._finished_at = perf_counter()
        self.status = MatchStatus.ABORTED

        self.result = MatchResult(
            winner=None,
            is_draw=False,
            move_count=self.board.move_count,
            elapsed_seconds=self.elapsed_seconds,
            reason=str(reason),
        )

        self.player_one.end_match()
        self.player_two.end_match()

        return self.result

    # ------------------------------------------------------------------
    # Human input
    # ------------------------------------------------------------------

    def submit_move(
        self,
        column: int,
    ) -> bool:
        """
        Submit a column to the current player.
        """
        if not self.is_running:
            return False

        submit_method = getattr(
            self.current_player,
            "submit_move",
            None,
        )

        if submit_method is None:
            return False

        return bool(
            submit_method(
                column,
                self.board,
            )
        )

    # ------------------------------------------------------------------
    # Turn progression
    # ------------------------------------------------------------------

    def update(self) -> TurnResult | None:
        """
        Ask the current player for a move and commit it.

        This synchronous method remains useful for human turns, tests,
        headless matches, and benchmarks.
        """
        if not self.is_running:
            return None

        player = self.current_player

        move_result = player.choose_move(
            self.board,
        )

        if move_result is None:
            return None

        return self._commit_move(
            player=player,
            move_result=move_result,
        )

    def play_one_turn(self) -> TurnResult | None:
        """
        Alias for update().
        """
        return self.update()

    def commit_move_result(
        self,
        *,
        player_id: int,
        expected_move_count: int,
        move_result: MoveResult,
    ) -> TurnResult | None:
        """
        Commit a move calculated outside the main match loop.

        The expected player and move count guard against stale background
        results after a restart, screen change, or another committed move.

        Returns None when the result is stale.
        """
        if not self.is_running:
            return None

        player_id = int(player_id)
        expected_move_count = int(
            expected_move_count
        )

        if (
            self.board.move_count
            != expected_move_count
        ):
            return None

        if (
            self.board.current_player
            != player_id
        ):
            return None

        player = self.player_for_id(
            player_id
        )

        return self._commit_move(
            player=player,
            move_result=move_result,
        )

    def _commit_move(
        self,
        *,
        player: Player,
        move_result: MoveResult,
    ) -> TurnResult:
        """
        Validate and commit one returned move.
        """
        if (
            player.player_id
            != self.board.current_player
        ):
            raise RuntimeError(
                f"Player {player.player_id} returned a move when "
                f"Player {self.board.current_player} was expected."
            )

        column = int(
            move_result.column
        )

        if not self.board.can_play(column):
            raise RuntimeError(
                f"Player {player.player_id} returned illegal column "
                f"{column}. Legal moves: "
                f"{self.board.legal_moves()}"
            )

        move = self.board.play(column)

        self.latest_analysis = (
            move_result.analysis
        )

        self.analysis_history.append(
            move_result.analysis
        )

        match_result: MatchResult | None = None

        if self.board.is_terminal:
            match_result = (
                self._finish_match()
            )

        return TurnResult(
            move=move,
            analysis=move_result.analysis,
            match_finished=self.is_finished,
            match_result=match_result,
        )

    def _finish_match(self) -> MatchResult:
        """
        Finalize a naturally completed match.
        """
        self._finished_at = perf_counter()
        self.status = MatchStatus.FINISHED

        if self.board.winner is not None:
            winner = self.board.winner
            reason = (
                f"{self.players[winner].name} wins."
            )
            is_draw = False
        else:
            winner = None
            reason = (
                "The board is full. "
                "The match is a draw."
            )
            is_draw = True

        self.result = MatchResult(
            winner=winner,
            is_draw=is_draw,
            move_count=self.board.move_count,
            elapsed_seconds=self.elapsed_seconds,
            reason=reason,
        )

        self.player_one.end_match()
        self.player_two.end_match()

        return self.result

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def player_for_id(
        self,
        player_id: int,
    ) -> Player:
        """
        Return a player by board identifier.
        """
        try:
            return self.players[
                int(player_id)
            ]

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "player_id must be 1 or 2, "
                f"got {player_id!r}"
            ) from error

    def analysis_for_move(
        self,
        move_index: int,
    ) -> MoveAnalysis | None:
        """
        Return analysis for a zero-based move index.
        """
        return self.analysis_history[
            move_index
        ]

