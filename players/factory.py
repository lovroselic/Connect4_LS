
# players/factory.py

from __future__ import annotations

from pathlib import Path

import torch

from agents.lookahead import Connect4Lookahead
from agents.ppo import CNet192
from app.lookahead_config import LOOKAHEAD_CONFIG
from game import Connect4Board
from players.base import Player, PlayerConfig, PlayerType
from players.human import HumanPlayer
from players.lookahead import LookaheadPlayer
from players.ppo import PPOPlayer


class PlayerFactory:
    """
    Construct concrete Player instances from PlayerConfig objects.

    Shared AI engines and models are reused between players.

    The Lookahead engine is warmed up once, using a small non-opening
    position, so Numba compilation happens before the first real AI move.
    """

    LOOKAHEAD_WARMUP_MOVES = (
        3,
        2,
        3,
        2,
        4,
        1,
    )

    def __init__(
        self,
        *,
        lookahead_engine: Connect4Lookahead | None = None,
        ppo_model: CNet192 | None = None,
        ppo_model_path: str | Path | None = None,
        ppo_device: torch.device | str | None = None,
        ppo_mirror_tta: bool = True,
    ) -> None:
        self._lookahead_engine = lookahead_engine
        self._lookahead_warmed_up = False

        self._ppo_model = ppo_model
        self._ppo_model_path = ppo_model_path

        self._ppo_device = torch.device(
            ppo_device
            if ppo_device is not None
            else "cpu"
        )

        self._ppo_mirror_tta = bool(
            ppo_mirror_tta
        )

        self._ppo_warmed_up = False

    # ------------------------------------------------------------------
    # Player construction
    # ------------------------------------------------------------------

    def create(
        self,
        player_id: int,
        config: PlayerConfig,
    ) -> Player:
        """
        Create one player from its configuration.

        The configuration is copied so the player owns an independent
        configuration that cannot be modified by Match Setup afterward.
        """
        config_copy = config.copy()
        config_copy.validate()

        if config_copy.player_type is PlayerType.HUMAN:
            return HumanPlayer(
                player_id=player_id,
                config=config_copy,
            )

        if config_copy.player_type is PlayerType.LOOKAHEAD:
            self.warm_up_lookahead()

            return LookaheadPlayer(
                player_id=player_id,
                config=config_copy,
                engine=self._get_lookahead_engine(),
                include_action_scores=True,
                action_score_depth=(
                    config_copy.lookahead_depth
                ),
            )

        if config_copy.player_type is PlayerType.PPO:
            player = PPOPlayer(
                player_id=player_id,
                config=config_copy,
                model=self._ppo_model,
                model_path=self._ppo_model_path,
                device=self._ppo_device,
                mirror_tta=self._ppo_mirror_tta,
            )

            if self._ppo_model is None:
                self._ppo_model = player.model

            if not self._ppo_warmed_up:
                player.warm_up()
                self._ppo_warmed_up = True

            return player

        raise ValueError(
            f"Unsupported player type: "
            f"{config_copy.player_type!r}"
        )

    def create_lookahead_analyzer(
        self,
        *,
        player_id: int,
        depth: int = 13,
    ) -> LookaheadPlayer:
        """
        Create a temporary Lookahead player for hints and analysis.

        The shared warmed-up engine is reused. The returned player calculates
        per-column action scores and stores the selected move's score in
        MoveAnalysis.evaluation.
        """
        self.warm_up_lookahead()

        config = PlayerConfig(
            player_type=PlayerType.LOOKAHEAD,
            name=f"LA{int(depth)} Hint",
            lookahead_depth=depth,
        )

        config.validate()

        return LookaheadPlayer(
            player_id=player_id,
            config=config,
            engine=self._get_lookahead_engine(),
            include_action_scores=True,
            action_score_depth=(
                config.lookahead_depth
            ),
        )

    def create_pair(
        self,
        player_one_config: PlayerConfig,
        player_two_config: PlayerConfig,
    ) -> tuple[Player, Player]:
        """
        Create Player 1 and Player 2 for one match.
        """
        player_one = self.create(
            player_id=1,
            config=player_one_config,
        )

        player_two = self.create(
            player_id=2,
            config=player_two_config,
        )

        return player_one, player_two

    # ------------------------------------------------------------------
    # Lookahead engine
    # ------------------------------------------------------------------

    def _get_lookahead_engine(
        self,
    ) -> Connect4Lookahead:
        """
        Lazily construct and reuse the Lookahead engine.
        """
        if self._lookahead_engine is None:
            self._lookahead_engine = (
                Connect4Lookahead()
            )

        return self._lookahead_engine

    def warm_up_lookahead(self) -> None:
        """
        Compile the Numba Lookahead search once.

        An empty board cannot be used because the opening book immediately
        returns column 3 and never enters the compiled search. The warm-up
        therefore uses a small legal midgame position.
        """
        if self._lookahead_warmed_up:
            return

        engine = self._get_lookahead_engine()

        warmup_board = Connect4Board.from_moves(
            self.LOOKAHEAD_WARMUP_MOVES
        )

        engine.n_step_lookahead(
            warmup_board.to_numpy(),
            player=warmup_board.current_player,
            depth=LOOKAHEAD_CONFIG.warmup_depth,
        )

        self._lookahead_warmed_up = True

    # ------------------------------------------------------------------
    # Warm-up state
    # ------------------------------------------------------------------

    @property
    def lookahead_is_warmed_up(self) -> bool:
        return self._lookahead_warmed_up

    @property
    def ppo_is_warmed_up(self) -> bool:
        return self._ppo_warmed_up

