@echo off
setlocal EnableExtensions

rem ============================================================
rem  Connect Four standalone project structure
rem ============================================================

set "PROJECT_NAME=Connect4_LS"
set "ROOT=%CD%\%PROJECT_NAME%"

echo.
echo Creating project:
echo %ROOT%
echo.

if exist "%ROOT%" (
    echo ERROR: The directory already exists:
    echo %ROOT%
    echo.
    pause
    exit /b 1
)

rem ============================================================
rem  Create directories
rem ============================================================

mkdir "%ROOT%"

mkdir "%ROOT%\app"

mkdir "%ROOT%\game"

mkdir "%ROOT%\players"

mkdir "%ROOT%\agents"
mkdir "%ROOT%\agents\lookahead"
mkdir "%ROOT%\agents\ppo"

mkdir "%ROOT%\ui"
mkdir "%ROOT%\ui\widgets"
mkdir "%ROOT%\ui\screens"

mkdir "%ROOT%\rendering"

mkdir "%ROOT%\infrastructure"

mkdir "%ROOT%\assets"
mkdir "%ROOT%\assets\images"
mkdir "%ROOT%\assets\fonts"
mkdir "%ROOT%\assets\sounds"
mkdir "%ROOT%\assets\icons"

mkdir "%ROOT%\models"

mkdir "%ROOT%\config"

mkdir "%ROOT%\logs"
mkdir "%ROOT%\replays"
mkdir "%ROOT%\results"

mkdir "%ROOT%\tests"

mkdir "%ROOT%\build"

rem ============================================================
rem  Root files
rem ============================================================

type nul > "%ROOT%\main.py"
type nul > "%ROOT%\requirements.txt"
type nul > "%ROOT%\README.md"
type nul > "%ROOT%\.gitignore"

rem ============================================================
rem  Application package
rem ============================================================

type nul > "%ROOT%\app\__init__.py"
type nul > "%ROOT%\app\application.py"
type nul > "%ROOT%\app\state.py"
type nul > "%ROOT%\app\config.py"
type nul > "%ROOT%\app\paths.py"

rem ============================================================
rem  Core game package
rem ============================================================

type nul > "%ROOT%\game\__init__.py"
type nul > "%ROOT%\game\board.py"
type nul > "%ROOT%\game\rules.py"
type nul > "%ROOT%\game\position.py"
type nul > "%ROOT%\game\match.py"
type nul > "%ROOT%\game\result.py"
type nul > "%ROOT%\game\replay.py"

rem ============================================================
rem  Player package
rem ============================================================

type nul > "%ROOT%\players\__init__.py"
type nul > "%ROOT%\players\base.py"
type nul > "%ROOT%\players\human.py"
type nul > "%ROOT%\players\lookahead.py"
type nul > "%ROOT%\players\ppo.py"
type nul > "%ROOT%\players\random.py"

rem ============================================================
rem  Agent implementations
rem ============================================================

type nul > "%ROOT%\agents\__init__.py"

type nul > "%ROOT%\agents\lookahead\__init__.py"
type nul > "%ROOT%\agents\lookahead\engine.py"
type nul > "%ROOT%\agents\lookahead\numba_search.py"
type nul > "%ROOT%\agents\lookahead\evaluation.py"
type nul > "%ROOT%\agents\lookahead\transposition.py"

type nul > "%ROOT%\agents\ppo\__init__.py"
type nul > "%ROOT%\agents\ppo\model.py"
type nul > "%ROOT%\agents\ppo\observation.py"
type nul > "%ROOT%\agents\ppo\inference.py"

rem ============================================================
rem  UI package
rem ============================================================

type nul > "%ROOT%\ui\__init__.py"
type nul > "%ROOT%\ui\theme.py"
type nul > "%ROOT%\ui\layout.py"

type nul > "%ROOT%\ui\widgets\__init__.py"
type nul > "%ROOT%\ui\widgets\button.py"
type nul > "%ROOT%\ui\widgets\label.py"
type nul > "%ROOT%\ui\widgets\selector.py"
type nul > "%ROOT%\ui\widgets\checkbox.py"
type nul > "%ROOT%\ui\widgets\slider.py"
type nul > "%ROOT%\ui\widgets\panel.py"

type nul > "%ROOT%\ui\screens\__init__.py"
type nul > "%ROOT%\ui\screens\base_screen.py"
type nul > "%ROOT%\ui\screens\main_menu.py"
type nul > "%ROOT%\ui\screens\match_setup.py"
type nul > "%ROOT%\ui\screens\game_screen.py"
type nul > "%ROOT%\ui\screens\results_screen.py"
type nul > "%ROOT%\ui\screens\settings_screen.py"
type nul > "%ROOT%\ui\screens\test_menu.py"

