"""Exact kind1 scoped-removal admission, projected before prior named-route proof."""
import hashlib,json
from pathlib import Path
def project_sources(root,sources=None):
    root=Path(root);sources=dict(sources or {});data=json.loads((root/'tests/fixtures/portable-named-enemy-removal-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text());assert hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed named-enemy removal source: '+name
        assert current.count(row['current'])==1
        old=current.replace(row['current'],row['baseline'],1);assert hashlib.sha256(old.encode()).hexdigest()==row['baseline_sha256']
        sources[name]=old
    return sources
