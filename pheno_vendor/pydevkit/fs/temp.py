"""Temporary file utilities."""

import os
import tempfile
from contextlib import contextmanager
from typing import Any, Generator, Optional


class TempFile:
    """Temporary file manager."""

    def __init__(self, suffix: str = '', prefix: str = 'tmp', dir: Optional[str] = None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.path: Optional[str] = None
        self.fd: Optional[int] = None

    def __enter__(self):
        self.fd, self.path = tempfile.mkstemp(
            suffix=self.suffix,
            prefix=self.prefix,
            dir=self.dir,
        )
        return self.path

    def __exit__(self, *args):
        if self.fd is not None:
            os.close(self.fd)
        if self.path and os.path.exists(self.path):
            os.unlink(self.path)


class TempDir:
    """Temporary directory manager."""

    def __init__(self, suffix: str = '', prefix: str = 'tmp', dir: Optional[str] = None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.path: Optional[str] = None

    def __enter__(self):
        self.path = tempfile.mkdtemp(
            suffix=self.suffix,
            prefix=self.prefix,
            dir=self.dir,
        )
        return self.path

    def __exit__(self, *args):
        if self.path and os.path.exists(self.path):
            import shutil
            shutil.rmtree(self.path)


@contextmanager
def create_temp_file(**kwargs: Any) -> Generator[str, None, None]:
    """Create temporary file context manager."""
    with TempFile(**kwargs) as path:
        yield path


@contextmanager
def create_temp_dir(**kwargs: Any) -> Generator[str, None, None]:
    """Create temporary directory context manager."""
    with TempDir(**kwargs) as path:
        yield path
