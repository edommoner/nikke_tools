"""Portable target-rule parser versus original boss parser; no GPU."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app')]
import engine_worker
from calculator.boss_pattern import _target_rule
from portable_enemy_target_specs import target_rule

def main():
 rows=[]
 targets=['all','random:1','random:2','random:5','random:99','random:0002','top_atk:1','top_atk:8','slot:5,1,3,1','slot: 2, 4','slot:0','slot:6','slot:','random:0','random:-1','all:1','other:1']
 for target in targets:
  for ignore in (False,True,'bad'):
   spec=dict(target=target,ignore_taunt=ignore);native=actual=None;ne=ae=None
   try:native=_target_rule(spec,'portable-policy-check',5)
   except (ValueError,TypeError) as e:ne=type(e).__name__
   try:actual=target_rule(spec)
   except (ValueError,TypeError) as e:ae=type(e).__name__
   assert bool(ne)==bool(ae),(spec,ne,ae,native,actual)
   if native is not None:
    rule={'all':0,'slot':1,'random':2,'top_atk':3}[native['rule']]
    n=len(native['slots']) if rule==1 else min(native['n'],5)
    slots=sum((who+1)<<(3*i) for i,who in enumerate(native['slots']))
    assert actual==[rule,n,slots,int(native['ignore_taunt'])],(spec,native,actual)
   rows.append(dict(spec=spec,passed=True,native=native,portable=actual,rejected=bool(ne)))
 paths=['app/portable_enemy_target_specs.py','research/verify-enemy-target-spec.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']
 r=dict(passed=True,cpu_only=True,cases=rows,gpu_production_admission_enabled=False,source_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},scope='51 parser cases; counts above5 normalize to5 because victim population is at most5. No GPU execution or boss scheduling certification.')
 (R/'research/portable-enemy-target-spec-native.json').write_text(json.dumps(r,indent=2)+'\n');print(len(rows),'portable victim rules match original parser')
if __name__=='__main__':main()
