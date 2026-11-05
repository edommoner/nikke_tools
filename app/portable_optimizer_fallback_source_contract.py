"""Exact optimizer fallback inverse for historical audits; no numerical claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='c15cc94a4778826054fa417fb710288d734bc941737775282c07e916f97890cd'
AFTER_SHA256={'app/portable_detail.py': '2f5ac5374a8bc98d1db641ba3b8669649761720bf4e10ba27f86de40b48c102c'}


def fallback_preimage(root,name,raw):
    ledger=(Path(root)/'tests/fixtures/portable-optimizer-fallback-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Optimizer fallback source ledger changed')
    data=json.loads(ledger)
    if data.get('schema')!='optimizer-fallback-source-history-v1' or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False:
        raise ValueError('Optimizer fallback history scope changed')
    row=data['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed optimizer fallback source: '+name)
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Optimizer fallback inverse span changed: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Optimizer fallback historical preimage changed: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return fallback_preimage(root,name,raw)
    return raw
