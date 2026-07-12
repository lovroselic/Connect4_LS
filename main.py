# =============================================================================
# Connect4 LaughingSkull version
# based on model trained for kaggle competition
# model training and details, as well as JS version - lookahead only:
#   https://github.com/lovroselic/Connect4    
# =============================================================================


# =============================================================================
# # imports
# =============================================================================


from app.version import __version__
from app.application import Application

# =============================================================================
# # main
# =============================================================================

def main() -> None:
    print(f"Connect4_LS v{__version__} starting...")
    
    application = Application() 
    application.run()

if __name__ == "__main__":
    main()