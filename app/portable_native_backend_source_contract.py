"""Exact reviewed native-backend inverse for historical audits only.

This reconstructs pre-native bytes; it does not normalize generated code or
certify numerical equivalence of current CPU/GPU execution.
"""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='19cdfea3a9b245978876b83cadde8abb6bc9eca499b460eb483e32795141e881'
AFTER_SHA256={'app/portable_slang_generation.py': '1fc0467944a3a6eb73b79456a230a6a7aac9b8bb18697aa35e9f67323c1adf6e', 'app/portable_detail.py': '6cf3225c1cb294bc5e5b022ce4ba07a5f3203891efe0d6ff1d860d26343bcee1', 'app/portable_backend.py': 'f2155d2d99c144f8ee188314ef0781c3f29b7f6d437b0137276f3985f0443aba'}


def native_preimage(root,name,raw):
    from portable_browser_backend_source_contract import reviewed_bytes as browser_reviewed_bytes
    raw=browser_reviewed_bytes(root,name,raw)
    ledger=(Path(root)/'tests/fixtures/portable-native-backend-source-delta.json').read_bytes()
    if hashlib.sha256(ledger).hexdigest()!=LEDGER_SHA256:raise ValueError('Native backend source ledger changed')
    data=json.loads(ledger)
    if (data.get('schema')!='native-backend-source-history-v1'
        or data.get('baseline_commit')!='777dcaf33ab4a452bc7636a32a27e1939eb899dc'
        or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False):
        raise ValueError('Native backend source history scope changed')
    row=data['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed native backend source: '+name)
    text=raw.decode('utf-8');boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Native backend inverse span changed: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Native backend historical preimage changed: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    # Other historical versions still go through their existing strict guards.
    # Only the exact reviewed native digest enters this new inverse.
    from portable_browser_backend_source_contract import reviewed_bytes as browser_reviewed_bytes
    raw=browser_reviewed_bytes(root,name,raw)
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:
        return native_preimage(root,name,raw)
    return raw
