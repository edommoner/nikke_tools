"""Reviewed mode-reference delta; original source hashes remain authoritative."""
import hashlib,json
from pathlib import Path

def baseline_source(root,name,source):
    rows=json.loads((Path(root)/'tests/fixtures/portable-mode-capacity-source-delta.json').read_text())['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],('Weapon phase statements or signature changed: ' if name=='gpu/weapon_frame_phases.slang' else 'Unreviewed mode capacity source: ')+name
    for change in reversed(row['changes']):
        assert source.count(change['current'])==1,'Missing or ambiguous mode capacity delta: '+name
        source=source.replace(change['current'],change['baseline'],1)
    assert hashlib.sha256(source.encode()).hexdigest()==row['baseline_sha256'],'Mode capacity historical source changed: '+name
    return source,True
