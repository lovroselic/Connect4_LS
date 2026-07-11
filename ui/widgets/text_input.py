
# ui/widgets/text_input.py

from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.theme import FONTS, THEME


TextChangeCallback = Callable[[str], None]


class TextInput:
    """
    Single-line text input widget.

    Supports mouse focus, keyboard typing, Backspace, Delete, Home, End,
    horizontal cursor movement, Enter confirmation, and a maximum length.
    """

    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        *,
        text: str = "",
        placeholder: str = "",
        on_change: TextChangeCallback | None = None,
        max_length: int = 24,
        enabled: bool = True,
        visible: bool = True,
    ) -> None:
        self.rect = pygame.Rect(rect)

        self.text = str(text)
        self.placeholder = str(placeholder)
        self.on_change = on_change

        self.max_length = max(1, int(max_length))

        self.enabled = bool(enabled)
        self.visible = bool(visible)
        self.focused = False
        self.hovered = False

        self.cursor_position = len(self.text)

        self._cursor_visible = True
        self._last_cursor_toggle_ms = pygame.time.get_ticks()
        self._cursor_blink_interval_ms = 500

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process mouse and keyboard events.

        Returns True when the event was consumed.
        """
        if not self.visible or not self.enabled:
            self.focused = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            return self.hovered

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return False

            self.set_focus(
                self.rect.collidepoint(event.pos)
            )

            return self.focused

        if event.type != pygame.KEYDOWN or not self.focused:
            return False

        if event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            self.set_focus(False)
            return True

        if event.key == pygame.K_ESCAPE:
            self.set_focus(False)
            return True

        if event.key == pygame.K_BACKSPACE:
            if self.cursor_position > 0:
                self.text = (
                    self.text[:self.cursor_position - 1]
                    + self.text[self.cursor_position:]
                )

                self.cursor_position -= 1
                self._notify_change()

            return True

        if event.key == pygame.K_DELETE:
            if self.cursor_position < len(self.text):
                self.text = (
                    self.text[:self.cursor_position]
                    + self.text[self.cursor_position + 1:]
                )

                self._notify_change()

            return True

        if event.key == pygame.K_LEFT:
            self.cursor_position = max(
                0,
                self.cursor_position - 1,
            )
            self._reset_cursor_blink()
            return True

        if event.key == pygame.K_RIGHT:
            self.cursor_position = min(
                len(self.text),
                self.cursor_position + 1,
            )
            self._reset_cursor_blink()
            return True

        if event.key == pygame.K_HOME:
            self.cursor_position = 0
            self._reset_cursor_blink()
            return True

        if event.key == pygame.K_END:
            self.cursor_position = len(self.text)
            self._reset_cursor_blink()
            return True

        if event.unicode and event.unicode.isprintable():
            if len(self.text) < self.max_length:
                self.text = (
                    self.text[:self.cursor_position]
                    + event.unicode
                    + self.text[self.cursor_position:]
                )

                self.cursor_position += len(event.unicode)
                self._notify_change()

            return True

        return False

    def update(
        self,
        mouse_pos: tuple[int, int],
    ) -> None:
        """
        Update hover state and cursor blinking.
        """
        if not self.visible or not self.enabled:
            self.hovered = False
            self.focused = False
            return

        self.hovered = self.rect.collidepoint(mouse_pos)

        now = pygame.time.get_ticks()

        if (
            self.focused
            and now - self._last_cursor_toggle_ms
            >= self._cursor_blink_interval_ms
        ):
            self._cursor_visible = not self._cursor_visible
            self._last_cursor_toggle_ms = now

        if not self.focused:
            self._cursor_visible = False

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the input field.
        """
        if not self.visible:
            return

        if not self.enabled:
            background = THEME.button_disabled
            border = THEME.button_border
            text_color = THEME.text_disabled
        elif self.focused:
            background = THEME.panel_background_hover
            border = THEME.accent_hover
            text_color = THEME.text_primary
        elif self.hovered:
            background = THEME.panel_background_hover
            border = THEME.button_border_hover
            text_color = THEME.text_primary
        else:
            background = THEME.panel_background_hover
            border = THEME.button_border
            text_color = THEME.text_primary

        pygame.draw.rect(
            surface,
            background,
            self.rect,
            border_radius=THEME.button_radius,
        )

        pygame.draw.rect(
            surface,
            border,
            self.rect,
            width=THEME.button_border_width,
            border_radius=THEME.button_radius,
        )

        font = FONTS.get(
            THEME.font_body,
        )

        display_text = self.text
        display_color = text_color

        if not display_text and not self.focused:
            display_text = self.placeholder
            display_color = THEME.text_muted

        text_surface = font.render(
            display_text,
            True,
            display_color,
        )

        text_rect = text_surface.get_rect(
            midleft=(
                self.rect.left + 14,
                self.rect.centery,
            )
        )

        clip_rect = pygame.Rect(
            self.rect.left + 12,
            self.rect.top + 4,
            self.rect.width - 24,
            self.rect.height - 8,
        )

        previous_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        surface.blit(
            text_surface,
            text_rect,
        )

        if (
            self.focused
            and self._cursor_visible
        ):
            prefix_surface = font.render(
                self.text[:self.cursor_position],
                True,
                text_color,
            )

            cursor_x = (
                self.rect.left
                + 14
                + prefix_surface.get_width()
            )

            cursor_top = (
                self.rect.centery
                - font.get_height() // 2
            )

            pygame.draw.line(
                surface,
                THEME.text_primary,
                (cursor_x, cursor_top),
                (
                    cursor_x,
                    cursor_top + font.get_height(),
                ),
                width=2,
            )

        surface.set_clip(previous_clip)

    def set_text(
        self,
        text: str,
        *,
        notify: bool = True,
    ) -> None:
        """
        Replace the current text.
        """
        self.text = str(text)[:self.max_length]
        self.cursor_position = len(self.text)

        if notify:
            self._notify_change()

    def set_focus(
        self,
        focused: bool,
    ) -> None:
        """
        Change keyboard focus.
        """
        self.focused = bool(
            focused
            and self.enabled
            and self.visible
        )

        self._reset_cursor_blink()

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.enabled = bool(enabled)

        if not self.enabled:
            self.focused = False

    def set_visible(
        self,
        visible: bool,
    ) -> None:
        self.visible = bool(visible)

        if not self.visible:
            self.focused = False

    def set_rect(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
    ) -> None:
        self.rect = pygame.Rect(rect)

    def set_position(
        self,
        x: int,
        y: int,
    ) -> None:
        self.rect.topleft = (
            int(x),
            int(y),
        )

    def set_center(
        self,
        x: int,
        y: int,
    ) -> None:
        self.rect.center = (
            int(x),
            int(y),
        )

    def set_size(
        self,
        width: int,
        height: int,
    ) -> None:
        self.rect.size = (
            max(1, int(width)),
            max(1, int(height)),
        )

    def _notify_change(self) -> None:
        self._reset_cursor_blink()

        if self.on_change is not None:
            self.on_change(self.text)

    def _reset_cursor_blink(self) -> None:
        self._cursor_visible = True
        self._last_cursor_toggle_ms = pygame.time.get_ticks()

