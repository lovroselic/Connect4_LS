from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = PROJECT_ROOT / "models"
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
REPLAYS_DIR = PROJECT_ROOT / "replays"
RESULTS_DIR = PROJECT_ROOT / "results"

PPO_2004_PATH = MODELS_DIR / "PPO_2004.pt"