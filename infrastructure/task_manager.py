
# infrastructure/task_manager.py

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from infrastructure.background_task import BackgroundTask


T = TypeVar("T")


class TaskManager:
    """
    Owns the application's worker-thread pool.
    """

    def __init__(
        self,
        *,
        maximum_workers: int = 1,
    ) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max(
                1,
                int(maximum_workers),
            ),
            thread_name_prefix="Connect4Worker",
        )

        self._shutdown = False

    def create_task(self) -> BackgroundTask[T]:
        if self._shutdown:
            raise RuntimeError(
                "TaskManager has already been shut down."
            )

        return BackgroundTask(
            self._executor
        )

    def shutdown(
        self,
        *,
        wait: bool = True,
    ) -> None:
        if self._shutdown:
            return

        self._shutdown = True

        self._executor.shutdown(
            wait=wait,
            cancel_futures=True,
        )

