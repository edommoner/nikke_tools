"""Exact browser transport inverse for historical audits; no numerical claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='cb64e4519396f075149f9bfffd5b10c10bb487d5571ef0e3e3cb6a37c57ff3eb'
AFTER_SHA256={'app/portable_detail.py': 'a670dedc0faaae03db12cd67ac1c5340d9ba6894b33d2be3291bc0be92c12ae4'}


def browser_preimage(root,name,raw):
    ledger=(Path(root)/'tests/fixtures/portable-browser-backend-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Browser backend source ledger changed')
    data=json.loads(ledger)
    if data.get('schema')!='browser-backend-source-history-v1' or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False:
        raise ValueError('Browser backend history scope changed')
    row=data['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed browser backend source: '+name)
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Browser backend inverse span changed: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Browser backend historical preimage changed: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return browser_preimage(root,name,raw)
    return raw
