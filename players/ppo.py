
# players/ppo.py

from __future__ import annotations

from pathlib import Path
from time import perf_counter

import numpy as np
import torch
import torch.nn.functional as F

from agents.ppo import CNet192, load_cnet192
from app.paths import PPO_2004_PATH
from game import Connect4Board
from players.base import (
    MoveAnalysis,
    MoveResult,
    Player,
    PlayerConfig,
    PlayerType,
)


class PPOPlayer(Player):
    """
    Player controlled by the trained CNet192 PPO policy/value network.

    The model receives a single 6 x 7 point-of-view channel:

        +1 = current player's pieces
        -1 = opponent's pieces
         0 = empty

    Legal columns are masked before deterministic selection or sampling.
    """

    CENTER_COLUMN = 3

    def __init__(
        self,
        player_id: int,
        config: PlayerConfig,
        *,
        model: CNet192 | None = None,
        model_path: str | Path | None = None,
        device: torch.device | str | None = None,
        mirror_tta: bool = True,
    ) -> None:
        if config.player_type is not PlayerType.PPO:
            raise ValueError(
                "PPOPlayer requires PlayerType.PPO configuration."
            )

        super().__init__(
            player_id=player_id,
            config=config,
        )

        self.device = torch.device(
            device if device is not None else "cpu"
        )

        self.model_path = Path(
            model_path if model_path is not None else PPO_2004_PATH
        )

        self.mirror_tta = bool(mirror_tta)
        self._cancel_requested = False

        if model is None:
            self.model, self.checkpoint = load_cnet192(
                self.model_path,
                device=self.device,
                strict=True,
            )
        else:
            self.model = model.to(self.device)
            self.checkpoint = {}

        self.model.eval()

    @property
    def deterministic(self) -> bool:
        return self.config.deterministic

    def begin_match(self) -> None:
        self._cancel_requested = False

    def end_match(self) -> None:
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def choose_move(
        self,
        board: Connect4Board,
    ) -> MoveResult | None:
        """
        Select a legal move from the PPO policy.

        Deterministic mode chooses the legal move with the highest probability.
        Non-deterministic mode samples from the masked legal distribution.
        """
        if self._cancel_requested:
            return None

        if board.is_terminal:
            return None

        if board.current_player != self.player_id:
            return None

        legal_moves = board.legal_moves()

        if not legal_moves:
            return None

        started_at = perf_counter()

        pov = self._make_pov_board(board)

        logits, value_estimate = self._infer(
            pov,
        )

        probabilities = self._masked_probabilities(
            logits,
            legal_moves,
        )

        if self.deterministic:
            column = self._select_deterministic(
                probabilities,
                legal_moves,
            )
        else:
            column = int(
                np.random.default_rng().choice(
                    Connect4Board.COLS,
                    p=probabilities,
                )
            )

        elapsed_seconds = (
            perf_counter() - started_at
        )

        if self._cancel_requested:
            return None

        if column not in legal_moves:
            raise RuntimeError(
                "PPO model selected an illegal move: "
                f"{column}. Legal moves: {legal_moves}"
            )

        analysis = MoveAnalysis(
            selected_column=column,
            elapsed_seconds=elapsed_seconds,
            policy_probabilities=tuple(
                float(probability)
                for probability in probabilities
            ),
            value_estimate=float(value_estimate),
            message=(
                f"PPO selected column {column} "
                f"with probability {probabilities[column]:.3f}."
            ),
        )

        return MoveResult(
            column=column,
            analysis=analysis,
        )

    def warm_up(self) -> None:
        """
        Run one empty-board inference.

        This forces PyTorch initialization and is useful before a match starts.
        """
        empty = np.zeros(
            (
                Connect4Board.ROWS,
                Connect4Board.COLS,
            ),
            dtype=np.float32,
        )

        self._infer(empty)

    def _make_pov_board(
        self,
        board: Connect4Board,
    ) -> np.ndarray:
        """
        Convert the board to the model's point-of-view representation.
        """
        grid = board.to_numpy(
            dtype=np.int8,
        )

        pov = np.zeros(
            (
                Connect4Board.ROWS,
                Connect4Board.COLS,
            ),
            dtype=np.float32,
        )

        pov[grid == self.player_id] = 1.0

        pov[
            (grid != Connect4Board.EMPTY)
            & (grid != self.player_id)
        ] = -1.0

        return pov

    def _infer(
        self,
        pov: np.ndarray,
    ) -> tuple[np.ndarray, float]:
        """
        Return policy logits and a scalar value estimate.

        With mirror TTA enabled, policy logits are averaged after restoring the
        mirrored output to the original column order. Value estimates are also
        averaged between the normal and mirrored positions.
        """
        array = np.asarray(
            pov,
            dtype=np.float32,
        )

        if array.shape != (
            Connect4Board.ROWS,
            Connect4Board.COLS,
        ):
            raise ValueError(
                "PPO input must have shape "
                f"({Connect4Board.ROWS}, {Connect4Board.COLS}), "
                f"got {array.shape}"
            )

        if self.mirror_tta:
            batch = np.stack(
                [
                    array,
                    np.fliplr(array).copy(),
                ],
                axis=0,
            )

            tensor = (
                torch.from_numpy(batch)
                .unsqueeze(1)
                .to(self.device)
            )

            with torch.inference_mode():
                logits_tensor, values_tensor = self.model(
                    tensor
                )

            logits_batch = (
                logits_tensor
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            values_batch = (
                values_tensor
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            normal_logits = logits_batch[0]

            mirrored_logits = (
                logits_batch[1][::-1]
            )

            logits = (
                normal_logits + mirrored_logits
            ) * 0.5

            value_estimate = float(
                values_batch.mean()
            )

        else:
            tensor = (
                torch.from_numpy(array)
                .unsqueeze(0)
                .unsqueeze(0)
                .to(self.device)
            )

            with torch.inference_mode():
                logits_tensor, values_tensor = self.model(
                    tensor
                )

            logits = (
                logits_tensor[0]
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            value_estimate = float(
                values_tensor[0].item()
            )

        logits = np.nan_to_num(
            logits,
            nan=-1e9,
            posinf=1e9,
            neginf=-1e9,
        )

        return logits, value_estimate

    @staticmethod
    def _masked_probabilities(
        logits: np.ndarray,
        legal_moves: list[int],
    ) -> np.ndarray:
        """
        Convert logits to probabilities after masking illegal columns.
        """
        logits_tensor = torch.as_tensor(
            logits,
            dtype=torch.float32,
        )

        masked_logits = torch.full(
            (Connect4Board.COLS,),
            -torch.inf,
            dtype=torch.float32,
        )

        legal_index = torch.tensor(
            legal_moves,
            dtype=torch.long,
        )

        masked_logits[legal_index] = (
            logits_tensor[legal_index]
        )

        probabilities = F.softmax(
            masked_logits,
            dim=0,
        )

        result = (
            probabilities
            .cpu()
            .numpy()
            .astype(np.float64)
        )

        if not np.isfinite(result).all():
            result = np.zeros(
                Connect4Board.COLS,
                dtype=np.float64,
            )

            uniform_probability = (
                1.0 / len(legal_moves)
            )

            for column in legal_moves:
                result[column] = (
                    uniform_probability
                )

        return result

    @classmethod
    def _select_deterministic(
        cls,
        probabilities: np.ndarray,
        legal_moves: list[int],
    ) -> int:
        """
        Select the highest-probability legal move.

        Ties prefer the center, then the lower column index. This matches the
        deterministic tie-breaking convention of the latest Kaggle agent.
        """
        ordered = sorted(
            legal_moves,
            key=lambda column: (
                float(probabilities[column]),
                -abs(column - cls.CENTER_COLUMN),
                -column,
            ),
            reverse=True,
        )

        return int(ordered[0])

