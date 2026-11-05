"""Exact optimizer verification inverse for historical audits; no numerical claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='43b0848464d7f6d541c4039ee5420f90a8784227c6e7c9ebf9efea92bcde40b0'
AFTER_SHA256={'app/portable_detail.py': '9cb081db502aae45070507bd19f5cf3b588302ed7d8fbf3b523889d68062a000'}


def verification_preimage(root,name,raw):
    ledger=(Path(root)/'tests/fixtures/portable-optimizer-verification-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Optimizer verification source ledger changed')
    data=json.loads(ledger)
    if data.get('schema')!='optimizer-verification-source-history-v1' or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False:
        raise ValueError('Optimizer verification history scope changed')
    row=data['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed optimizer verification source: '+name)
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Optimizer verification inverse span changed: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Optimizer verification historical preimage changed: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return verification_preimage(root,name,raw)
    return raw
