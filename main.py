# =============================================================================
# Connect4 LaughingSkull version
# based on model trainde for kaggle competition
# model training and details, as well as JS version - lookahead only:
#   https://github.com/lovroselic/Connect4    
# =============================================================================


# =============================================================================
# # imports
# =============================================================================

#import torch
#import pygame

from app.version import __version__
#from app.config import AppConfig
#from app.paths import PPO_2004_PATH
#from app.state import AppState, ScreenID

from app.application import Application


#from agents.lookahead import Connect4Lookahead
#from agents.ppo import load_cnet192

#from ui.theme import FONTS, THEME
#from ui.widgets.button import Button
#from ui.widgets.selector import Selector
#from ui.screens.base_screen import BaseScreen
#from ui.screens.main_menu import MainMenuScreen
#from ui.screens.match_setup import MatchSetupScreen
#from ui.screens.settings_screen import SettingsScreen
#from ui.screens.test_menu import TestMenuScreen

#from players import PlayerConfig, PlayerType

# =============================================================================
# # functions
# =============================================================================




# =============================================================================
# # main
# =============================================================================

def main() -> None:
    print(f"Connect4_LS v{__version__} starting...")
    
    application = Application() 
    application.run()

if __name__ == "__main__":
    main()