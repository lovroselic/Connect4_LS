# ui/screens/about_screen.py

from __future__ import annotations

import webbrowser

import pygame

from app import __version__
from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button
from ui.widgets.hyperlink import Hyperlink


class AboutScreen(BaseScreen):
    """
    Scrollable About, controls, AI information, links, and credits screen.
    """

    CONTENT_TOP = 108
    CONTENT_BOTTOM_MARGIN = 92
    SCROLL_STEP = 48

    def __init__(self, application) -> None:
        super().__init__(application)

        self.back_button = Button(
            rect=(
                0,
                0,
                THEME.small_button_width,
                THEME.small_button_height,
            ),
            text="Back",
            callback=self.application.go_back,
        )

        self.links = {
            "kaggle": Hyperlink(
                "Original Kaggle notebook",
                (
                    "https://www.kaggle.com/code/lovroselic/"
                    "connect-4-ls-fast-la-bitboard-op-book-par"
                ),
                callback=self._open_link,
            ),
            "web_game": Hyperlink(
                "Play the web version",
                (
                    "https://www.laughingskull.org/"
                    "Games/Connect4/Connect4.php"
                ),
                callback=self._open_link,
            ),
            "github": Hyperlink(
                "Connect4_LS on GitHub",
                "https://github.com/lovroselic/Connect4_LS",
                callback=self._open_link,
            ),
            "laughingskull": Hyperlink(
                "LaughingSkull",
                "https://www.laughingskull.org",
                callback=self._open_link,
            ),
            "pygame": Hyperlink(
                "Pygame",
                "https://www.pygame.org",
                callback=self._open_link,
            ),
            "numba": Hyperlink(
                "Numba",
                "https://numba.pydata.org",
                callback=self._open_link,
            ),
            "pytorch": Hyperlink(
                "PyTorch",
                "https://pytorch.org",
                callback=self._open_link,
            ),
        }

        self.panel_rect = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.scroll_offset = 0
        self.maximum_scroll = 0
        self._link_keys_drawn: set[str] = set()

        self.refresh_layout()

    # ------------------------------------------------------------------
    # Lifecycle and input
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        super().on_enter()

        self.scroll_offset = 0
        self._set_cursor(
            pygame.SYSTEM_CURSOR_ARROW
        )

    def on_exit(self) -> None:
        self._set_cursor(
            pygame.SYSTEM_CURSOR_ARROW
        )

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.application.go_back()
                return

            if event.key in (
                pygame.K_UP,
                pygame.K_PAGEUP,
            ):
                self._scroll_by(
                    -self.SCROLL_STEP
                )
                return

            if event.key in (
                pygame.K_DOWN,
                pygame.K_PAGEDOWN,
            ):
                self._scroll_by(
                    self.SCROLL_STEP
                )
                return

            if event.key == pygame.K_HOME:
                self.scroll_offset = 0
                return

            if event.key == pygame.K_END:
                self.scroll_offset = (
                    self.maximum_scroll
                )
                return

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_by(
                -event.y
                * self.SCROLL_STEP
            )
            return

        if self.back_button.handle_event(
            event
        ):
            return

        for key in self._link_keys_drawn:
            if self.links[key].handle_event(
                event
            ):
                return

    def update(
        self,
        delta_time: float,
    ) -> None:
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        self.back_button.update(
            mouse_position
        )

        any_link_hovered = False

        for key in self._link_keys_drawn:
            link = self.links[key]
            link.update(mouse_position)
            any_link_hovered = (
                any_link_hovered
                or link.hovered
            )

        self._set_cursor(
            pygame.SYSTEM_CURSOR_HAND
            if any_link_hovered
            else pygame.SYSTEM_CURSOR_ARROW
        )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        self.draw_background(
            surface,
            THEME.background_secondary,
        )

        self.draw_title(
            surface,
            "About Connect4_LS",
            y=42,
        )

        self.draw_subtitle(
            surface,
            (
                f"Version {__version__} — one board, "
                "three kinds of confidence."
            ),
            y=78,
        )

        self._draw_panel(
            surface,
            self.panel_rect,
        )

        old_clip = surface.get_clip()

        inner_clip = self.panel_rect.inflate(
            -2 * THEME.panel_padding,
            -2 * THEME.panel_padding,
        )

        surface.set_clip(
            inner_clip
        )

        self._link_keys_drawn.clear()

        content_height = self._draw_content(
            surface
        )

        surface.set_clip(
            old_clip
        )

        viewport_height = (
            inner_clip.height
        )

        self.maximum_scroll = max(
            0,
            content_height
            - viewport_height,
        )

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset,
                self.maximum_scroll,
            ),
        )

        self._draw_scroll_indicator(
            surface
        )

        self.back_button.draw(surface)

        self.draw_footer(
            surface,
            (
                "Mouse wheel or cursor arrows to scroll. "
                "External links open in your browser."
            ),
        )

    def _draw_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        pygame.draw.rect(
            surface,
            THEME.panel_background,
            rect,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            rect,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

    def _draw_content(
        self,
        surface: pygame.Surface,
    ) -> int:
        padding = THEME.panel_padding

        available_width = (
            self.panel_rect.width
            - 2 * padding
        )

        content_top = (
            self.panel_rect.top
            + padding
            - self.scroll_offset
        )

        if available_width >= 900:
            column_gap = 34
            column_width = (
                available_width
                - column_gap
            ) // 2

            left_x = (
                self.panel_rect.left
                + padding
            )

            right_x = (
                left_x
                + column_width
                + column_gap
            )

            left_bottom = (
                self._draw_project_column(
                    surface,
                    left_x,
                    content_top,
                    column_width,
                )
            )

            right_bottom = (
                self._draw_ai_column(
                    surface,
                    right_x,
                    content_top,
                    column_width,
                )
            )

            return (
                max(
                    left_bottom,
                    right_bottom,
                )
                - content_top
                + padding
            )

        x = self.panel_rect.left + padding
        width = available_width

        y = self._draw_project_column(
            surface,
            x,
            content_top,
            width,
        )

        y += 24

        y = self._draw_ai_column(
            surface,
            x,
            y,
            width,
        )

        return (
            y
            - content_top
            + padding
        )

    def _draw_project_column(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
    ) -> int:
        y = self._draw_heading(
            surface,
            "The Game",
            x,
            y,
        )

        y = self._draw_wrapped_text(
            surface,
            (
                "Connect4_LS is a desktop Connect Four game built with "
                "Python and Pygame. It supports Human vs Human, Human vs AI, "
                "and AI vs AI on the standard 6 × 7 board — because seven "
                "columns are apparently enough room for both strategy and "
                "public humiliation."
            ),
            x,
            y,
            width,
        )

        y += 10

        y = self._draw_wrapped_text(
            surface,
            (
                "The project began as a fast bitboard Lookahead script for a "
                "Kaggle competition, then escaped into JavaScript as a web "
                "game. Reinforcement learning followed, because a functioning "
                "search engine clearly was not enough trouble."
            ),
            x,
            y,
            width,
        )

        y += 8
        y = self._draw_link(
            surface,
            "kaggle",
            x,
            y,
        )

        y = self._draw_link(
            surface,
            "web_game",
            x,
            y,
        )

        y += 8

        y = self._draw_wrapped_text(
            surface,
            (
                "The DQN agent remained firmly at village-idiot level. "
                "AlphaZero showed promise, provided one was willing to wait "
                "roughly another three centuries. PPO eventually produced "
                "PPO_2004, which can hold its own against deeper Lookahead "
                "agents and occasionally behaves as though this was planned."
            ),
            x,
            y,
            width,
        )

        y += 10

        y = self._draw_wrapped_text(
            surface,
            (
                "From first bitboard to this desktop version, the whole "
                "expedition took about a year — a perfectly reasonable amount "
                "of time to drop coloured discs into seven columns."
            ),
            x,
            y,
            width,
        )

        y += 8
        y = self._draw_link(
            surface,
            "github",
            x,
            y,
        )

        y += 18

        y = self._draw_heading(
            surface,
            "Human Controls",
            x,
            y,
        )

        controls = (
            (
                "Mouse",
                "Select and play a column",
            ),
            (
                "1–7",
                "Play that column immediately",
            ),
            (
                "A / D",
                "Move selection left or right",
            ),
            (
                "Left / Right",
                "Also move selection, but with arrow keys",
            ),
            (
                "Enter / Space",
                "Play the selected column",
            ),
            (
                "R",
                "Restart, optimism fully restored",
            ),
            (
                "Esc",
                "Retreat to the previous screen",
            ),
        )

        for key, description in controls:
            y = self._draw_key_row(
                surface,
                key,
                description,
                x,
                y,
                width,
            )

        y += 14

        y = self._draw_heading(
            surface,
            "Hint",
            x,
            y,
        )

        return self._draw_wrapped_text(
            surface,
            (
                "During a human turn, Hint (LA13) asks the depth-13 "
                "Lookahead engine for a recommendation. It highlights the "
                "suggested column and reports the evaluation score without "
                "actually playing the move, preserving your right to ignore "
                "excellent advice."
            ),
            x,
            y,
            width,
        )

    def _draw_ai_column(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
    ) -> int:
        y = self._draw_heading(
            surface,
            "Players and AI",
            x,
            y,
        )

        ai_sections = (
            (
                "Human",
                (
                    "A local player armed with a mouse, keyboard, intuition, "
                    "and the traditional ability to blame the interface."
                ),
            ),
            (
                "Lookahead",
                (
                    "A depth-limited search engine accelerated with Numba. "
                    "Higher depths search farther ahead, consume more time, "
                    "and become increasingly smug about obvious moves."
                ),
            ),
            (
                "PPO",
                (
                    "A neural-network player trained with Proximal Policy "
                    "Optimization. It chooses moves from learned board "
                    "patterns rather than explicitly searching every future."
                ),
            ),
        )

        for title, description in ai_sections:
            y = self._draw_small_heading(
                surface,
                title,
                x,
                y,
            )

            y = self._draw_wrapped_text(
                surface,
                description,
                x,
                y,
                width,
            )

            y += 9

        y += 8

        y = self._draw_heading(
            surface,
            "AI Match Controls",
            x,
            y,
        )

        match_controls = (
            (
                "P",
                "Pause or resume AI vs AI",
            ),
            (
                "N / .",
                "Play one AI move while paused",
            ),
        )

        for key, description in (
            match_controls
        ):
            y = self._draw_key_row(
                surface,
                key,
                description,
                x,
                y,
                width,
            )

        y += 18

        y = self._draw_heading(
            surface,
            "Credits",
            x,
            y,
        )

        y = self._draw_bullet(
            surface,
            (
                "Design, programming, PPO training, and most questionable "
                "decisions: Lovro Selič, a.k.a. LaughingSkull"
            ),
            x,
            y,
            width,
        )

        y = self._draw_link(
            surface,
            "laughingskull",
            x + 18,
            y,
        )

        y += 6

        y = self._draw_bullet(
            surface,
            "Game framework",
            x,
            y,
            width,
        )

        y = self._draw_link(
            surface,
            "pygame",
            x + 18,
            y,
        )

        y += 6

        y = self._draw_bullet(
            surface,
            "Lookahead acceleration",
            x,
            y,
            width,
        )

        y = self._draw_link(
            surface,
            "numba",
            x + 18,
            y,
        )

        y += 6

        y = self._draw_bullet(
            surface,
            "Neural-network inference",
            x,
            y,
            width,
        )

        y = self._draw_link(
            surface,
            "pytorch",
            x + 18,
            y,
        )

        y += 14

        return self._draw_wrapped_text(
            surface,
            (
                "Yep, that's it ..."
                
            ),
            x,
            y,
            width,
            color=THEME.text_muted,
        )

    # ------------------------------------------------------------------
    # Text and link helpers
    # ------------------------------------------------------------------

    def _draw_heading(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
    ) -> int:
        font = FONTS.get(
            THEME.font_subheading,
            bold=True,
        )

        text_surface = font.render(
            text,
            True,
            THEME.text_primary,
        )

        surface.blit(
            text_surface,
            (x, y),
        )

        return (
            y
            + text_surface.get_height()
            + 9
        )

    def _draw_small_heading(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
    ) -> int:
        font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        text_surface = font.render(
            text,
            True,
            THEME.accent_hover,
        )

        surface.blit(
            text_surface,
            (x, y),
        )

        return (
            y
            + text_surface.get_height()
            + 4
        )

    def _draw_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        maximum_width: int,
        *,
        color=None,
    ) -> int:
        font = FONTS.get(
            THEME.font_small,
        )

        color = (
            THEME.text_secondary
            if color is None
            else color
        )

        words = str(text).split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            candidate = (
                word
                if not current_line
                else f"{current_line} {word}"
            )

            if (
                font.size(candidate)[0]
                <= maximum_width
            ):
                current_line = candidate
            else:
                if current_line:
                    lines.append(
                        current_line
                    )

                current_line = word

        if current_line:
            lines.append(
                current_line
            )

        line_height = (
            font.get_linesize()
        )

        for line in lines:
            line_surface = font.render(
                line,
                True,
                color,
            )

            surface.blit(
                line_surface,
                (x, y),
            )

            y += line_height

        return y

    def _draw_link(
        self,
        surface: pygame.Surface,
        key: str,
        x: int,
        y: int,
    ) -> int:
        link = self.links[key]

        link.set_position(
            x,
            y,
        )

        self._link_keys_drawn.add(
            key
        )

        link.draw(surface)

        return (
            y
            + link.rect.height
            + 6
        )

    def _draw_key_row(
        self,
        surface: pygame.Surface,
        key: str,
        description: str,
        x: int,
        y: int,
        maximum_width: int,
    ) -> int:
        key_font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        text_font = FONTS.get(
            THEME.font_small,
        )

        key_width = min(
            120,
            max(
                78,
                maximum_width // 3,
            ),
        )

        key_surface = key_font.render(
            key,
            True,
            THEME.accent_hover,
        )

        surface.blit(
            key_surface,
            (x, y),
        )

        description_width = max(
            80,
            maximum_width - key_width,
        )

        next_y = self._draw_wrapped_text(
            surface,
            description,
            x + key_width,
            y,
            description_width,
        )

        return max(
            y + key_surface.get_height(),
            next_y,
        ) + 5

    def _draw_bullet(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        maximum_width: int,
    ) -> int:
        bullet_font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        bullet_surface = (
            bullet_font.render(
                "•",
                True,
                THEME.accent_hover,
            )
        )

        surface.blit(
            bullet_surface,
            (x, y),
        )

        return (
            self._draw_wrapped_text(
                surface,
                text,
                x + 18,
                y,
                maximum_width - 18,
            )
            + 3
        )

    # ------------------------------------------------------------------
    # Commands and layout
    # ------------------------------------------------------------------

    def _open_link(
        self,
        url: str,
    ) -> None:
        try:
            self.application.audio.play_button_click()
        except Exception:
            pass

        try:
            opened = webbrowser.open(
                url,
                new=2,
            )

            if not opened:
                print(
                    "[About] Browser did not accept URL: "
                    f"{url}"
                )

        except Exception as error:
            print(
                "[About] Could not open URL "
                f"{url}: {error}"
            )

    def _scroll_by(
        self,
        amount: int,
    ) -> None:
        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset
                + int(amount),
                self.maximum_scroll,
            ),
        )

    def _draw_scroll_indicator(
        self,
        surface: pygame.Surface,
    ) -> None:
        if self.maximum_scroll <= 0:
            return

        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        if self.scroll_offset <= 0:
            text = "Scroll down for more ↓"
        elif (
            self.scroll_offset
            >= self.maximum_scroll
        ):
            text = "End of excessively documented history"
        else:
            text = text = "Scroll down for more"

        text_surface = font.render(
            text,
            True,
            THEME.text_muted,
        )

        text_rect = (
            text_surface.get_rect(
                midbottom=(
                    self.panel_rect.centerx,
                    self.panel_rect.bottom - 8,
                )
            )
        )

        pygame.draw.rect(
            surface,
            THEME.panel_background,
            text_rect.inflate(
                20,
                8,
            ),
            border_radius=6,
        )

        surface.blit(
            text_surface,
            text_rect,
        )

    @staticmethod
    def _set_cursor(
        cursor_type: int,
    ) -> None:
        try:
            pygame.mouse.set_cursor(
                pygame.cursors.Cursor(
                    cursor_type
                )
            )
        except pygame.error:
            pass

    def refresh_layout(self) -> None:
        super().refresh_layout()

        margin = THEME.screen_margin

        self.panel_rect = pygame.Rect(
            margin,
            self.CONTENT_TOP,
            self.width - 2 * margin,
            max(
                220,
                self.height
                - self.CONTENT_TOP
                - self.CONTENT_BOTTOM_MARGIN,
            ),
        )

        self.back_button.set_position(
            margin,
            self.height
            - margin
            - THEME.small_button_height,
        )

        self.scroll_offset = max(
            0,
            min(
                self.scroll_offset,
                self.maximum_scroll,
            ),
        )
