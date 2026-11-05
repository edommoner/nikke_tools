"""Exact optimizer throughput inverse for historical audits; no numerical claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='2ca35e647280212f7ead9d92fae1dfd9dc06f9d4d664745dfffeeddf4a39553a'
AFTER_SHA256={'app/portable_detail.py': 'abd7414865de63ffb0c7a32db1193cfddc27456c187296f12bfdba86295d9841', 'app/portable_slang_generation.py': '7bcd8a7017f09792eb61eb7ef8afe65832815f34ad1821efd0cab982fc3d4b4f'}


def throughput_preimage(root,name,raw):
    ledger=(Path(root)/'tests/fixtures/portable-optimizer-throughput-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Optimizer throughput source ledger changed')
    data=json.loads(ledger)
    if data.get('schema')!='optimizer-throughput-source-history-v1' or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False:
        raise ValueError('Optimizer throughput history scope changed')
    row=data['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed optimizer throughput source: '+name)
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Optimizer throughput inverse span changed: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Optimizer throughput historical preimage changed: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return throughput_preimage(root,name,raw)
    return raw
