"""Process-local file facts, invalidated by filesystem identity and timestamps.

No persistent ledger. Readers are checked on both sides of computation; callers
still compare their source hashes before and after builds/dispatches.
"""
import hashlib
from pathlib import Path
from threading import RLock

_lock = RLock()
_values = {}


def stamp(path):
    s = Path(path).stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def file_value(path, kind, reader):
    path = Path(path)
    key = (str(path.absolute()), kind)
    with _lock:
        before = stamp(path)
        saved = _values.get(key)
        if saved is not None and saved[0] == before:
            return saved[1]
        value = reader(path)
        after = stamp(path)
        if before != after:
            raise RuntimeError('File changed while reading identity: '+str(path))
        _values[key] = (after, value)
        return value


def file_digest(path):
    return file_value(path, 'sha256', lambda p: hashlib.sha256(p.read_bytes()).hexdigest())
