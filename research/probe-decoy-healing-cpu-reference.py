"""CPU-only snapshot semantics for the next decoy-healing GPU port."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from calculator.buff_manager import BuffManager,ActiveBuff
def carrier(current=20,maximum=100,at=0,end=math.inf,stat='decoy',other=None):
    a=ActiveBuff({'stat':stat},'source',['receiver'],at,end);a.decoy_per_target={'receiver':current};a.decoy_max_per_target={'receiver':maximum}
    if other is not None:a.decoy_per_target['other']=other;a.decoy_max_per_target['other']=100
    return a
def check(name,active,amount,expected,quantities,t=0,capacity=None):
    bm=object.__new__(BuffManager);bm._active=active;invalidations=[];bm._invalidate_buffs_cache=lambda:invalidations.append(True)
    actual=bm.heal_decoy('receiver',amount,t);observed=[dict(a.decoy_per_target) for a in active];expected_quantities=[{'receiver':x} if isinstance(x,(int,float)) else x for x in quantities]
    row=dict(name=name,actual_healed=actual,expected_healed=expected,quantities=observed,expected_quantities=expected_quantities,capacity=bm.decoy_capacity('receiver'),cache_invalidations=len(invalidations))
    row['passed']=actual==expected and observed==expected_quantities and len(invalidations)==int(expected>0) and (capacity is None or row['capacity']==capacity);return row
rows=[
    check('partial-existing-decoy',[carrier()],50,50,[70],capacity=100),
    check('overheal-clamps-to-snapshot',[carrier()],500,80,[100]),
    check('negative-heal-is-noop',[carrier()],-10,0,[20]),
    check('absent-carrier-is-not-created',[],50,0,[],capacity=0),
    check('expired-carrier-cannot-be-healed',[carrier(end=.1)],50,0,[20],t=.1),
    check('newest-activation-first',[carrier(10,at=0),carrier(20,at=1)],100,100,[30,100],t=2,capacity=200),
    check('equal-time-keeps-resident-order-not-UID',[carrier(10,at=0),carrier(20,at=0)],50,50,[60,20]),
    check('empty-recipient-in-retained-shared-carrier',[carrier(0,other=50)],25,25,[{'receiver':25,'other':50}]),
    check('shield-carrier-is-not-a-decoy',[carrier(stat='shield_from_max_hp_pct')],50,0,[20],capacity=0),
    check('missing-recipient-is-not-created',[ActiveBuff({'stat':'decoy'},'source',['other'],0,math.inf)],50,0,[{}],capacity=0),
]
catalog=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
raw=[dict(character=name,name=e.get('name'),scaling=e.get('scaling'),timing=e.get('trigger',{}).get('timing'),tick_interval=e.get('tick_interval')) for name,effects in catalog.items() for e in effects if e.get('stat')=='decoy_heal_pct']
files=['research/probe-decoy-healing-cpu-reference.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py']
r=dict(cpu_reference_verified=all(x['passed'] for x in rows),gpu_implemented=False,objective_complete=False,direct_state_queries=True,whole_squad_verified=False,cases=rows,raw_carriers=raw,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-decoy-healing-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=r['cpu_reference_verified'],cases=len(rows),raw_carriers=raw,gpu_implemented=False),ensure_ascii=True));raise SystemExit(0 if r['cpu_reference_verified'] else 1)
