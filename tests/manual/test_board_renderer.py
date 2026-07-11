
# tests/manual/test_board_renderer.py

from __future__ import annotations

import pygame

from game import Connect4Board
from rendering import BoardRenderer
from ui.theme import FONTS, THEME


WINDOW_SIZE = (1000, 800)
TARGET_FPS = 60


def main() -> None:
    pygame.init()

    try:
        screen = pygame.display.set_mode(
            WINDOW_SIZE,
            pygame.RESIZABLE,
        )

        pygame.display.set_caption(
            "Connect4_LS - Board Renderer Test"
        )

        clock = pygame.time.Clock()

        board = Connect4Board()
        renderer = BoardRenderer()

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_r:
                        board.reset()

                    elif event.key == pygame.K_u:
                        board.undo()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        column = renderer.column_at(
                            event.pos
                        )

                        if (
                            column is not None
                            and board.can_play(column)
                        ):
                            board.play(column)

            width, height = screen.get_size()

            board_area = pygame.Rect(
                80,
                100,
                width - 160,
                height - 220,
            )

            renderer.set_area(board_area)

            renderer.update_hover(
                pygame.mouse.get_pos(),
                board,
                interactive=not board.is_terminal,
            )

            screen.fill(
                THEME.background
            )

            title_font = FONTS.get(
                THEME.font_heading,
                bold=True,
            )

            title = title_font.render(
                "Board Renderer Test",
                True,
                THEME.text_primary,
            )

            title_rect = title.get_rect(
                center=(
                    width // 2,
                    45,
                )
            )

            screen.blit(
                title,
                title_rect,
            )

            renderer.draw(
                screen,
                board,
                preview_player=board.current_player,
                show_column_numbers=True,
            )

            info_font = FONTS.get(
                THEME.font_body,
            )

            if board.winner is not None:
                status_text = (
                    f"Player {board.winner} wins"
                )
            elif board.is_draw:
                status_text = "Draw"
            else:
                status_text = (
                    f"Player {board.current_player}'s turn"
                )

            status_surface = info_font.render(
                status_text,
                True,
                THEME.text_secondary,
            )

            status_rect = status_surface.get_rect(
                center=(
                    width // 2,
                    height - 58,
                )
            )

            screen.blit(
                status_surface,
                status_rect,
            )

            help_font = FONTS.get(
                THEME.font_small,
            )

            help_surface = help_font.render(
                "Click a column to play · U = undo · R = reset · Esc = exit",
                True,
                THEME.text_muted,
            )

            help_rect = help_surface.get_rect(
                center=(
                    width // 2,
                    height - 28,
                )
            )

            screen.blit(
                help_surface,
                help_rect,
            )

            pygame.display.flip()
            clock.tick(TARGET_FPS)

    finally:
        pygame.quit()


if __name__ == "__main__":
    main()

