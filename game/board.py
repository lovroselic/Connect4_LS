
# game/board.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True, slots=True)
class MoveRecord:
    """
    One committed Connect Four move.
    """

    column: int
    row: int
    player: int
    bit: int


@dataclass(frozen=True, slots=True)
class BoardSnapshot:
    """
    Immutable representation of a Connect Four position.

    This can safely be passed to AI workers without exposing the live board
    object to mutation.
    """

    player_one_bits: int
    player_two_bits: int
    mask: int
    current_player: int
    move_count: int
    winner: int | None


class Connect4Board:
    """
    Authoritative Connect Four game state.

    Bitboard layout:

        - 6 playable rows
        - 7 columns
        - 7 bits per column
        - the seventh bit in each column is an unused sentinel bit
        - playable row 0 is the bottom row

    Bit index:

        column * STRIDE + bottom_based_row

    Public matrix representations use the conventional screen layout:

        row 0 = top
        row 5 = bottom

    Cell values:

        0 = empty
        1 = Player 1
        2 = Player 2
    """

    ROWS = 6
    COLS = 7
    CONNECT = 4

    STRIDE = ROWS + 1

    PLAYER_ONE = 1
    PLAYER_TWO = 2
    EMPTY = 0

    CENTER_COLUMN = COLS // 2
    CENTER_ORDER = (3, 4, 2, 5, 1, 6, 0)

    COL_MASK: tuple[int, ...]
    TOP_MASK: tuple[int, ...]
    BOTTOM_MASK: tuple[int, ...]
    FULL_MASK: int
    SENTINEL_MASK: int
    WIN_MASKS: tuple[int, ...]
    WIN_CELLS: tuple[tuple[tuple[int, int], ...], ...]

    _PRECOMPUTED = False

    def __init__(
        self,
        *,
        starting_player: int = PLAYER_ONE,
    ) -> None:
        self._ensure_precomputed()

        self._starting_player = self._validate_player(starting_player)

        self.player_one_bits = 0
        self.player_two_bits = 0
        self.mask = 0

        self.current_player = self._starting_player
        self.move_count = 0

        self.winner: int | None = None
        self.move_history: list[MoveRecord] = []

    # ------------------------------------------------------------------
    # Construction and reset
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        starting_player: int | None = None,
    ) -> None:
        """
        Reset the board to an empty position.
        """
        if starting_player is not None:
            self._starting_player = self._validate_player(
                starting_player
            )

        self.player_one_bits = 0
        self.player_two_bits = 0
        self.mask = 0

        self.current_player = self._starting_player
        self.move_count = 0

        self.winner = None
        self.move_history.clear()

    def copy(self) -> "Connect4Board":
        """
        Return an independent mutable copy of this board.
        """
        clone = Connect4Board(
            starting_player=self._starting_player
        )

        clone.player_one_bits = self.player_one_bits
        clone.player_two_bits = self.player_two_bits
        clone.mask = self.mask

        clone.current_player = self.current_player
        clone.move_count = self.move_count
        clone.winner = self.winner

        clone.move_history = self.move_history.copy()

        return clone

    def snapshot(self) -> BoardSnapshot:
        """
        Return an immutable snapshot of the current position.
        """
        return BoardSnapshot(
            player_one_bits=self.player_one_bits,
            player_two_bits=self.player_two_bits,
            mask=self.mask,
            current_player=self.current_player,
            move_count=self.move_count,
            winner=self.winner,
        )

    # ------------------------------------------------------------------
    # Board state properties
    # ------------------------------------------------------------------

    @property
    def starting_player(self) -> int:
        return self._starting_player

    @property
    def is_full(self) -> bool:
        return self.mask == self.FULL_MASK

    @property
    def is_draw(self) -> bool:
        return self.is_full and self.winner is None

    @property
    def is_terminal(self) -> bool:
        return self.winner is not None or self.is_full

    @property
    def last_move(self) -> MoveRecord | None:
        if not self.move_history:
            return None

        return self.move_history[-1]

    @property
    def player_one_count(self) -> int:
        return self.player_one_bits.bit_count()

    @property
    def player_two_count(self) -> int:
        return self.player_two_bits.bit_count()

    # ------------------------------------------------------------------
    # Move handling
    # ------------------------------------------------------------------

    def can_play(self, column: int) -> bool:
        """
        Return True when a move can legally be played in the column.

        This method returns False rather than raising for out-of-range columns.
        """
        if not isinstance(column, int):
            return False

        if column < 0 or column >= self.COLS:
            return False

        if self.is_terminal:
            return False

        return (self.mask & self.TOP_MASK[column]) == 0

    def legal_moves(
        self,
        *,
        center_first: bool = False,
    ) -> list[int]:
        """
        Return all currently legal columns.
        """
        order = (
            self.CENTER_ORDER
            if center_first
            else range(self.COLS)
        )

        return [
            column
            for column in order
            if self.can_play(column)
        ]

    def play(self, column: int) -> MoveRecord:
        """
        Commit one move for the current player.

        Raises:
            TypeError:
                If column is not an integer.

            ValueError:
                If the column is outside 0..6.

            RuntimeError:
                If the game is already over or the selected column is full.
        """
        if not isinstance(column, int):
            raise TypeError(
                f"column must be int, got {type(column).__name__}"
            )

        if column < 0 or column >= self.COLS:
            raise ValueError(
                f"column must be between 0 and {self.COLS - 1}, "
                f"got {column}"
            )

        if self.is_terminal:
            raise RuntimeError(
                "Cannot play a move after the game has ended."
            )

        if (self.mask & self.TOP_MASK[column]) != 0:
            raise RuntimeError(
                f"Column {column} is full."
            )

        player = self.current_player
        move_bit = self._play_bit(
            self.mask,
            column,
        )

        if move_bit == 0:
            raise RuntimeError(
                f"Could not calculate a valid move bit for column {column}."
            )

        row = self._row_from_bit(
            move_bit,
            column,
        )

        self.mask |= move_bit

        if player == self.PLAYER_ONE:
            self.player_one_bits |= move_bit
            player_bits = self.player_one_bits
        else:
            self.player_two_bits |= move_bit
            player_bits = self.player_two_bits

        self.move_count += 1

        record = MoveRecord(
            column=column,
            row=row,
            player=player,
            bit=move_bit,
        )

        self.move_history.append(record)

        if self._has_won_bits(player_bits):
            self.winner = player
        elif not self.is_full:
            self.current_player = self.other_player(player)

        return record

    def undo(self) -> MoveRecord | None:
        """
        Undo the most recent move.

        Returns the removed move, or None when the history is empty.
        """
        if not self.move_history:
            return None

        record = self.move_history.pop()

        self.mask &= ~record.bit

        if record.player == self.PLAYER_ONE:
            self.player_one_bits &= ~record.bit
        else:
            self.player_two_bits &= ~record.bit

        self.move_count -= 1
        self.current_player = record.player
        self.winner = None

        return record

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(
        self,
        row: int,
        column: int,
    ) -> int:
        """
        Return the cell value using top-based matrix coordinates.

        row 0 is the top row.
        """
        self._validate_matrix_coordinates(
            row,
            column,
        )

        bottom_row = self.ROWS - 1 - row
        bit = self.bit_at(
            column,
            bottom_row,
        )

        if self.player_one_bits & bit:
            return self.PLAYER_ONE

        if self.player_two_bits & bit:
            return self.PLAYER_TWO

        return self.EMPTY

    def column_height(self, column: int) -> int:
        """
        Return the number of occupied playable cells in a column.
        """
        self._validate_column(column)

        return (
            self.mask
            & self.COL_MASK[column]
        ).bit_count()

    # ------------------------------------------------------------------
    # Win handling
    # ------------------------------------------------------------------

    def has_won(self, player: int) -> bool:
        """
        Return True when the supplied player has four connected pieces.
        """
        player = self._validate_player(player)

        bits = (
            self.player_one_bits
            if player == self.PLAYER_ONE
            else self.player_two_bits
        )

        return self._has_won_bits(bits)

    def winning_cells(
        self,
        player: int | None = None,
    ) -> tuple[tuple[int, int], ...]:
        """
        Return one winning group of four cells.

        Coordinates use top-based matrix rows:

            (row, column)

        Returns an empty tuple when no winning line exists.
        """
        if player is None:
            player = self.winner

        if player is None:
            return ()

        player = self._validate_player(player)

        bits = (
            self.player_one_bits
            if player == self.PLAYER_ONE
            else self.player_two_bits
        )

        for mask, cells in zip(
            self.WIN_MASKS,
            self.WIN_CELLS,
        ):
            if bits & mask == mask:
                return cells

        return ()

    # ------------------------------------------------------------------
    # Matrix conversion
    # ------------------------------------------------------------------

    def to_numpy(
        self,
        *,
        dtype=np.int8,
    ) -> np.ndarray:
        """
        Convert the position to a top-to-bottom 6 x 7 NumPy board.
        """
        board = np.zeros(
            (self.ROWS, self.COLS),
            dtype=dtype,
        )

        for column in range(self.COLS):
            for bottom_row in range(self.ROWS):
                bit = self.bit_at(
                    column,
                    bottom_row,
                )

                matrix_row = (
                    self.ROWS - 1 - bottom_row
                )

                if self.player_one_bits & bit:
                    board[matrix_row, column] = (
                        self.PLAYER_ONE
                    )
                elif self.player_two_bits & bit:
                    board[matrix_row, column] = (
                        self.PLAYER_TWO
                    )

        return board

    def to_flat_list(self) -> list[int]:
        """
        Convert the board to Kaggle's flat top-to-bottom list format.
        """
        return self.to_numpy(
            dtype=np.int8
        ).reshape(-1).astype(int).tolist()

    @classmethod
    def from_numpy(
        cls,
        board: np.ndarray | Iterable[Iterable[int]],
        *,
        starting_player: int = PLAYER_ONE,
        current_player: int | None = None,
        validate: bool = True,
    ) -> "Connect4Board":
        """
        Build a board from a top-to-bottom 6 x 7 matrix.

        This reconstructs move history column by column only as a legal stack
        representation. It cannot recover the original chronological order
        from a static matrix, so move_history remains empty.
        """
        array = np.asarray(board)

        if array.shape != (cls.ROWS, cls.COLS):
            raise ValueError(
                "board must have shape "
                f"({cls.ROWS}, {cls.COLS}), "
                f"got {array.shape}"
            )

        result = cls(
            starting_player=starting_player
        )

        player_one_bits = 0
        player_two_bits = 0
        mask = 0

        for matrix_row in range(cls.ROWS):
            bottom_row = (
                cls.ROWS - 1 - matrix_row
            )

            for column in range(cls.COLS):
                value = int(
                    array[matrix_row, column]
                )

                if value == cls.EMPTY:
                    continue

                if value not in (
                    cls.PLAYER_ONE,
                    cls.PLAYER_TWO,
                ):
                    raise ValueError(
                        "Board cells must contain only "
                        "0, 1, or 2."
                    )

                bit = cls.bit_at(
                    column,
                    bottom_row,
                )

                mask |= bit

                if value == cls.PLAYER_ONE:
                    player_one_bits |= bit
                else:
                    player_two_bits |= bit

        result.player_one_bits = player_one_bits
        result.player_two_bits = player_two_bits
        result.mask = mask

        result.move_count = mask.bit_count()
        result.move_history = []

        p1_won = result._has_won_bits(
            player_one_bits
        )
        p2_won = result._has_won_bits(
            player_two_bits
        )

        if p1_won and not p2_won:
            result.winner = cls.PLAYER_ONE
        elif p2_won and not p1_won:
            result.winner = cls.PLAYER_TWO
        else:
            result.winner = None

        if current_player is None:
            result.current_player = (
                result._infer_current_player()
            )
        else:
            result.current_player = (
                result._validate_player(
                    current_player
                )
            )

        if validate:
            result.validate_position()

        return result

    @classmethod
    def from_flat_list(
        cls,
        board: Iterable[int],
        *,
        starting_player: int = PLAYER_ONE,
        current_player: int | None = None,
        validate: bool = True,
    ) -> "Connect4Board":
        """
        Build a board from Kaggle's flat 42-element board format.
        """
        values = list(board)

        expected_size = cls.ROWS * cls.COLS

        if len(values) != expected_size:
            raise ValueError(
                f"Flat board must contain {expected_size} values, "
                f"got {len(values)}"
            )

        array = np.asarray(
            values,
            dtype=np.int8,
        ).reshape(
            cls.ROWS,
            cls.COLS,
        )

        return cls.from_numpy(
            array,
            starting_player=starting_player,
            current_player=current_player,
            validate=validate,
        )

    @classmethod
    def from_moves(
        cls,
        moves: Iterable[int],
        *,
        starting_player: int = PLAYER_ONE,
    ) -> "Connect4Board":
        """
        Build a board by replaying a chronological sequence of columns.
        """
        result = cls(
            starting_player=starting_player
        )

        for move_number, column in enumerate(
            moves,
            start=1,
        ):
            try:
                result.play(int(column))
            except (
                TypeError,
                ValueError,
                RuntimeError,
            ) as error:
                raise ValueError(
                    f"Invalid move at position {move_number}: "
                    f"{column!r}"
                ) from error

        return result

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_position(self) -> None:
        """
        Validate the internal position.

        Raises ValueError when the position cannot represent a legal
        Connect Four state.
        """
        if self.player_one_bits & self.player_two_bits:
            raise ValueError(
                "Player bitboards overlap."
            )

        combined = (
            self.player_one_bits
            | self.player_two_bits
        )

        if self.mask != combined:
            raise ValueError(
                "mask does not equal the union of both player bitboards."
            )

        if self.mask & self.SENTINEL_MASK:
            raise ValueError(
                "Position contains occupied sentinel bits."
            )

        if self.mask & ~self.FULL_MASK:
            raise ValueError(
                "Position contains bits outside the playable board."
            )

        self._validate_gravity()

        p1_count = self.player_one_count
        p2_count = self.player_two_count

        if self._starting_player == self.PLAYER_ONE:
            if not (
                p1_count == p2_count
                or p1_count == p2_count + 1
            ):
                raise ValueError(
                    "Stone counts are inconsistent with Player 1 "
                    "starting the game."
                )
        else:
            if not (
                p2_count == p1_count
                or p2_count == p1_count + 1
            ):
                raise ValueError(
                    "Stone counts are inconsistent with Player 2 "
                    "starting the game."
                )

        p1_won = self._has_won_bits(
            self.player_one_bits
        )
        p2_won = self._has_won_bits(
            self.player_two_bits
        )

        if p1_won and p2_won:
            raise ValueError(
                "Both players cannot have winning positions "
                "in a legal completed game."
            )

        if p1_won:
            expected_last_player = (
                self.PLAYER_ONE
            )

            if self._last_player_from_counts() != expected_last_player:
                raise ValueError(
                    "Player 1 has won but the stone counts indicate "
                    "Player 1 did not move last."
                )

        if p2_won:
            expected_last_player = (
                self.PLAYER_TWO
            )

            if self._last_player_from_counts() != expected_last_player:
                raise ValueError(
                    "Player 2 has won but the stone counts indicate "
                    "Player 2 did not move last."
                )

    def _validate_gravity(self) -> None:
        """
        Ensure there are no floating pieces in any column.
        """
        for column in range(self.COLS):
            occupied = (
                self.mask
                & self.COL_MASK[column]
            )

            seen_empty = False

            for bottom_row in range(self.ROWS):
                bit = self.bit_at(
                    column,
                    bottom_row,
                )

                if occupied & bit:
                    if seen_empty:
                        raise ValueError(
                            f"Column {column} contains a floating piece."
                        )
                else:
                    seen_empty = True

    # ------------------------------------------------------------------
    # Bitboard helpers
    # ------------------------------------------------------------------

    @classmethod
    def bit_at(
        cls,
        column: int,
        bottom_row: int,
    ) -> int:
        """
        Return the bit representing one playable cell.

        bottom_row 0 is the lowest row.
        """
        return 1 << (
            column * cls.STRIDE + bottom_row
        )

    @classmethod
    def _play_bit(
        cls,
        mask: int,
        column: int,
    ) -> int:
        return (
            mask + cls.BOTTOM_MASK[column]
        ) & cls.COL_MASK[column]

    @classmethod
    def _has_won_bits(
        cls,
        bits: int,
    ) -> bool:
        vertical = bits & (
            bits >> 1
        )

        if vertical & (
            vertical >> 2
        ):
            return True

        horizontal = bits & (
            bits >> cls.STRIDE
        )

        if horizontal & (
            horizontal
            >> (2 * cls.STRIDE)
        ):
            return True

        diagonal_up = bits & (
            bits >> (cls.STRIDE + 1)
        )

        if diagonal_up & (
            diagonal_up
            >> (2 * (cls.STRIDE + 1))
        ):
            return True

        diagonal_down = bits & (
            bits >> (cls.STRIDE - 1)
        )

        if diagonal_down & (
            diagonal_down
            >> (2 * (cls.STRIDE - 1))
        ):
            return True

        return False

    @classmethod
    def _ensure_precomputed(cls) -> None:
        if cls._PRECOMPUTED:
            return

        column_masks: list[int] = []
        top_masks: list[int] = []
        bottom_masks: list[int] = []

        full_mask = 0
        sentinel_mask = 0

        for column in range(cls.COLS):
            column_mask = 0

            for bottom_row in range(cls.ROWS):
                column_mask |= cls.bit_at(
                    column,
                    bottom_row,
                )

            column_masks.append(
                column_mask
            )

            bottom_masks.append(
                cls.bit_at(
                    column,
                    0,
                )
            )

            top_masks.append(
                cls.bit_at(
                    column,
                    cls.ROWS - 1,
                )
            )

            full_mask |= column_mask

            sentinel_mask |= 1 << (
                column * cls.STRIDE
                + cls.ROWS
            )

        win_masks: list[int] = []
        win_cells: list[
            tuple[tuple[int, int], ...]
        ] = []

        def add_window(
            cells_bottom_based: list[
                tuple[int, int]
            ],
        ) -> None:
            mask = 0
            display_cells: list[
                tuple[int, int]
            ] = []

            for bottom_row, column in cells_bottom_based:
                mask |= cls.bit_at(
                    column,
                    bottom_row,
                )

                matrix_row = (
                    cls.ROWS - 1 - bottom_row
                )

                display_cells.append(
                    (
                        matrix_row,
                        column,
                    )
                )

            win_masks.append(mask)
            win_cells.append(
                tuple(display_cells)
            )

        # Horizontal windows
        for bottom_row in range(cls.ROWS):
            for column in range(
                cls.COLS - cls.CONNECT + 1
            ):
                add_window(
                    [
                        (
                            bottom_row,
                            column + offset,
                        )
                        for offset in range(
                            cls.CONNECT
                        )
                    ]
                )

        # Vertical windows
        for column in range(cls.COLS):
            for bottom_row in range(
                cls.ROWS - cls.CONNECT + 1
            ):
                add_window(
                    [
                        (
                            bottom_row + offset,
                            column,
                        )
                        for offset in range(
                            cls.CONNECT
                        )
                    ]
                )

        # Diagonal rising right
        for bottom_row in range(
            cls.ROWS - cls.CONNECT + 1
        ):
            for column in range(
                cls.COLS - cls.CONNECT + 1
            ):
                add_window(
                    [
                        (
                            bottom_row + offset,
                            column + offset,
                        )
                        for offset in range(
                            cls.CONNECT
                        )
                    ]
                )

        # Diagonal rising left
        for bottom_row in range(
            cls.ROWS - cls.CONNECT + 1
        ):
            for column in range(
                cls.CONNECT - 1,
                cls.COLS,
            ):
                add_window(
                    [
                        (
                            bottom_row + offset,
                            column - offset,
                        )
                        for offset in range(
                            cls.CONNECT
                        )
                    ]
                )

        cls.COL_MASK = tuple(
            column_masks
        )

        cls.TOP_MASK = tuple(
            top_masks
        )

        cls.BOTTOM_MASK = tuple(
            bottom_masks
        )

        cls.FULL_MASK = full_mask
        cls.SENTINEL_MASK = sentinel_mask

        cls.WIN_MASKS = tuple(
            win_masks
        )

        cls.WIN_CELLS = tuple(
            win_cells
        )

        cls._PRECOMPUTED = True

    # ------------------------------------------------------------------
    # Turn helpers
    # ------------------------------------------------------------------

    def _infer_current_player(self) -> int:
        p1_count = self.player_one_count
        p2_count = self.player_two_count

        if self._starting_player == self.PLAYER_ONE:
            if p1_count == p2_count:
                return self.PLAYER_ONE

            return self.PLAYER_TWO

        if p1_count == p2_count:
            return self.PLAYER_TWO

        return self.PLAYER_ONE

    def _last_player_from_counts(self) -> int | None:
        if self.move_count == 0:
            return None

        inferred_next = self._infer_current_player()

        return self.other_player(
            inferred_next
        )

    @classmethod
    def other_player(
        cls,
        player: int,
    ) -> int:
        player = cls._validate_player(
            player
        )

        if player == cls.PLAYER_ONE:
            return cls.PLAYER_TWO

        return cls.PLAYER_ONE

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @classmethod
    def _validate_player(
        cls,
        player: int,
    ) -> int:
        try:
            normalized = int(player)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid player value: {player!r}"
            ) from error

        if normalized not in (
            cls.PLAYER_ONE,
            cls.PLAYER_TWO,
        ):
            raise ValueError(
                f"player must be 1 or 2, got {player!r}"
            )

        return normalized

    @classmethod
    def _validate_column(
        cls,
        column: int,
    ) -> None:
        if not isinstance(column, int):
            raise TypeError(
                f"column must be int, got {type(column).__name__}"
            )

        if column < 0 or column >= cls.COLS:
            raise ValueError(
                f"column must be between 0 and {cls.COLS - 1}, "
                f"got {column}"
            )

    @classmethod
    def _validate_matrix_coordinates(
        cls,
        row: int,
        column: int,
    ) -> None:
        if not isinstance(row, int):
            raise TypeError(
                f"row must be int, got {type(row).__name__}"
            )

        cls._validate_column(column)

        if row < 0 or row >= cls.ROWS:
            raise ValueError(
                f"row must be between 0 and {cls.ROWS - 1}, "
                f"got {row}"
            )

    @staticmethod
    def _row_from_bit(
        move_bit: int,
        column: int,
    ) -> int:
        """
        Convert a move bit to a top-based matrix row.
        """
        bit_index = (
            move_bit.bit_length() - 1
        )

        bottom_row = (
            bit_index
            - column * Connect4Board.STRIDE
        )

        return (
            Connect4Board.ROWS
            - 1
            - bottom_row
        )

    # ------------------------------------------------------------------
    # Debug representation
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        symbols = {
            self.EMPTY: ".",
            self.PLAYER_ONE: "X",
            self.PLAYER_TWO: "O",
        }

        matrix = self.to_numpy()

        lines = [
            " ".join(
                symbols[int(value)]
                for value in row
            )
            for row in matrix
        ]

        lines.append(
            "0 1 2 3 4 5 6"
        )

        return "\n".join(lines)

