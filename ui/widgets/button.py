# ui/widgets/button.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, Optional

import pygame

from ui.theme import FONTS, THEME, Color


ButtonCallback = Callable[[], None]
ActivationSoundCallback = Callable[[], None]


@dataclass(slots=True)
class ButtonStyle:
    """
    Visual settings for a button.
    """

    background: Color
    background_hover: Color
    background_pressed: Color
    background_disabled: Color

    border: Color
    border_hover: Color

    text: Color
    text_disabled: Color

    border_width: int
    border_radius: int

    font_size: int


def default_button_style() -> ButtonStyle:
    """
    Return the standard application button style.
    """
    return ButtonStyle(
        background=THEME.button_background,
        background_hover=THEME.button_hover,
        background_pressed=THEME.button_pressed,
        background_disabled=THEME.button_disabled,
        border=THEME.button_border,
        border_hover=THEME.button_border_hover,
        text=THEME.text_primary,
        text_disabled=THEME.text_disabled,
        border_width=THEME.button_border_width,
        border_radius=THEME.button_radius,
        font_size=THEME.font_button,
    )


class Button:
    """
    Reusable Pygame button.

    A shared activation-sound callback may be registered by the application.
    """

    _activation_sound_callback: ClassVar[
        ActivationSoundCallback | None
    ] = None

    def __init__(
        self,
        rect: pygame.Rect
        | tuple[int, int, int, int],
        text: str,
        callback: Optional[
            ButtonCallback
        ] = None,
        *,
        enabled: bool = True,
        visible: bool = True,
        style: Optional[
            ButtonStyle
        ] = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.text = str(text)
        self.callback = callback

        self.enabled = bool(enabled)
        self.visible = bool(visible)

        self.style = (
            style
            or default_button_style()
        )

        self.hovered = False
        self.pressed = False

        self._pressed_inside = False
        self._last_click_time_ms = 0

    @classmethod
    def set_activation_sound_callback(
        cls,
        callback: ActivationSoundCallback
        | None,
    ) -> None:
        """
        Set the sound callback used by every Button instance.
        """
        cls._activation_sound_callback = (
            callback
        )

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> bool:
        """
        Process a Pygame event.

        Returns True when the event was consumed.
        """
        if (
            not self.visible
            or not self.enabled
        ):
            self.hovered = False
            self.pressed = False
            self._pressed_inside = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = (
                self.rect.collidepoint(
                    event.pos
                )
            )

            if (
                not self.hovered
                and self._pressed_inside
            ):
                self.pressed = False

            return self.hovered

        if (
            event.type
            == pygame.MOUSEBUTTONDOWN
        ):
            if event.button != 1:
                return False

            if self.rect.collidepoint(
                event.pos
            ):
                self.hovered = True
                self.pressed = True
                self._pressed_inside = True
                return True

            return False

        if (
            event.type
            == pygame.MOUSEBUTTONUP
        ):
            if event.button != 1:
                return False

            was_pressed_inside = (
                self._pressed_inside
            )

            self.hovered = (
                self.rect.collidepoint(
                    event.pos
                )
            )

            self.pressed = False
            self._pressed_inside = False

            if (
                was_pressed_inside
                and self.hovered
            ):
                self.activate()
                return True

            return was_pressed_inside

        return False

    def update(
        self,
        mouse_pos: tuple[int, int],
    ) -> None:
        """
        Update hover state.
        """
        if (
            not self.visible
            or not self.enabled
        ):
            self.hovered = False
            self.pressed = False
            self._pressed_inside = False
            return

        self.hovered = (
            self.rect.collidepoint(
                mouse_pos
            )
        )

    def activate(self) -> None:
        """
        Trigger the button sound and callback.
        """
        if (
            not self.visible
            or not self.enabled
        ):
            return

        self._last_click_time_ms = (
            pygame.time.get_ticks()
        )

        sound_callback = (
            type(self)
            ._activation_sound_callback
        )

        if sound_callback is not None:
            try:
                sound_callback()
            except Exception:
                pass

        if self.callback is not None:
            self.callback()

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        """
        Draw the button.
        """
        if not self.visible:
            return

        background = (
            self._current_background()
        )

        border = self._current_border()

        text_color = (
            self.style.text
            if self.enabled
            else self.style.text_disabled
        )

        pygame.draw.rect(
            surface,
            background,
            self.rect,
            border_radius=(
                self.style.border_radius
            ),
        )

        if self.style.border_width > 0:
            pygame.draw.rect(
                surface,
                border,
                self.rect,
                width=(
                    self.style.border_width
                ),
                border_radius=(
                    self.style.border_radius
                ),
            )

        font = FONTS.get(
            self.style.font_size,
            bold=True,
        )

        text_surface = font.render(
            self.text,
            True,
            text_color,
        )

        text_rect = (
            text_surface.get_rect(
                center=self.rect.center,
            )
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.enabled = bool(enabled)

        if not self.enabled:
            self.hovered = False
            self.pressed = False
            self._pressed_inside = False

    def set_visible(
        self,
        visible: bool,
    ) -> None:
        self.visible = bool(visible)

        if not self.visible:
            self.hovered = False
            self.pressed = False
            self._pressed_inside = False

    def set_text(
        self,
        text: str,
    ) -> None:
        self.text = str(text)

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

    def contains_point(
        self,
        point: tuple[int, int],
    ) -> bool:
        return (
            self.visible
            and self.rect.collidepoint(
                point
            )
        )

    def _current_background(self) -> Color:
        if not self.enabled:
            return (
                self.style
                .background_disabled
            )

        if self.pressed:
            return (
                self.style
                .background_pressed
            )

        if self.hovered:
            return (
                self.style
                .background_hover
            )

        return self.style.background

    def _current_border(self) -> Color:
        if (
            self.enabled
            and self.hovered
        ):
            return (
                self.style.border_hover
            )

        return self.style.border
