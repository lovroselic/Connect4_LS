
# rendering/board_renderer.py

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game import Connect4Board
from ui.theme import FONTS, THEME


@dataclass(frozen=True, slots=True)
class BoardLayout:
    """
    Calculated board geometry for one frame.
    """

    board_rect: pygame.Rect
    cell_size: int
    disc_radius: int
    column_rects: tuple[pygame.Rect, ...]


class BoardRenderer:
    """
    Draw a Connect Four board and translate mouse positions to columns.

    The renderer owns no game state. It only draws a supplied Connect4Board.
    """

    BOARD_PADDING_CELLS = 0.18
    DISC_RADIUS_FACTOR = 0.39
    PREVIEW_ALPHA = 150

    def __init__(self) -> None:
        self.layout = BoardLayout(
            board_rect=pygame.Rect(0, 0, 1, 1),
            cell_size=1,
            disc_radius=1,
            column_rects=tuple(
                pygame.Rect(0, 0, 1, 1)
                for _ in range(Connect4Board.COLS)
            ),
        )

        self.hovered_column: int | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def set_area(
        self,
        area: pygame.Rect | tuple[int, int, int, int],
    ) -> None:
        """
        Fit the board inside the supplied area while preserving its 7:6 ratio.
        """
        available = pygame.Rect(area)

        cell_size = min(
            available.width // Connect4Board.COLS,
            available.height // Connect4Board.ROWS,
        )

        cell_size = max(1, int(cell_size))

        board_width = cell_size * Connect4Board.COLS
        board_height = cell_size * Connect4Board.ROWS

        board_rect = pygame.Rect(
            0,
            0,
            board_width,
            board_height,
        )

        board_rect.center = available.center

        column_rects = tuple(
            pygame.Rect(
                board_rect.left + column * cell_size,
                board_rect.top,
                cell_size,
                board_rect.height,
            )
            for column in range(Connect4Board.COLS)
        )

        self.layout = BoardLayout(
            board_rect=board_rect,
            cell_size=cell_size,
            disc_radius=max(
                2,
                int(cell_size * self.DISC_RADIUS_FACTOR),
            ),
            column_rects=column_rects,
        )

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def update_hover(
        self,
        mouse_position: tuple[int, int],
        board: Connect4Board,
        *,
        interactive: bool = True,
    ) -> int | None:
        """
        Update and return the hovered legal column.
        """
        if not interactive or board.is_terminal:
            self.hovered_column = None
            return None

        column = self.column_at(mouse_position)

        if column is None or not board.can_play(column):
            self.hovered_column = None
        else:
            self.hovered_column = column

        return self.hovered_column

    def column_at(
        self,
        position: tuple[int, int],
    ) -> int | None:
        """
        Return the board column at a screen position.
        """
        if not self.layout.board_rect.collidepoint(position):
            return None

        relative_x = (
            position[0]
            - self.layout.board_rect.left
        )

        column = (
            relative_x
            // self.layout.cell_size
        )

        if 0 <= column < Connect4Board.COLS:
            return int(column)

        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
        board: Connect4Board,
        *,
        preview_player: int | None = None,
        show_column_numbers: bool = True,
    ) -> None:
        """
        Draw the board, pieces, winning highlight and optional hover preview.
        """
        self._draw_shadow(surface)
        self._draw_board_body(surface)
        self._draw_cells(surface, board)

        if (
            preview_player is not None
            and self.hovered_column is not None
            and board.can_play(self.hovered_column)
        ):
            self._draw_preview(
                surface,
                board,
                preview_player,
                self.hovered_column,
            )

        if board.winner is not None:
            self._draw_winning_cells(
                surface,
                board,
            )

        if show_column_numbers:
            self._draw_column_numbers(surface)

    def _draw_shadow(
        self,
        surface: pygame.Surface,
    ) -> None:
        shadow_rect = self.layout.board_rect.move(
            8,
            10,
        )

        pygame.draw.rect(
            surface,
            THEME.shadow,
            shadow_rect,
            border_radius=max(
                8,
                self.layout.cell_size // 5,
            ),
        )

    def _draw_board_body(
        self,
        surface: pygame.Surface,
    ) -> None:
        pygame.draw.rect(
            surface,
            THEME.board_background,
            self.layout.board_rect,
            border_radius=max(
                8,
                self.layout.cell_size // 5,
            ),
        )

        pygame.draw.rect(
            surface,
            THEME.board_border,
            self.layout.board_rect,
            width=max(
                2,
                self.layout.cell_size // 24,
            ),
            border_radius=max(
                8,
                self.layout.cell_size // 5,
            ),
        )

    def _draw_cells(
        self,
        surface: pygame.Surface,
        board: Connect4Board,
    ) -> None:
        for row in range(Connect4Board.ROWS):
            for column in range(Connect4Board.COLS):
                center = self.cell_center(
                    row,
                    column,
                )

                value = board.get_cell(
                    row,
                    column,
                )

                color = self._piece_color(value)

                pygame.draw.circle(
                    surface,
                    THEME.board_hole_shadow,
                    (
                        center[0] + 2,
                        center[1] + 3,
                    ),
                    self.layout.disc_radius,
                )

                pygame.draw.circle(
                    surface,
                    color,
                    center,
                    self.layout.disc_radius,
                )

                pygame.draw.circle(
                    surface,
                    THEME.board_cell_border,
                    center,
                    self.layout.disc_radius,
                    width=max(
                        1,
                        self.layout.cell_size // 28,
                    ),
                )

                if value != Connect4Board.EMPTY:
                    self._draw_disc_highlight(
                        surface,
                        center,
                    )

    def _draw_disc_highlight(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
    ) -> None:
        radius = max(
            2,
            self.layout.disc_radius // 4,
        )

        offset = max(
            2,
            self.layout.disc_radius // 3,
        )

        highlight_surface = pygame.Surface(
            (
                radius * 2,
                radius * 2,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            highlight_surface,
            (255, 255, 255, 55),
            (
                radius,
                radius,
            ),
            radius,
        )

        surface.blit(
            highlight_surface,
            (
                center[0] - offset - radius,
                center[1] - offset - radius,
            ),
        )

    def _draw_preview(
        self,
        surface: pygame.Surface,
        board: Connect4Board,
        player: int,
        column: int,
    ) -> None:
        height = board.column_height(column)

        if height >= Connect4Board.ROWS:
            return

        matrix_row = (
            Connect4Board.ROWS
            - 1
            - height
        )

        center = self.cell_center(
            matrix_row,
            column,
        )

        preview_surface = pygame.Surface(
            (
                self.layout.disc_radius * 2 + 4,
                self.layout.disc_radius * 2 + 4,
            ),
            pygame.SRCALPHA,
        )

        color = self._piece_color(player)

        pygame.draw.circle(
            preview_surface,
            (
                color[0],
                color[1],
                color[2],
                self.PREVIEW_ALPHA,
            ),
            (
                preview_surface.get_width() // 2,
                preview_surface.get_height() // 2,
            ),
            self.layout.disc_radius,
        )

        preview_rect = preview_surface.get_rect(
            center=center,
        )

        surface.blit(
            preview_surface,
            preview_rect,
        )

    def _draw_winning_cells(
        self,
        surface: pygame.Surface,
        board: Connect4Board,
    ) -> None:
        winning_cells = board.winning_cells()

        if not winning_cells:
            return

        pulse = (
            pygame.time.get_ticks()
            // 300
        ) % 2

        width = max(
            3,
            self.layout.cell_size // 18,
        )

        radius = (
            self.layout.disc_radius
            + 4
            + pulse * 2
        )

        for row, column in winning_cells:
            pygame.draw.circle(
                surface,
                THEME.win_highlight,
                self.cell_center(row, column),
                radius,
                width=width,
            )

    def _draw_column_numbers(
        self,
        surface: pygame.Surface,
    ) -> None:
        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        y = (
            self.layout.board_rect.bottom
            + max(
                12,
                self.layout.cell_size // 5,
            )
        )

        for column in range(Connect4Board.COLS):
            text_surface = font.render(
                str(column + 1),
                True,
                THEME.text_muted,
            )

            text_rect = text_surface.get_rect(
                center=(
                    self.layout.column_rects[column].centerx,
                    y,
                )
            )

            surface.blit(
                text_surface,
                text_rect,
            )

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def cell_center(
        self,
        row: int,
        column: int,
    ) -> tuple[int, int]:
        """
        Return the center point of a top-based board cell.
        """
        return (
            self.layout.board_rect.left
            + column * self.layout.cell_size
            + self.layout.cell_size // 2,
            self.layout.board_rect.top
            + row * self.layout.cell_size
            + self.layout.cell_size // 2,
        )

    @staticmethod
    def _piece_color(
        value: int,
    ) -> tuple[int, int, int]:
        if value == Connect4Board.PLAYER_ONE:
            return THEME.player_one

        if value == Connect4Board.PLAYER_TWO:
            return THEME.player_two

        return THEME.board_hole

