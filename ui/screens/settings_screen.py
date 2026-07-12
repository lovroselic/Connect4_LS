# ui/screens/settings_screen.py

from __future__ import annotations

from dataclasses import replace

import pygame

from app.config import AppConfig
from ui.screens.base_screen import BaseScreen
from ui.theme import FONTS, THEME
from ui.widgets.button import Button
from ui.widgets.selector import Selector


class SettingsScreen(BaseScreen):
    """
    Interactive application settings screen.

    Selector changes are held in a draft configuration until Apply & Save is
    pressed.
    """

    RESOLUTIONS = (
        (800, 600),
        (1024, 720),
        (1280, 720),
        (1280, 800),
        (1366, 768),
        (1600, 900),
        (1920, 1080),
        (2560, 1440),
    )

    BOOLEAN_OPTIONS = (
        False,
        True,
    )

    FPS_OPTIONS = (
        30,
        60,
        75,
        90,
        120,
        144,
        165,
        240,
    )

    ANIMATION_SPEED_OPTIONS = (
        0.5,
        0.75,
        1.0,
        1.25,
        1.5,
        2.0,
    )

    AI_DELAY_OPTIONS = (
        0,
        100,
        200,
        300,
        500,
        750,
        1000,
        1500,
    )

    VOLUME_OPTIONS = tuple(
        value / 10
        for value in range(0, 11)
    )

    def __init__(self, application) -> None:
        super().__init__(application)

        self.draft_config = replace(
            self.config
        )

        self.resolution_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.RESOLUTIONS,
            formatter=self._format_resolution,
        )

        self.fullscreen_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.BOOLEAN_OPTIONS,
            formatter=self._format_enabled,
        )

        self.fps_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.FPS_OPTIONS,
            formatter=lambda value: (
                f"{value} FPS"
            ),
        )

        self.analysis_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.BOOLEAN_OPTIONS,
            formatter=self._format_enabled,
        )

        self.test_menu_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.BOOLEAN_OPTIONS,
            formatter=self._format_enabled,
        )

        self.animation_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.ANIMATION_SPEED_OPTIONS,
            formatter=lambda value: (
                f"{value:.2f}×"
            ),
        )

        self.ai_delay_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.AI_DELAY_OPTIONS,
            formatter=lambda value: (
                f"{value} ms"
            ),
        )

        self.sound_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.BOOLEAN_OPTIONS,
            formatter=self._format_enabled,
        )

        self.volume_selector = Selector(
            rect=(0, 0, 260, 44),
            options=self.VOLUME_OPTIONS,
            formatter=lambda value: (
                f"{round(value * 100):d}%"
            ),
        )

        self.setting_rows = [
            (
                "Resolution",
                self.resolution_selector,
            ),
            (
                "Fullscreen",
                self.fullscreen_selector,
            ),
            (
                "Target FPS",
                self.fps_selector,
            ),
            (
                "Analysis panel",
                self.analysis_selector,
            ),
            (
                "Test menu",
                self.test_menu_selector,
            ),
            (
                "Animation speed",
                self.animation_selector,
            ),
            (
                "AI move delay",
                self.ai_delay_selector,
            ),
            (
                "Sound",
                self.sound_selector,
            ),
            (
                "Master volume",
                self.volume_selector,
            ),
        ]

        self.apply_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Apply & Save",
            callback=self._apply_and_save,
        )

        self.defaults_button = Button(
            rect=(
                0,
                0,
                THEME.button_width,
                THEME.button_height,
            ),
            text="Restore Defaults",
            callback=self._restore_defaults,
        )

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

        self.buttons = [
            self.apply_button,
            self.defaults_button,
            self.back_button,
        ]

        self.selectors = [
            selector
            for _, selector
            in self.setting_rows
        ]

        self.settings_panel = pygame.Rect(
            0,
            0,
            0,
            0,
        )

        self.status_text = ""
        self.status_is_error = False

        self._load_selectors_from_config(
            self.draft_config
        )

        self.refresh_layout()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        super().on_enter()

        self.draft_config = replace(
            self.config
        )

        self._load_selectors_from_config(
            self.draft_config
        )

        self.status_text = ""
        self.status_is_error = False

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.application.go_back()
                return

            if event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self._apply_and_save()
                return

        for button in self.buttons:
            if button.handle_event(event):
                return

        for selector in self.selectors:
            if selector.handle_event(event):
                return

    def update(
        self,
        delta_time: float,
    ) -> None:
        del delta_time

        mouse_position = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(
                mouse_position
            )

        for selector in self.selectors:
            selector.update(
                mouse_position
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
            "Settings",
            y=42,
        )

        self.draw_subtitle(
            surface,
            "Configure the application, then apply and save.",
            y=82,
        )

        self._draw_settings_panel(
            surface
        )

        for selector in self.selectors:
            selector.draw(surface)

        for button in self.buttons:
            button.draw(surface)

        self._draw_status(surface)

        self.draw_footer(
            surface,
            "Test Menu visibility takes effect after restarting the application.",
        )

    def _draw_settings_panel(
        self,
        surface: pygame.Surface,
    ) -> None:
        pygame.draw.rect(
            surface,
            THEME.panel_background,
            self.settings_panel,
            border_radius=THEME.panel_radius,
        )

        pygame.draw.rect(
            surface,
            THEME.panel_border,
            self.settings_panel,
            width=THEME.panel_border_width,
            border_radius=THEME.panel_radius,
        )

        label_font = FONTS.get(
            THEME.font_body,
            bold=True,
        )

        row_height = 48

        start_y = (
            self.settings_panel.top
            + THEME.panel_padding
            + 20
        )

        label_x = (
            self.settings_panel.left
            + THEME.panel_padding
        )

        for index, (
            label,
            selector,
        ) in enumerate(self.setting_rows):
            row_center_y = (
                start_y
                + index * row_height
            )

            if index > 0:
                separator_y = (
                    row_center_y
                    - row_height // 2
                )

                pygame.draw.line(
                    surface,
                    THEME.panel_border,
                    (
                        self.settings_panel.left
                        + THEME.panel_padding,
                        separator_y,
                    ),
                    (
                        self.settings_panel.right
                        - THEME.panel_padding,
                        separator_y,
                    ),
                    width=1,
                )

            label_surface = label_font.render(
                label,
                True,
                THEME.text_primary,
            )

            label_rect = (
                label_surface.get_rect(
                    midleft=(
                        label_x,
                        row_center_y,
                    )
                )
            )

            surface.blit(
                label_surface,
                label_rect,
            )

    def _draw_status(
        self,
        surface: pygame.Surface,
    ) -> None:
        if not self.status_text:
            return

        font = FONTS.get(
            THEME.font_small,
            bold=True,
        )

        color = (
            THEME.danger
            if self.status_is_error
            else THEME.success
        )

        status_surface = font.render(
            self.status_text,
            True,
            color,
        )

        status_rect = (
            status_surface.get_rect(
                center=(
                    self.width // 2,
                    self.height - 68,
                )
            )
        )

        surface.blit(
            status_surface,
            status_rect,
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def refresh_layout(self) -> None:
        super().refresh_layout()

        panel_width = min(
            760,
            self.width
            - 2 * THEME.screen_margin,
        )

        panel_height = min(
            500,
            self.height - 230,
        )

        self.settings_panel = pygame.Rect(
            0,
            0,
            panel_width,
            panel_height,
        )

        self.settings_panel.midtop = (
            self.width // 2,
            105,
        )

        selector_width = min(
            290,
            max(
                220,
                panel_width // 2 - 50,
            ),
        )

        selector_height = 40
        row_height = 48

        start_y = (
            self.settings_panel.top
            + THEME.panel_padding
            + 20
        )

        selector_x = (
            self.settings_panel.right
            - THEME.panel_padding
            - selector_width
        )

        for index, selector in enumerate(
            self.selectors
        ):
            row_center_y = (
                start_y
                + index * row_height
            )

            selector.set_rect(
                (
                    selector_x,
                    row_center_y
                    - selector_height // 2,
                    selector_width,
                    selector_height,
                )
            )

        buttons_y = (
            self.settings_panel.bottom
            + 16
        )

        button_gap = 18

        total_width = (
            self.apply_button.rect.width
            + button_gap
            + self.defaults_button.rect.width
        )

        first_button_x = (
            self.width // 2
            - total_width // 2
        )

        self.apply_button.set_position(
            first_button_x,
            buttons_y,
        )

        self.defaults_button.set_position(
            first_button_x
            + self.apply_button.rect.width
            + button_gap,
            buttons_y,
        )

        self.back_button.set_position(
            THEME.screen_margin,
            self.height
            - THEME.screen_margin
            - THEME.small_button_height,
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _apply_and_save(self) -> None:
        self._update_draft_from_selectors()

        try:
            self.application.apply_config(
                self.draft_config,
                save=True,
            )

        except Exception as error:
            self.status_text = (
                "Could not apply settings: "
                f"{error}"
            )

            self.status_is_error = True
            return

        self.draft_config = replace(
            self.config
        )

        self._load_selectors_from_config(
            self.draft_config
        )

        self.status_text = (
            "Settings applied and saved."
        )

        self.status_is_error = False

    def _restore_defaults(self) -> None:
        self.draft_config = AppConfig()

        self._load_selectors_from_config(
            self.draft_config
        )

        self.status_text = (
            "Default values loaded. "
            "Press Apply & Save to confirm."
        )

        self.status_is_error = False

    # ------------------------------------------------------------------
    # Draft synchronization
    # ------------------------------------------------------------------

    def _update_draft_from_selectors(
        self,
    ) -> None:
        width, height = (
            self.resolution_selector.value
        )

        self.draft_config.window_width = width
        self.draft_config.window_height = height

        self.draft_config.fullscreen = (
            self.fullscreen_selector.value
        )

        self.draft_config.target_fps = (
            self.fps_selector.value
        )

        self.draft_config.show_analysis_panel = (
            self.analysis_selector.value
        )

        self.draft_config.show_test_menu = (
            self.test_menu_selector.value
        )

        self.draft_config.animation_speed = (
            self.animation_selector.value
        )

        self.draft_config.ai_move_delay_ms = (
            self.ai_delay_selector.value
        )

        self.draft_config.sound_enabled = (
            self.sound_selector.value
        )

        self.draft_config.master_volume = (
            self.volume_selector.value
        )

        self.draft_config.validate()

    def _load_selectors_from_config(
        self,
        config: AppConfig,
    ) -> None:
        resolution = (
            config.window_width,
            config.window_height,
        )

        if resolution not in self.RESOLUTIONS:
            resolution = (
                self._nearest_resolution(
                    resolution
                )
            )

        self.resolution_selector.set_value(
            resolution,
            notify=False,
        )

        self.fullscreen_selector.set_value(
            bool(config.fullscreen),
            notify=False,
        )

        self.fps_selector.set_value(
            self._nearest_value(
                config.target_fps,
                self.FPS_OPTIONS,
            ),
            notify=False,
        )

        self.analysis_selector.set_value(
            bool(
                config.show_analysis_panel
            ),
            notify=False,
        )

        self.test_menu_selector.set_value(
            bool(
                config.show_test_menu
            ),
            notify=False,
        )

        self.animation_selector.set_value(
            self._nearest_value(
                config.animation_speed,
                self.ANIMATION_SPEED_OPTIONS,
            ),
            notify=False,
        )

        self.ai_delay_selector.set_value(
            self._nearest_value(
                config.ai_move_delay_ms,
                self.AI_DELAY_OPTIONS,
            ),
            notify=False,
        )

        self.sound_selector.set_value(
            bool(config.sound_enabled),
            notify=False,
        )

        self.volume_selector.set_value(
            self._nearest_value(
                config.master_volume,
                self.VOLUME_OPTIONS,
            ),
            notify=False,
        )

    # ------------------------------------------------------------------
    # Formatting and selection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_resolution(
        resolution: tuple[int, int],
    ) -> str:
        return (
            f"{resolution[0]} × "
            f"{resolution[1]}"
        )

    @staticmethod
    def _format_enabled(
        value: bool,
    ) -> str:
        return (
            "Enabled"
            if value
            else "Disabled"
        )

    @classmethod
    def _nearest_resolution(
        cls,
        resolution: tuple[int, int],
    ) -> tuple[int, int]:
        width, height = resolution

        return min(
            cls.RESOLUTIONS,
            key=lambda candidate: (
                abs(candidate[0] - width)
                + abs(candidate[1] - height)
            ),
        )

    @staticmethod
    def _nearest_value(
        value,
        options,
    ):
        return min(
            options,
            key=lambda candidate: abs(
                candidate - value
            ),
        )
