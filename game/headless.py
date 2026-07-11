
# game/headless.py

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from game.match import Connect4Match, MatchResult, TurnResult


TurnCallback = Callable[
    [Connect4Match, TurnResult],
    None,
]


@dataclass(frozen=True, slots=True)
class HeadlessRunResult:
    """
    Result of one completed headless match.
    """

    match_result: MatchResult
    elapsed_seconds: float
    turns_played: int


class HeadlessMatchRunner:
    """
    Run Connect4Match instances without Pygame or animation delays.

    Human players are not suitable for this runner unless their moves have
    already been submitted externally.
    """

    def __init__(
        self,
        *,
        maximum_turns: int = 42,
    ) -> None:
        self.maximum_turns = max(
            1,
            int(maximum_turns),
        )

    def run(
        self,
        match: Connect4Match,
        *,
        start_match: bool = True,
        on_turn: TurnCallback | None = None,
    ) -> HeadlessRunResult:
        """
        Run a match until it finishes.

        Raises RuntimeError if a player repeatedly returns no move or if the
        configured turn limit is exceeded.
        """
        if start_match:
            match.start()

        if not match.is_running:
            raise RuntimeError(
                "The supplied match is not running."
            )

        started_at = perf_counter()
        turns_played = 0

        while match.is_running:
            turn = match.play_one_turn()

            if turn is None:
                raise RuntimeError(
                    "Headless match stalled because the current player "
                    f"'{match.current_player.name}' returned no move."
                )

            turns_played += 1

            if on_turn is not None:
                on_turn(
                    match,
                    turn,
                )

            if turns_played > self.maximum_turns:
                match.abort(
                    "Headless match exceeded the maximum turn limit."
                )

                raise RuntimeError(
                    "Headless match exceeded "
                    f"{self.maximum_turns} turns."
                )

        if match.result is None:
            raise RuntimeError(
                "Headless match ended without a MatchResult."
            )

        elapsed_seconds = (
            perf_counter() - started_at
        )

        return HeadlessRunResult(
            match_result=match.result,
            elapsed_seconds=elapsed_seconds,
            turns_played=turns_played,
        )

