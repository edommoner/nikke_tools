"""Exact historical source inverse, not generated-code normalization or a seal."""
import hashlib,json,re
from pathlib import Path
LEDGER_SHA256='93afb12ae4b67224a4cfe099ccf64bead769c52229d85ddfe0b45bfbc282f2f6'
def project_sources(root):
    root=Path(root);raw=(root/'tests/fixtures/portable-weighted-incoming-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Weighted source inverse ledger changed')
    data=json.loads(raw)
    if data['schema']!=1 or data['normalizer_changed'] is not False or data['baseline_commit']!='e93182fb61ed6fce5cb7d02e13e1aa5ac59ec840':raise ValueError('Weighted source baseline changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed weighted dependency: '+name)
    projected={}
    for name,row in data['files'].items():
        text=(root/name).read_text()
        if hashlib.sha256(text.encode()).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed weighted source: '+name)
        for hunk in reversed(row['hunks']):
            if text.count(hunk['after'])!=1:raise ValueError('Ambiguous weighted source inverse: '+name)
            text=text.replace(hunk['after'],hunk['before'],1)
        if hashlib.sha256(text.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Weighted source preimage differs: '+name)
        projected[name]=text
    return projected
def projected_hashes(root,source,sources):
    root=Path(root).resolve();found={}
    def visit(path):
        name=path.relative_to(root).as_posix()
        if name in found:return
        raw=sources[name].encode() if name in sources else path.read_bytes();found[name]=hashlib.sha256(raw).hexdigest()
        for inc in re.findall(rb'^\s*#include\s+"([^"]+)"',raw,re.M):visit((path.parent/inc.decode()).resolve())
    visit(root/source);return found
def historical_hashes(root,source):return projected_hashes(root,source,project_sources(root))
