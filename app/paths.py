# app/paths.py

from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "Connect4_LS"
PUBLISHER_NAME = "LaughingSkull"

# Bundled, read-only files.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = PROJECT_ROOT / "models"
BUNDLED_CONFIG_DIR = PROJECT_ROOT / "config"

PPO_2004_PATH = MODELS_DIR / "PPO_2004.pt"
LOOKAHEAD_CONFIG_PATH = BUNDLED_CONFIG_DIR / "lookahead.json"
DEFAULT_SETTINGS_TEMPLATE_PATH = BUNDLED_CONFIG_DIR / "settings.json"


def _local_app_data_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        return Path(local_app_data)

    return Path.home() / ".local" / "share"


# Writable, per-user files.
USER_DATA_DIR = (
    _local_app_data_root()
    / PUBLISHER_NAME
    / APP_NAME
)

CONFIG_DIR = USER_DATA_DIR / "config"
LOGS_DIR = USER_DATA_DIR / "logs"
REPLAYS_DIR = USER_DATA_DIR / "replays"
RESULTS_DIR = USER_DATA_DIR / "results"
NUMBA_CACHE_DIR = USER_DATA_DIR / "numba_cache"

SETTINGS_PATH = CONFIG_DIR / "settings.json"


def ensure_user_directories() -> None:
    for directory in (
        CONFIG_DIR,
        LOGS_DIR,
        REPLAYS_DIR,
        RESULTS_DIR,
        NUMBA_CACHE_DIR,
    ):
        try:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            print(
                "[Paths] Could not create directory "
                f"{directory}: {error}"
            )


# Must be set before Numba initializes its cache machinery.
os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    str(NUMBA_CACHE_DIR),
)

ensure_user_directories()
