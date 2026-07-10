
import torch

from app.version import __version__
from agents.lookahead import Connect4Lookahead
from agents.ppo import load_cnet192
from app.paths import PPO_2004_PATH




def main() -> None:
    print(f"Connect4_LS v{__version__} starting...")
    lookahead = Connect4Lookahead()
    
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    ppo_model, checkpoint = load_cnet192(
       PPO_2004_PATH,
       device=device,
    )
    ppo_model.eval()
     
    print("PPO model loaded.")
    print(f"Checkpoint: {PPO_2004_PATH.name}")
    print(f"Device: {device}")
    print(f"Architecture: {checkpoint['cfg']['arch']}")
    print(f"Episode: {checkpoint.get('episode', 'unknown')}")


if __name__ == "__main__":
    main()