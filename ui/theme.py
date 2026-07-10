# ui/theme.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pygame


Color = tuple[int, int, int]
ColorAlpha = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class Theme:
    """
    Visual constants used throughout the Connect4_LS interface.

    The class is immutable so UI code cannot accidentally alter the global
    theme while rendering a screen.
    """

    # ------------------------------------------------------------
    # Application background
    # ------------------------------------------------------------

    background: Color = (18, 22, 32)
    background_secondary: Color = (26, 32, 46)

    panel_background: Color = (34, 41, 58)
    panel_background_hover: Color = (42, 50, 69)
    panel_border: Color = (75, 87, 112)

    overlay: ColorAlpha = (0, 0, 0, 170)

    # ------------------------------------------------------------
    # Text
    # ------------------------------------------------------------

    text_primary: Color = (240, 243, 248)
    text_secondary: Color = (172, 182, 201)
    text_muted: Color = (118, 128, 149)

    text_dark: Color = (22, 26, 35)
    text_disabled: Color = (105, 112, 128)

    # ------------------------------------------------------------
    # Accent colours
    # ------------------------------------------------------------

    accent: Color = (68, 145, 235)
    accent_hover: Color = (88, 165, 255)
    accent_pressed: Color = (49, 117, 204)

    success: Color = (74, 184, 116)
    warning: Color = (232, 174, 72)
    danger: Color = (218, 78, 89)

    # ------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------

    button_background: Color = (53, 63, 84)
    button_hover: Color = (67, 80, 106)
    button_pressed: Color = (43, 52, 70)
    button_disabled: Color = (42, 47, 58)

    button_border: Color = (91, 105, 135)
    button_border_hover: Color = (120, 151, 196)

    # ------------------------------------------------------------
    # Connect Four colours
    # ------------------------------------------------------------

    board_background: Color = (39, 94, 181)
    board_border: Color = (25, 65, 132)
    board_slot: Color = (16, 20, 29)

    player_one: Color = (226, 67, 67)
    player_one_highlight: Color = (255, 105, 96)

    player_two: Color = (241, 198, 61)
    player_two_highlight: Color = (255, 224, 105)

    winning_marker: Color = (113, 238, 164)

    # ------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------

    screen_margin: int = 32
    section_spacing: int = 24
    widget_spacing: int = 14

    panel_padding: int = 24
    panel_border_width: int = 2
    panel_radius: int = 12

    button_width: int = 300
    button_height: int = 58
    button_radius: int = 10
    button_border_width: int = 2

    small_button_width: int = 180
    small_button_height: int = 46

    # ------------------------------------------------------------
    # Font sizes
    # ------------------------------------------------------------

    font_title: int = 54
    font_heading: int = 34
    font_subheading: int = 25
    font_body: int = 20
    font_button: int = 23
    font_small: int = 16

    # ------------------------------------------------------------
    # Animation timing
    # ------------------------------------------------------------

    button_press_duration_ms: int = 100
    screen_fade_duration_ms: int = 180


THEME: Final[Theme] = Theme()


class FontCache:
    """
    Lazily creates and caches Pygame font objects.

    Pygame font creation is not expensive enough to be dramatic, but there is
    no reason to recreate the same font every frame.
    """

    def __init__(self, font_name: str | None = None) -> None:
        self.font_name = font_name
        self._fonts: dict[tuple[int, bool, bool], pygame.font.Font] = {}

    def get(
        self,
        size: int,
        *,
        bold: bool = False,
        italic: bool = False,
    ) -> pygame.font.Font:
        """
        Return a cached font with the requested properties.
        """
        key = (int(size), bool(bold), bool(italic))

        if key not in self._fonts:
            font = pygame.font.Font(self.font_name, key[0])
            font.set_bold(key[1])
            font.set_italic(key[2])
            self._fonts[key] = font

        return self._fonts[key]

    def clear(self) -> None:
        """
        Remove all cached font objects.
        """
        self._fonts.clear()


FONTS: Final[FontCache] = FontCache()


def brighten(color: Color, amount: int = 20) -> Color:
    """
    Return a brighter RGB colour.

    Parameters
    ----------
    color:
        Source RGB colour.

    amount:
        Value added to each channel.
    """
    return tuple(
        min(255, channel + int(amount))
        for channel in color
    )


def darken(color: Color, amount: int = 20) -> Color:
    """
    Return a darker RGB colour.

    Parameters
    ----------
    color:
        Source RGB colour.

    amount:
        Value removed from each channel.
    """
    return tuple(
        max(0, channel - int(amount))
        for channel in color
    )


def with_alpha(color: Color, alpha: int) -> ColorAlpha:
    """
    Convert an RGB colour into an RGBA colour.
    """
    return (
        color[0],
        color[1],
        color[2],
        max(0, min(int(alpha), 255)),
    )

