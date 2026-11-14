"""Shared offline file guards for every KonaklamaFlow command.

No network, credentials, PMS write, or guest-data echo. A report must never
replace its source, even through a hard link or a symbolic link.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .core import InputError

# One byte ceiling for every command-line JSON input (snapshots and reports).
MAX_INPUT_BYTES = 2_000_000
MAX_ROOMS = 500
MAX_RESERVATIONS = 5_000


def unique_object(pairs):
    """Reject duplicate keys instead of keeping the last value."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InputError("Duplicate JSON fields")
        obj[key] = value
    return obj


def read_limited_json(path: str, limit: int = MAX_INPUT_BYTES):
    """Read one JSON document without echoing paths, keys or values."""
    if type(limit) is not int or limit < 1:
        raise InputError("input JSON exceeds safety limit")
    with open(path, "rb") as stream:
        payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise InputError("input JSON exceeds safety limit")
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
    except InputError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise InputError("unable to read JSON input") from None


def ensure_output_not_input(output: str, *sources: str) -> None:
    """Refuse any output path that is the same file as an input."""
    output_path = Path(output)
    for source in sources:
        input_path = Path(source)
        try:
            linked = (output_path.exists() and input_path.exists()
                      and output_path.samefile(input_path))
        except OSError:
            linked = False
        if input_path.resolve() == output_path.resolve() or linked:
            raise InputError("output path must differ from input to prevent data loss")


def write_owner_report(path: str, output: str, *sources: str) -> None:
    """Atomically replace a report so only the owning user can read it."""
    if sources:
        ensure_output_not_input(path, *sources)
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(target.parent), delete=False) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o600)
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
