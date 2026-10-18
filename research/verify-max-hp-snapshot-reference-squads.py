"""Validate authored interactions and raw definitions before GPU comparison."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('snapshot_cpu_squads',ROOT/'scripts/verify-max-hp-snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from calculator.buff_manager import BuffManager
from effect_runtime import pool
original=BuffManager._activate;observed=[];rows=[]
def activate(manager,effect,caster,t,*args,**kwargs):
 result=original(manager,effect,caster,t,*args,**kwargs)
 if effect.get('stat')=='max_hp_from_max_hp_pct':
  observed.extend(dict(time=t,value=ab.hp_bonus_flat,caster=caster) for ab in pool(manager,'max_hp_snapshot').values() if ab.effect is effect and ab.caster==caster)
 return result
for name,body,extra in m.fixtures():
 observed.clear()
 with patch.object(BuffManager,'_activate',activate),m.m.s.v.context(name,extra):result=m.m.s.v.v.a.evaluate(body)
 row=dict(name=name,passed=any(item['value']>0 for item in observed),total_damage=result['total_damage'],snapshot_activations=len(observed),positive_activations=sum(item['value']>0 for item in observed))
 rows.append(row);print(json.dumps(row),flush=True)
report=dict(passed=len(rows)==5 and all(row['passed'] for row in rows),scope='CPU fixture activation only; GPU comparison pending.',cases=rows,
 source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')})
(ROOT/'research/max-hp-snapshot-reference-squads.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
