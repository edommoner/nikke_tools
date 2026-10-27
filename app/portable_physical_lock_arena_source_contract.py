"""Exact opt-in state delta; generated-code normalization is unchanged."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
 from portable_physical_lock_cover_source_contract import project_sources as cover
 root=Path(root);out=cover(root,sources);data=json.loads((root/'tests/fixtures/portable-physical-lock-arena-source-delta.json').read_text())
 for name,digest in data['added_sources'].items():
  if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise AssertionError('Unreviewed target-count dependency: '+name)
 for name,row in data['sources'].items():
  current=out.get(name,(root/name).read_text())
  if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise AssertionError('Unreviewed target-count source: '+name)
  if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise AssertionError('Lock historical baseline changed: '+name)
  out[name]=row['baseline']
 return out

def project_backend_source(root,source=None):
 from portable_physical_lock_cover_source_contract import project_backend_source as cover
 root=Path(root);name='app/portable_backend.py';current=cover(root,source)
 row=json.loads((root/'tests/fixtures/portable-physical-lock-arena-source-delta.json').read_text())['sources'][name]
 if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed physical lock arena transport source')
 if hashlib.sha256(row['baseline'].encode()).hexdigest()!=row['baseline_sha256']:raise ValueError('Historical physical lock transport baseline changed')
 return row['baseline']
