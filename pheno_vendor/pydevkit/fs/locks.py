"""File locking utilities."""

import os
import time
from pathlib import Path
from typing import Optional


class FileLock:
    """
    Simple file-based lock.

    Example:
        with FileLock("myfile.lock"):
            # Critical section
            pass
    """

    def __init__(self, lock_file: str, timeout: float = 10.0):
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.acquired = False

    def acquire(self) -> bool:
        """Acquire lock."""
        start_time = time.time()

        while True:
            try:
                # Try to create lock file
                fd = os.open(
                    self.lock_file,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY
                )
                os.close(fd)
                self.acquired = True
                return True
            except FileExistsError:
                # Lock file exists
                if time.time() - start_time > self.timeout:
                    return False
                time.sleep(0.1)

    def release(self) -> None:
        """Release lock."""
        if self.acquired and self.lock_file.exists():
            self.lock_file.unlink()
            self.acquired = False

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock: {self.lock_file}")
        return self

    def __exit__(self, *args):
        self.release()


def try_lock_file(path: str, timeout: float = 10.0) -> Optional[FileLock]:
    """Try to acquire file lock."""
    lock = FileLock(f"{path}.lock", timeout=timeout)
    if lock.acquire():
        return lock
    return None
