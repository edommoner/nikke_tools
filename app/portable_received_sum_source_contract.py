"""Exact inverse for the common received-damage compensation state; no normalizer changes."""
import hashlib,json
from pathlib import Path
LEDGER_SHA256='076dbcec909e3497a4b996a0410f5554188f367c371f7974d71107ad474ef7cc'

def project_sources(root):
    root=Path(root);raw=(root/'tests/fixtures/portable-received-sum-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Received sum source ledger changed')
    data=json.loads(raw)
    if data['normalizer_changed'] is not False or data['baseline_commit']!='d7f4e000438188b31eb025a870e59289bb09a798':raise ValueError('Received sum baseline changed')
    result={}
    for name,row in data['files'].items():
        current=(root/name).read_bytes()
        if current!=row['after'].encode() or hashlib.sha256(current).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed received sum source: '+name)
        if hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Received sum preimage differs')
        result[name]=row['before']
    return result

def historical_hashes(root,source):
    from portable_slang_generation import source_hashes
    root=Path(root);current=source_hashes(root,source);before=project_sources(root)
    return {n:hashlib.sha256(before[n].encode()).hexdigest() if n in before else h for n,h in current.items()}
