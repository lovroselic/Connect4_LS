# ui/screens/base_screen.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from ui.theme import FONTS, THEME

if TYPE_CHECKING:
    from app.application import Application


class BaseScreen(ABC):
    """
    Base class for all application screens.

    A screen does not own the main loop. It receives events, updates its
    controls, and draws itself through the Application object.
    """

    def __init__(self, application: "Application") -> None:
        self.application = application
        self.screen = application.screen
        self.config = application.config
        self.state = application.state

        self.width, self.height = self.screen.get_size()

    def on_enter(self) -> None:
        """
        Called whenever this screen becomes active.
        """
        self.refresh_layout()

    def on_exit(self) -> None:
        """
        Called before this screen stops being active.
        """
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Process one Pygame event.

        Derived screens may override this method, but should normally call
        super().handle_event(event) so shared keyboard behaviour remains active.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()

    def update(self, delta_time: float) -> None:
        """
        Update screen state.

        Parameters
        ----------
        delta_time:
            Elapsed time since the previous frame, in seconds.
        """
        del delta_time

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the complete screen.
        """
        raise NotImplementedError

    def handle_escape(self) -> None:
        """
        Default Escape behaviour.
    
        Return to the previous screen through the Application so the active
        screen object and AppState remain synchronized.
        """
        self.application.go_back()

    def refresh_layout(self) -> None:
        """
        Refresh cached dimensions after the window size changes.

        Derived screens should override this method to reposition their
        controls, while still calling super().refresh_layout().
        """
        self.width, self.height = self.screen.get_size()

    def draw_background(
        self,
        surface: pygame.Surface,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        """
        Fill the screen with the standard background colour.
        """
        surface.fill(color or THEME.background)

    def draw_title(
        self,
        surface: pygame.Surface,
        text: str,
        *,
        y: int = 90,
    ) -> pygame.Rect:
        """
        Draw a centered screen title.

        Returns
        -------
        pygame.Rect
            Rectangle occupied by the rendered title.
        """
        font = FONTS.get(
            THEME.font_title,
            bold=True,
        )

        text_surface = font.render(
            str(text),
            True,
            THEME.text_primary,
        )

        text_rect = text_surface.get_rect(
            center=(self.width // 2, int(y)),
        )

        surface.blit(text_surface, text_rect)
        return text_rect

    def draw_subtitle(
        self,
        surface: pygame.Surface,
        text: str,
        *,
        y: int,
    ) -> pygame.Rect:
        """
        Draw centered secondary text.
        """
        font = FONTS.get(THEME.font_body)

        text_surface = font.render(
            str(text),
            True,
            THEME.text_secondary,
        )

        text_rect = text_surface.get_rect(
            center=(self.width // 2, int(y)),
        )

        surface.blit(text_surface, text_rect)
        return text_rect

    def draw_footer(
        self,
        surface: pygame.Surface,
        text: str,
    ) -> pygame.Rect:
        """
        Draw muted text near the bottom of the window.
        """
        font = FONTS.get(THEME.font_small)

        text_surface = font.render(
            str(text),
            True,
            THEME.text_muted,
        )

        text_rect = text_surface.get_rect(
            center=(
                self.width // 2,
                self.height - THEME.screen_margin,
            )
        )

        surface.blit(text_surface, text_rect)
        return text_rect
