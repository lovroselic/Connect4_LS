# players/human.py

from __future__ import annotations

from game import Connect4Board
from players.base import (
    MoveResult,
    Player,
    PlayerConfig,
    PlayerType,
)


class HumanPlayer(Player):
    """
    Human-controlled match participant.

    The game screen submits a selected column using submit_move().
    The match controller then retrieves it through choose_move().
    """

    def __init__(
        self,
        player_id: int,
        config: PlayerConfig,
    ) -> None:
        if config.player_type is not PlayerType.HUMAN:
            raise ValueError(
                "HumanPlayer requires PlayerType.HUMAN configuration."
            )

        super().__init__(
            player_id=player_id,
            config=config,
        )

        self._pending_column: int | None = None

    @property
    def has_pending_move(self) -> bool:
        """
        Return True when the UI has submitted a move.
        """
        return self._pending_column is not None

    @property
    def pending_column(self) -> int | None:
        """
        Return the submitted column without consuming it.
        """
        return self._pending_column

    def begin_match(self) -> None:
        """
        Clear stale input before a new match begins.
        """
        self._pending_column = None

    def end_match(self) -> None:
        """
        Clear any unconsumed input after a match ends.
        """
        self._pending_column = None

    def cancel(self) -> None:
        """
        Cancel an input waiting to be consumed.
        """
        self._pending_column = None

    def submit_move(
        self,
        column: int,
        board: Connect4Board | None = None,
    ) -> bool:
        """
        Submit a human-selected column.

        Returns False when:

            - column is not an integer;
            - column is outside 0..6;
            - a move is already pending;
            - the supplied board rejects the move.

        Passing the board is recommended because it allows immediate rejection
        of full columns or moves submitted after the game has ended.
        """
        if not isinstance(column, int):
            return False

        if column < 0 or column >= Connect4Board.COLS:
            return False

        if self._pending_column is not None:
            return False

        if board is not None:
            if board.current_player != self.player_id:
                return False

            if not board.can_play(column):
                return False

        self._pending_column = column
        return True

    def choose_move(
        self,
        board: Connect4Board,
    ) -> MoveResult | None:
        """
        Return and consume the pending human move.

        Returns None while waiting for input.
        """
        if self._pending_column is None:
            return None

        column = self._pending_column
        self._pending_column = None

        if board.current_player != self.player_id:
            return None

        if not board.can_play(column):
            return None

        return MoveResult(
            column=column,
        )

