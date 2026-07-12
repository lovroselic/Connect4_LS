# ui/widgets/hyperlink.py

from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.theme import FONTS, THEME


LinkCallback = Callable[[str], None]


class Hyperlink:
    """
    Reusable clickable text link for Pygame screens.
    """

    def __init__(
        self,
        text: str,
        url: str,
        *,
        callback: LinkCallback | None = None,
        font_size: int | None = None,
    ) -> None:
        self.text = str(text)
        self.url = str(url)
        self.callback = callback

        self.font_size = (
            THEME.font_small
            if font_size is None
            else int(font_size)
        )

        self.rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.visible = True
        self.enabled = True
        self.hovered = False

    def set_position(
        self,
        x: int,
        y: int,
    ) -> None:
        font = FONTS.get(
            self.font_size,
            bold=True,
        )

        width, height = font.size(
            self.text
        )

        self.rect = pygame.Rect(
            int(x),
            int(y),
            width,
            height,
        )

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> bool:
        if (
            not self.visible
            or not self.enabled
        ):
            self.hovered = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = (
                self.rect.collidepoint(
                    event.pos
                )
            )

            return self.hovered

        if (
            event.type
            == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.rect.collidepoint(
                event.pos
            )
        ):
            self.activate()
            return True

        return False

    def update(
        self,
        mouse_position: tuple[int, int],
    ) -> None:
        if (
            not self.visible
            or not self.enabled
        ):
            self.hovered = False
            return

        self.hovered = (
            self.rect.collidepoint(
                mouse_position
            )
        )

    def activate(self) -> None:
        if (
            not self.visible
            or not self.enabled
        ):
            return

        if self.callback is not None:
            self.callback(
                self.url
            )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        if not self.visible:
            return

        font = FONTS.get(
            self.font_size,
            bold=True,
        )

        color = (
            THEME.accent_hover
            if self.enabled
            else THEME.text_disabled
        )

        text_surface = font.render(
            self.text,
            True,
            color,
        )

        surface.blit(
            text_surface,
            self.rect,
        )

        if self.hovered:
            underline_y = (
                self.rect.bottom - 1
            )

            pygame.draw.line(
                surface,
                color,
                (
                    self.rect.left,
                    underline_y,
                ),
                (
                    self.rect.right,
                    underline_y,
                ),
                width=1,
            )
