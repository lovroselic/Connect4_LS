
# app/lookahead_config.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.paths import PROJECT_ROOT


LOOKAHEAD_CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "lookahead.json"
)


@dataclass(frozen=True, slots=True)
class LookaheadConfig:
    """
    Shared configuration for all Lookahead players and UI controls.
    """

    minimum_depth: int = 3
    maximum_depth: int = 15
    default_depth: int = 9
    warmup_depth: int = 3

    @classmethod
    def load(
        cls,
        path: str | Path = LOOKAHEAD_CONFIG_PATH,
    ) -> "LookaheadConfig":
        """
        Load and validate lookahead settings.

        Missing or malformed files safely fall back to defaults.
        """
        config_path = Path(path)

        try:
            with config_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            FileNotFoundError,
            PermissionError,
            json.JSONDecodeError,
            OSError,
        ):
            return cls()

        if not isinstance(data, dict):
            return cls()

        defaults = cls()

        minimum_depth = cls._to_int(
            data.get(
                "minimum_depth",
                defaults.minimum_depth,
            ),
            defaults.minimum_depth,
        )

        maximum_depth = cls._to_int(
            data.get(
                "maximum_depth",
                defaults.maximum_depth,
            ),
            defaults.maximum_depth,
        )

        if minimum_depth < 1:
            minimum_depth = 1

        if maximum_depth < minimum_depth:
            maximum_depth = minimum_depth

        default_depth = cls._clamp(
            cls._to_int(
                data.get(
                    "default_depth",
                    defaults.default_depth,
                ),
                defaults.default_depth,
            ),
            minimum_depth,
            maximum_depth,
        )

        warmup_depth = cls._clamp(
            cls._to_int(
                data.get(
                    "warmup_depth",
                    defaults.warmup_depth,
                ),
                defaults.warmup_depth,
            ),
            minimum_depth,
            maximum_depth,
        )

        return cls(
            minimum_depth=minimum_depth,
            maximum_depth=maximum_depth,
            default_depth=default_depth,
            warmup_depth=warmup_depth,
        )

    def clamp_depth(
        self,
        depth: int,
    ) -> int:
        """
        Clamp a depth to the configured range.
        """
        normalized = self._to_int(
            depth,
            self.default_depth,
        )

        return self._clamp(
            normalized,
            self.minimum_depth,
            self.maximum_depth,
        )

    @property
    def selectable_depths(self) -> tuple[int, ...]:
        """
        Return all depths available in Match Setup.
        """
        return tuple(
            range(
                self.minimum_depth,
                self.maximum_depth + 1,
            )
        )

    @staticmethod
    def _to_int(
        value,
        fallback: int,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return int(fallback)

    @staticmethod
    def _clamp(
        value: int,
        minimum: int,
        maximum: int,
    ) -> int:
        return max(
            minimum,
            min(value, maximum),
        )


LOOKAHEAD_CONFIG = LookaheadConfig.load()

