
# game/tournament.py

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from game.headless import HeadlessMatchRunner
from game.match import Connect4Match
from players import PlayerConfig, PlayerFactory


@dataclass(frozen=True, slots=True)
class TournamentResult:
    """
    Aggregate result of repeated matches.
    """

    games_played: int

    player_one_wins: int
    player_two_wins: int
    draws: int

    total_moves: int
    elapsed_seconds: float

    @property
    def player_one_win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0

        return (
            self.player_one_wins
            / self.games_played
        )

    @property
    def player_two_win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0

        return (
            self.player_two_wins
            / self.games_played
        )

    @property
    def draw_rate(self) -> float:
        if self.games_played == 0:
            return 0.0

        return (
            self.draws
            / self.games_played
        )

    @property
    def average_moves(self) -> float:
        if self.games_played == 0:
            return 0.0

        return (
            self.total_moves
            / self.games_played
        )


class TournamentRunner:
    """
    Run repeated headless games between two player configurations.
    """

    def __init__(
        self,
        player_factory: PlayerFactory,
    ) -> None:
        self.player_factory = player_factory
        self.headless_runner = HeadlessMatchRunner()

    def run(
        self,
        player_one_config: PlayerConfig,
        player_two_config: PlayerConfig,
        *,
        games: int,
        alternate_starting_player: bool = True,
        verbose: bool = False,
    ) -> TournamentResult:
        """
        Run a series of independent matches.
        """
        games = max(
            1,
            int(games),
        )

        player_one_wins = 0
        player_two_wins = 0
        draws = 0
        total_moves = 0

        started_at = perf_counter()

        for game_index in range(games):
            starting_player = 1

            if (
                alternate_starting_player
                and game_index % 2 == 1
            ):
                starting_player = 2

            player_one, player_two = (
                self.player_factory.create_pair(
                    player_one_config,
                    player_two_config,
                )
            )

            match = Connect4Match(
                player_one,
                player_two,
                starting_player=starting_player,
            )

            run_result = self.headless_runner.run(
                match
            )

            result = run_result.match_result

            total_moves += result.move_count

            if result.is_draw:
                draws += 1
            elif result.winner == 1:
                player_one_wins += 1
            elif result.winner == 2:
                player_two_wins += 1

            if verbose:
                print(
                    f"Game {game_index + 1}/{games}: "
                    f"{result.reason} "
                    f"({result.move_count} moves)"
                )

        elapsed_seconds = (
            perf_counter() - started_at
        )

        return TournamentResult(
            games_played=games,
            player_one_wins=player_one_wins,
            player_two_wins=player_two_wins,
            draws=draws,
            total_moves=total_moves,
            elapsed_seconds=elapsed_seconds,
        )

