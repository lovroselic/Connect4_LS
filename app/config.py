# app/config.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Mapping

from app.paths import CONFIG_DIR


DEFAULT_SETTINGS_PATH = CONFIG_DIR / "settings.json"


@dataclass(slots=True)
class AppConfig:
    """
    Runtime configuration for Connect4_LS.

    Values are loaded from config/settings.json. Missing or invalid values
    fall back to the defaults defined here.
    """

    show_test_menu: bool = True
    show_analysis_panel: bool = True

    window_width: int = 1280
    window_height: int = 800
    fullscreen: bool = False

    target_fps: int = 60
    animation_speed: float = 1.0
    ai_move_delay_ms: int = 300

    window_title: str = "Connect4_LS"

    @classmethod
    def load(cls, path: Path | str = DEFAULT_SETTINGS_PATH) -> "AppConfig":
        """
        Load configuration from a JSON file.

        Missing files, malformed JSON, unknown keys and invalid values are
        handled safely. Unknown keys are ignored.
        """
        config_path = Path(path)

        if not config_path.exists():
            print(
                f"[Config] Settings file not found: {config_path}\n"
                "[Config] Using default settings."
            )
            return cls()

        try:
            with config_path.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(
                f"[Config] Could not read settings file: {config_path}\n"
                f"[Config] {error}\n"
                "[Config] Using default settings."
            )
            return cls()

        if not isinstance(raw_data, Mapping):
            print(
                f"[Config] Root JSON value must be an object: {config_path}\n"
                "[Config] Using default settings."
            )
            return cls()

        valid_field_names = {field.name for field in fields(cls)}

        filtered_data = {
            key: value
            for key, value in raw_data.items()
            if key in valid_field_names
        }

        config = cls()

        for key, value in filtered_data.items():
            setattr(config, key, value)

        config.validate()
        return config

    def validate(self) -> None:
        """
        Validate and normalize configuration values in place.
        """

        self.show_test_menu = self._as_bool(
            self.show_test_menu,
            default=True,
        )
        self.show_analysis_panel = self._as_bool(
            self.show_analysis_panel,
            default=True,
        )
        self.fullscreen = self._as_bool(
            self.fullscreen,
            default=False,
        )

        self.window_width = self._clamp_int(
            self.window_width,
            minimum=800,
            maximum=7680,
            default=1280,
        )
        self.window_height = self._clamp_int(
            self.window_height,
            minimum=600,
            maximum=4320,
            default=800,
        )
        self.target_fps = self._clamp_int(
            self.target_fps,
            minimum=30,
            maximum=240,
            default=60,
        )
        self.ai_move_delay_ms = self._clamp_int(
            self.ai_move_delay_ms,
            minimum=0,
            maximum=10_000,
            default=300,
        )

        self.animation_speed = self._clamp_float(
            self.animation_speed,
            minimum=0.1,
            maximum=10.0,
            default=1.0,
        )

        if not isinstance(self.window_title, str):
            self.window_title = "Connect4_LS"

        self.window_title = self.window_title.strip()

        if not self.window_title:
            self.window_title = "Connect4_LS"

    def save(self, path: Path | str = DEFAULT_SETTINGS_PATH) -> None:
        """
        Save the current configuration as formatted JSON.
        """
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        self.validate()

        with config_path.open("w", encoding="utf-8") as file:
            json.dump(
                asdict(self),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serializable dictionary containing the current settings.
        """
        self.validate()
        return asdict(self)

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return bool(value)

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"true", "yes", "on", "1"}:
                return True

            if normalized in {"false", "no", "off", "0"}:
                return False

        return default

    @staticmethod
    def _clamp_int(
        value: Any,
        minimum: int,
        maximum: int,
        default: int,
    ) -> int:
        try:
            integer_value = int(value)
        except (TypeError, ValueError):
            return default

        return max(minimum, min(integer_value, maximum))

    @staticmethod
    def _clamp_float(
        value: Any,
        minimum: float,
        maximum: float,
        default: float,
    ) -> float:
        try:
            float_value = float(value)
        except (TypeError, ValueError):
            return default

        return max(minimum, min(float_value, maximum))

