"""Publish owned-data acceptance only when all evidence matches current sources."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def checked_report(path):
    report = json.loads((ROOT / path).read_text(encoding='utf-8-sig'))
    assert report.get('passed'), f'Acceptance failed: {path}'
    hashes = report.get('source_sha256', {})
    assert hashes, f'Missing source provenance: {path}'
    for source, expected in hashes.items():
        assert digest(source) == expected, f'Stale evidence: {path}: {source}'
    return report
