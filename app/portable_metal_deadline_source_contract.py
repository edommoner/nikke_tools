"""Exact host-timeout inverse for historical audits; no GPU equivalence claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='f4f4088825b9ee641f34141821bcea293f11b2d88dc0a2bd2f01ae4deb4accdc'
AFTER_SHA256='ad1f55129422b4b80e34bd21f41cdb045f2d1a0d9f0a201e0c6c2e8be8c5b08e'
CALIBRATED_LEDGER_SHA256='2642d00e8a47cad5091a9d0e288d029ed55a911c313d6e4485be083ff0438030'


def historical_backend_bytes(root,raw):
    ledger=(Path(root)/'tests/fixtures/portable-metal-work-deadline-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Metal deadline source ledger changed')
    row=json.loads(ledger)
    if hashlib.sha256(raw).hexdigest()==AFTER_SHA256:
        calibrated=(Path(root)/'tests/fixtures/portable-metal-calibrated-deadline-source-delta.json').read_bytes()
        if hashlib.sha256(calibrated).hexdigest()!=CALIBRATED_LEDGER_SHA256:raise ValueError('Calibrated Metal deadline ledger changed')
        change=json.loads(calibrated);text=raw.decode('utf-8');boundary=len(text)
        for hunk in reversed(change['hunks']):
            start,end=hunk['start'],hunk['end']
            if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Calibrated Metal deadline inverse span changed')
            text=text[:start]+hunk['before']+text[end:];boundary=start
        raw=text.encode('utf-8')
        if hashlib.sha256(raw).hexdigest()!=change['before_sha256']:raise ValueError('Calibrated Metal deadline preimage changed')
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed Metal deadline transport')
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Metal deadline inverse span changed')
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Metal deadline historical preimage changed')
    return raw
