"""
This class contains code for locking and managing locks.

This functionality is developed to be thread-safe, but does not support multiprocessing.
"""

from collections import defaultdict
from contextlib import contextmanager
from threading import Lock

DEFAULT_TIMEOUT_SEC = 10

class NamedLocker:
    """
    A class that contains named locks. It is used to create a lock for a specific name.
    There can be multiple locks, each with a different name. This is used to prevent concurrent
    access to user settings for the same user, but to allow concurrent access for different users.

    This class is thread-safe, but will not work if the locks are accessed from different processes.
    """

    def __init__(self):
        # Lock to protect the locks dictionary.
        self._lock = Lock()
        # Dictionary containing the locks.
        self.locks: dict[str, Lock] = defaultdict(Lock)

    def acquire(self, name: str) -> bool:
        with self._lock:
            lock = self.locks[name]
        return lock.acquire(timeout=DEFAULT_TIMEOUT_SEC)

    def release(self, name: str):
        with self._lock:
            lock = self.locks[name]
        lock.release()

    @contextmanager
    def lock(self, name: str):
        """
        Context manager to acquire and release a named lock.

        :param name: The name of the lock.
        """
        has_acquired = self.acquire(name)
        if not has_acquired:
            raise TimeoutError(f"Could not acquire lock for {name}")
        try:
            yield None
        finally:
            self.release(name)
