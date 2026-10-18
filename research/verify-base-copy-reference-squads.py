"""Read-only fixture activation and source-selection evidence, CPU only."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('copy_cpu_fixtures',ROOT/'scripts/verify-base-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from effect_runtime import pool
original=m.BuffManager._activate;observed=[];rows=[]
def activate(manager,effect,caster,t,*args,**kwargs):
 result=original(manager,effect,caster,t,*args,**kwargs)
 if effect.get('stat') in m.POLICIES:
  observed.extend(dict(time=t,owner=caster,source=carrier.copy_source,basis=carrier.copy_basis,stat=effect['stat']) for carrier in pool(manager,'base_stat_copy').values() if carrier.effect is effect and carrier.caster==caster)
 return result
files=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
for name,body,extra in m.fixtures():
 observed.clear()
 with patch.object(m.BuffManager,'_activate',activate),m.m.s.v.context(name,extra):result=m.m.s.v.v.a.evaluate(body)
 row=dict(name=name,passed=any(value['basis']>0 for value in observed),total_damage=result['total_damage'],copy_activations=len(observed),sources=sorted({value['source'] for value in observed if value['source'] is not None}))
 rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
stable=all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
report=dict(passed=stable and len(rows)==11 and all(row['passed'] for row in rows),scope='CPU fixture activation only; GPU battle comparison pending.',cases=rows,source_stable=stable,source_sha256=hashes)
(ROOT/'research/base-copy-reference-squads.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
