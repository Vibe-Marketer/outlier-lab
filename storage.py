"""Atomic JSON writes for local configuration and background job receipts."""
import json
import os
import tempfile
import fcntl
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path, blocking=True):
    """Coordinate read/modify/write across the admin and local worker processes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            name = stream.name
            json.dump(value, stream, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def update_env(path, key, value):
    """Update one credential, retaining other services' private settings."""
    path = Path(path)
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [line for line in lines if not line.strip().startswith(key + "=")]
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        name = stream.name
        stream.write("\n".join([*lines, f"{key}={value}"]) + "\n")
    try:
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
