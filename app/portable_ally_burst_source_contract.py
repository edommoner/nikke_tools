"""Finite reviewed cast/admission delta; no unrelated source changes admitted."""
import hashlib,json
from pathlib import Path

def baseline_source(root,name,source):
    rows=json.loads((Path(root)/'tests/fixtures/portable-ally-burst-source-delta.json').read_text())['sources']
    if name not in rows:return source,False
    row=rows[name]
    assert hashlib.sha256(source.encode()).hexdigest()==row['current_sha256'],'Unreviewed ally-burst source: '+name
    assert source.count(row['current'])==1,'Missing or ambiguous ally-burst delta: '+name
    baseline=source.replace(row['current'],row['baseline'],1)
    assert hashlib.sha256(baseline.encode()).hexdigest()==row['baseline_sha256'],'Ally-burst historical source changed: '+name
    return baseline,True
