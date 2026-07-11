
# infrastructure/background_task.py

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Callable, Generic, TypeVar


T = TypeVar("T")


class BackgroundTask(Generic[T]):
    """
    Runs one callable on a worker thread.

    The Pygame thread can poll the task through update-style properties without
    blocking the UI.
    """

    def __init__(
        self,
        executor: ThreadPoolExecutor,
    ) -> None:
        self._executor = executor
        self._future: Future[T] | None = None
        self._lock = Lock()

    @property
    def is_running(self) -> bool:
        future = self._future

        return (
            future is not None
            and not future.done()
        )

    @property
    def is_done(self) -> bool:
        future = self._future

        return (
            future is not None
            and future.done()
        )

    @property
    def has_task(self) -> bool:
        return self._future is not None

    def start(
        self,
        function: Callable[[], T],
    ) -> bool:
        """
        Start a new background task.

        Returns False when another task is still running.
        """
        with self._lock:
            if self.is_running:
                return False

            self._future = self._executor.submit(
                function
            )

            return True

    def result(self) -> T | None:
        """
        Return the completed task result.

        Returns None while the task is still running or when no task exists.
        Exceptions raised by the worker are re-raised here.
        """
        future = self._future

        if future is None or not future.done():
            return None

        return future.result()

    def exception(self) -> BaseException | None:
        """
        Return the completed task exception, if any.
        """
        future = self._future

        if future is None or not future.done():
            return None

        return future.exception()

    def clear(self) -> None:
        """
        Forget a completed task.

        Running futures are not forcibly cancelled.
        """
        with self._lock:
            if self.is_running:
                return

            self._future = None

