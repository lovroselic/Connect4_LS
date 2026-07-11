# ui/widgets/selector.py

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

import pygame

from ui.theme import FONTS, THEME
from ui.widgets.button import Button, ButtonStyle, default_button_style


T = TypeVar("T")

SelectorCallback = Callable[[T], None]
LabelFormatter = Callable[[T], str]


class Selector(Generic[T]):
    """
    A horizontal selector with previous and next arrow buttons.

    The selector cycles through a fixed sequence of values and displays the
    currently selected value in the center.
    """

    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        options: Sequence[T],
        *,
        selected_index: int = 0,
        on_change: SelectorCallback[T] | None = None,
        formatter: LabelFormatter[T] | None = None,
        enabled: bool = True,
        visible: bool = True,
        wrap: bool = True,
    ) -> None:
        if not options:
            raise ValueError("Selector requires at least one option.")

        self.rect = pygame.Rect(rect)
        self.options = list(options)

        self.on_change = on_change
        self.formatter = formatter or str

        self.enabled = bool(enabled)
        self.visible = bool(visible)
        self.wrap = bool(wrap)

        self._selected_index = self._normalize_index(selected_index)

        arrow_style = self._create_arrow_style()

        self.previous_button = Button(
            rect=(0, 0, 1, 1),
            text="<",
            callback=self.select_previous,
            enabled=self.enabled,
            visible=self.visible,
            style=arrow_style,
        )

        self.next_button = Button(
            rect=(0, 0, 1, 1),
            text=">",
            callback=self.select_next,
            enabled=self.enabled,
            visible=self.visible,
            style=arrow_style,
        )

        self._layout_buttons()

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def value(self) -> T:
        return self.options[self._selected_index]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process mouse and keyboard input.

        Returns True when the selector consumed the event.
        """
        if not self.visible or not self.enabled:
            return False

        if self.previous_button.handle_event(event):
            return True

        if self.next_button.handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.select_previous()
                return True

            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.select_next()
                return True

        return False

    def update(self, mouse_pos: tuple[int, int]) -> None:
        """
        Update hover states.
        """
        if not self.visible:
            return

        self.previous_button.update(mouse_pos)
        self.next_button.update(mouse_pos)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the selector and the current value.
        """
        if not self.visible:
            return

        pygame.draw.rect(
            surface,
            THEME.panel_background_hover,
            self.rect,
            border_radius=THEME.button_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.button_border,
            self.rect,
            width=THEME.button_border_width,
            border_radius=THEME.button_radius,
        )

        self.previous_button.draw(surface)
        self.next_button.draw(surface)

        text_color = (
            THEME.text_primary
            if self.enabled
            else THEME.text_disabled
        )

        font = FONTS.get(
            THEME.font_button,
            bold=True,
        )

        value_surface = font.render(
            self.formatter(self.value),
            True,
            text_color,
        )

        value_rect = value_surface.get_rect(
            center=self.rect.center,
        )

        surface.blit(
            value_surface,
            value_rect,
        )

    def select_previous(self) -> None:
        """
        Select the previous option.
        """
        self._select_relative(-1)

    def select_next(self) -> None:
        """
        Select the next option.
        """
        self._select_relative(1)

    def set_index(
        self,
        index: int,
        *,
        notify: bool = True,
    ) -> None:
        """
        Select an option by index.
        """
        new_index = self._normalize_index(index)

        if new_index == self._selected_index:
            return

        self._selected_index = new_index

        if notify and self.on_change is not None:
            self.on_change(self.value)

    def set_value(
        self,
        value: T,
        *,
        notify: bool = True,
    ) -> None:
        """
        Select the first matching option value.
        """
        try:
            index = self.options.index(value)
        except ValueError as error:
            raise ValueError(
                f"Value is not present in selector options: {value!r}"
            ) from error

        self.set_index(
            index,
            notify=notify,
        )

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the selector.
        """
        self.enabled = bool(enabled)

        self.previous_button.set_enabled(self.enabled)
        self.next_button.set_enabled(self.enabled)

    def set_visible(self, visible: bool) -> None:
        """
        Show or hide the selector.
        """
        self.visible = bool(visible)

        self.previous_button.set_visible(self.visible)
        self.next_button.set_visible(self.visible)

    def set_rect(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
    ) -> None:
        """
        Replace the selector rectangle and update button positions.
        """
        self.rect = pygame.Rect(rect)
        self._layout_buttons()

    def set_position(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        Move the selector while preserving its size.
        """
        self.rect.topleft = (
            int(x),
            int(y),
        )

        self._layout_buttons()

    def set_center(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        Center the selector at the supplied position.
        """
        self.rect.center = (
            int(x),
            int(y),
        )

        self._layout_buttons()

    def set_size(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Resize the selector while preserving its top-left position.
        """
        self.rect.size = (
            max(1, int(width)),
            max(1, int(height)),
        )

        self._layout_buttons()

    def _select_relative(self, offset: int) -> None:
        if not self.enabled or not self.visible:
            return

        candidate = self._selected_index + int(offset)

        if self.wrap:
            candidate %= len(self.options)
        else:
            candidate = max(
                0,
                min(candidate, len(self.options) - 1),
            )

        self.set_index(candidate)

    def _normalize_index(self, index: int) -> int:
        try:
            normalized = int(index)
        except (TypeError, ValueError):
            normalized = 0

        if self.wrap:
            return normalized % len(self.options)

        return max(
            0,
            min(normalized, len(self.options) - 1),
        )

    def _layout_buttons(self) -> None:
        arrow_width = max(
            44,
            min(self.rect.height, 58),
        )

        self.previous_button.rect = pygame.Rect(
            self.rect.left,
            self.rect.top,
            arrow_width,
            self.rect.height,
        )

        self.next_button.rect = pygame.Rect(
            self.rect.right - arrow_width,
            self.rect.top,
            arrow_width,
            self.rect.height,
        )

    @staticmethod
    def _create_arrow_style() -> ButtonStyle:
        style = default_button_style()

        return ButtonStyle(
            background=style.background,
            background_hover=style.background_hover,
            background_pressed=style.background_pressed,
            background_disabled=style.background_disabled,
            border=style.border,
            border_hover=style.border_hover,
            text=style.text,
            text_disabled=style.text_disabled,
            border_width=0,
            border_radius=style.border_radius,
            font_size=style.font_size,
        )
