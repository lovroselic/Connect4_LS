
# players/factory.py

from __future__ import annotations

from pathlib import Path

import torch

from agents.lookahead import Connect4Lookahead
from agents.ppo import CNet192
from players.base import Player, PlayerConfig, PlayerType
from players.human import HumanPlayer
from players.lookahead import LookaheadPlayer
from players.ppo import PPOPlayer


class PlayerFactory:
    """
    Construct concrete Player instances from PlayerConfig objects.

    Shared AI engines and models are reused between players where appropriate.
    """

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

        self._ppo_model = ppo_model
        self._ppo_model_path = ppo_model_path
        self._ppo_device = torch.device(
            ppo_device if ppo_device is not None else "cpu"
        )
        self._ppo_mirror_tta = bool(
            ppo_mirror_tta
        )

    def create(
        self,
        player_id: int,
        config: PlayerConfig,
    ) -> Player:
        """
        Create one player from its configuration.
        """
        config_copy = config.copy()
        config_copy.validate()

        if config_copy.player_type is PlayerType.HUMAN:
            return HumanPlayer(
                player_id=player_id,
                config=config_copy,
            )

        if config_copy.player_type is PlayerType.LOOKAHEAD:
            return LookaheadPlayer(
                player_id=player_id,
                config=config_copy,
                engine=self._get_lookahead_engine(),
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

            return player

        raise ValueError(
            f"Unsupported player type: {config_copy.player_type!r}"
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

    def _get_lookahead_engine(self) -> Connect4Lookahead:
        if self._lookahead_engine is None:
            self._lookahead_engine = Connect4Lookahead()

        return self._lookahead_engine

