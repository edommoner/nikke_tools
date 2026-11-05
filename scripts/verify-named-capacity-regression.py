"""v30 regressions grouped by backend to avoid repeated PTX recompilation."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
named=load('named_capacity_combined','scripts/verify-named-capacity-detail.py')
cap=load('capacity_combined','scripts/verify-capacity-detail.py')
catalog=load('named_catalog_combined','scripts/verify-catalog-batch-detail.py')
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def report(rows,hashes,**kw):return dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,objective_complete=False,**kw)
def save(path,r,hashes):
    assert all(sha(p)==h for p,h in hashes.items()),'Sources changed during verification'
    r['source_sha256']={**r.get('source_sha256',{}),**hashes}
    (ROOT/path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert r['passed'],path
