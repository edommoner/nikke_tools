"""Pinned exact preimage for the opt-in cover extension; never normalization."""
import hashlib,json
from pathlib import Path
LEDGER_SHA256='3b61075912a3728c5fc3c849b67361dca855439603de95b79c06b0058b70b846'

def project_sources(root):
    root=Path(root);raw=(root/'tests/fixtures/portable-cover-defense-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Cover source inverse ledger changed')
    data=json.loads(raw)
    if data['schema']!=1 or data['normalizer_changed'] is not False or data['baseline_commit']!='48584f8a9dfde832d8a7bd66a1469d64c3224f6c':raise ValueError('Cover inverse baseline changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed cover dependency: '+name)
    projected={}
    for name,row in data['files'].items():
        current=(root/name).read_bytes()
        if current!=row['after'].encode() or hashlib.sha256(current).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed cover source: '+name)
        if hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Cover preimage differs: '+name)
        projected[name]=row['before']
    return projected
