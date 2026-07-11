# players/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlayerType(Enum):
    """
    Supported Connect Four player implementations.
    """

    HUMAN = "human"
    LOOKAHEAD = "lookahead"
    PPO = "ppo"

    @property
    def display_name(self) -> str:
        """
        User-facing player type name.
        """
        return {
            PlayerType.HUMAN: "Human",
            PlayerType.LOOKAHEAD: "Lookahead",
            PlayerType.PPO: "PPO",
        }[self]


@dataclass(slots=True)
class PlayerConfig:
    """
    Configuration used to construct one match participant.

    Not every field applies to every player type. For example, depth is used
    by Lookahead players, while model_name applies to PPO players.
    """

    player_type: PlayerType = PlayerType.HUMAN
    name: str = "Human"

    lookahead_depth: int = 7

    model_name: str = "PPO_2004.pt"
    deterministic: bool = True

    def validate(self) -> None:
        """
        Normalize configuration values in place.
        """
        if not isinstance(self.player_type, PlayerType):
            try:
                self.player_type = PlayerType(str(self.player_type))
            except (TypeError, ValueError):
                self.player_type = PlayerType.HUMAN

        if not isinstance(self.name, str):
            self.name = self.player_type.display_name

        self.name = self.name.strip()

        if not self.name:
            self.name = self.player_type.display_name

        try:
            self.lookahead_depth = int(self.lookahead_depth)
        except (TypeError, ValueError):
            self.lookahead_depth = 7

        self.lookahead_depth = max(
            3,
            min(self.lookahead_depth, 13),
        )

        if not isinstance(self.model_name, str):
            self.model_name = "PPO_2004.pt"

        self.model_name = self.model_name.strip()

        if not self.model_name:
            self.model_name = "PPO_2004.pt"

        self.deterministic = bool(self.deterministic)

    def copy(self) -> "PlayerConfig":
        """
        Return an independent copy of this configuration.
        """
        return PlayerConfig(
            player_type=self.player_type,
            name=self.name,
            lookahead_depth=self.lookahead_depth,
            model_name=self.model_name,
            deterministic=self.deterministic,
        )


@dataclass(slots=True)
class MoveAnalysis:
    """
    Optional diagnostic information produced when selecting a move.

    This structure will feed the analysis panel for both AI and human players.
    Human analysis may be calculated by an assisting agent after the move.
    """

    selected_column: int | None = None
    elapsed_seconds: float = 0.0

    evaluation: float | None = None
    search_depth: int | None = None
    nodes_evaluated: int | None = None

    action_scores: tuple[float, ...] | None = None
    policy_probabilities: tuple[float, ...] | None = None
    value_estimate: float | None = None

    message: str = ""


@dataclass(slots=True)
class MoveResult:
    """
    Result returned by a player after choosing a move.
    """

    column: int
    analysis: MoveAnalysis | None = None


class Player(ABC):
    """
    Common interface implemented by all match participants.

    The match controller will interact with Player objects without needing to
    know whether the move comes from a human, lookahead search, or PPO model.
    """

    def __init__(
        self,
        player_id: int,
        config: PlayerConfig,
    ) -> None:
        if player_id not in (1, 2):
            raise ValueError(
                f"player_id must be 1 or 2, got {player_id}"
            )

        config.validate()

        self.player_id = int(player_id)
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def player_type(self) -> PlayerType:
        return self.config.player_type

    @property
    def is_human(self) -> bool:
        return self.player_type is PlayerType.HUMAN

    def begin_match(self) -> None:
        """
        Called before a new match begins.
        """
        pass

    def end_match(self) -> None:
        """
        Called after a match ends.
        """
        pass

    def cancel(self) -> None:
        """
        Request cancellation of any pending move calculation.

        Human players and synchronous agents may leave this as a no-op.
        """
        pass

    @abstractmethod
    def choose_move(
        self,
        board: Any,
    ) -> MoveResult | None:
        """
        Select a move from the supplied board state.

        Human players may return None until input has been supplied.
        AI players should return a MoveResult.
        """
        raise NotImplementedError