rem ============================================================
rem  Rendering package
rem ============================================================

type nul > "%ROOT%\rendering\__init__.py"
type nul > "%ROOT%\rendering\board_renderer.py"
type nul > "%ROOT%\rendering\animation.py"
type nul > "%ROOT%\rendering\assets.py"
type nul > "%ROOT%\rendering\analysis_panel.py"

rem ============================================================
rem  Infrastructure package
rem ============================================================

type nul > "%ROOT%\infrastructure\__init__.py"
type nul > "%ROOT%\infrastructure\ai_executor.py"
type nul > "%ROOT%\infrastructure\logging.py"
type nul > "%ROOT%\infrastructure\persistence.py"
type nul > "%ROOT%\infrastructure\headless_runner.py"
type nul > "%ROOT%\infrastructure\tournament.py"

rem ============================================================
rem  Tests
rem ============================================================

type nul > "%ROOT%\tests\__init__.py"
type nul > "%ROOT%\tests\test_board.py"
type nul > "%ROOT%\tests\test_rules.py"
type nul > "%ROOT%\tests\test_match.py"
type nul > "%ROOT%\tests\test_bitboard.py"
type nul > "%ROOT%\tests\test_lookahead.py"
type nul > "%ROOT%\tests\test_ppo.py"
type nul > "%ROOT%\tests\test_tournament.py"

rem ============================================================
rem  Initial configuration files
rem ============================================================

(
    echo {
    echo     "show_test_menu": true,
    echo     "show_analysis_panel": true,
    echo     "window_width": 1280,
    echo     "window_height": 800,
    echo     "fullscreen": false,
    echo     "animation_speed": 1.0,
    echo     "ai_move_delay_ms": 300
    echo }
) > "%ROOT%\config\settings.json"

(
    echo {
    echo     "minimum_depth": 3,
    echo     "maximum_depth": 13,
    echo     "default_depth": 9,
    echo     "warmup_depth": 3
    echo }
) > "%ROOT%\config\lookahead.json"

rem Preserve otherwise empty runtime directories in Git.
type nul > "%ROOT%\assets\images\.gitkeep"
type nul > "%ROOT%\assets\fonts\.gitkeep"
type nul > "%ROOT%\assets\sounds\.gitkeep"
type nul > "%ROOT%\assets\icons\.gitkeep"
type nul > "%ROOT%\models\.gitkeep"
type nul > "%ROOT%\logs\.gitkeep"
type nul > "%ROOT%\replays\.gitkeep"
type nul > "%ROOT%\results\.gitkeep"
type nul > "%ROOT%\build\.gitkeep"

rem ============================================================
rem  Initial requirements
rem ============================================================

(
    echo pygame
    echo numpy
    echo numba
    echo torch
    echo pytest
    echo pyinstaller
) > "%ROOT%\requirements.txt"

rem ============================================================
rem  Initial .gitignore
rem ============================================================

(
    echo # Python
    echo __pycache__/
    echo *.py[cod]
    echo *$py.class
    echo.
    echo # Virtual environments
    echo .venv/
    echo venv/
    echo env/
    echo.
    echo # IDE
    echo .vscode/
    echo .idea/
    echo.
    echo # Tests and caches
    echo .pytest_cache/
    echo .mypy_cache/
    echo .coverage
    echo htmlcov/
    echo.
    echo # Runtime output
    echo logs/*
    echo !logs/.gitkeep
    echo replays/*
    echo !replays/.gitkeep
    echo results/*
    echo !results/.gitkeep
    echo.
    echo # Build output
    echo dist/
    echo build/*
    echo !build/.gitkeep
    echo *.spec
    echo.
    echo # Local configuration
    echo config/settings.local.json
) > "%ROOT%\.gitignore"

rem ============================================================
rem  Initial README
rem ============================================================

(
    echo # Connect Four Standalone
    echo.
    echo Standalone Pygame implementation of standard 6x7 Connect Four.
    echo.
    echo Supported players:
    echo.
    echo - Human
    echo - PPO model
    echo - Depth-based Numba lookahead agents
    echo.
    echo Supported match combinations:
    echo.
    echo - Human vs Human
    echo - Human vs AI
    echo - AI vs AI
    echo.
    echo Development and benchmark tools can be exposed through the test menu.
) > "%ROOT%\README.md"

rem ============================================================
rem  Finished
rem ============================================================

echo.
echo Project structure created successfully.
echo.
echo Root:
echo %ROOT%
echo.
echo Opening project directory...
start "" "%ROOT%"

echo.
pause
endlocal

