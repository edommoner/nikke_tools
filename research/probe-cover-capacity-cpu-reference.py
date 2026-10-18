"""CPU-only independent reference for max-HP-based cover capacity, not GPU proof."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from calculator.buff_manager import BuffManager,ActiveBuff
def buff(stat,value,caster='source',recipient='receiver',scaling=None,stack=1,expires=math.inf):
    e=dict(stat=stat,fixed_value=value,max_stack=3 if stack>1 else 1)
    if scaling:e['scaling']=scaling
    return ActiveBuff(e,caster,[recipient],0,expires,stack=stack)
def manager(effects,sourceHP=1000,receiverHP=2000,current=100,previous=100,sourcePct=100):
    bm=object.__new__(BuffManager);bm._active=effects
    bm.state=dict(base_stats={'source':{'hp':sourceHP},'receiver':{'hp':receiverHP}},hp_pct={'source':sourcePct,'receiver':100},cover_base_hp={'receiver':100},cover_hp={'receiver':current},cover_max_hp={'receiver':previous},down=set())
    bm._by_stat=lambda stat:[ab for ab in bm._active if ab.effect.get('stat')==stat]
    bm._invalidate_buffs_cache=lambda:None
    return bm
rows=[]
def check(name,bm,expectedCapacity,expectedCurrent=None,t=0):
    capacity=bm.cover_max_hp('receiver',t);bm.sync_cover_hp('receiver',t)
    row=dict(name=name,capacity=capacity,expected_capacity=expectedCapacity,current=bm.state['cover_hp']['receiver'],stored_maximum=bm.state['cover_max_hp']['receiver'])
    row['passed']=math.isclose(capacity,expectedCapacity,abs_tol=1e-10) and row['stored_maximum']==capacity and (expectedCurrent is None or math.isclose(row['current'],expectedCurrent,abs_tol=1e-10));rows.append(row)
flat=lambda **kw:buff('cover_hp_pct',10,scaling='max_hp',**kw)
check('caster-not-recipient-maximum',manager([flat()]),200,200)
check('live-caster-HP-bonus',manager([flat(),buff('max_hp_pct',50,recipient='source')]),250,250)
check('base-percentage-plus-caster-flat',manager([flat(),buff('cover_hp_pct',20)]),220,220)
check('stacked-caster-capacity',manager([flat(stack=3)]),400,400)
check('expiry-clamps-existing-cover',manager([flat(expires=1)],current=180,previous=200),100,100,t=1)
check('broken-cover-never-revives-from-capacity',manager([flat()],current=0),200,0)
check('increased-capacity-adds-only-difference',manager([flat()],current=40),200,140)
bm=manager([flat()]);bm.state['down']={'source'};check('down-caster-active-capacity-persists',bm,200,200)
check('caster-HP-bonus-dynamic-lost-HP',manager([flat(),buff('max_hp_only_pct',1.5,recipient='source',scaling='lost_hp_pct')],sourcePct=50),275,275)
catalog=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
carriers=[dict(character=name,name=e.get('name'),stat=e.get('stat'),target=e.get('target')) for name,effects in catalog.items() for e in effects if e.get('scaling')=='max_hp' and e.get('stat')=='cover_hp_pct']
files=['research/probe-cover-capacity-cpu-reference.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/data/parsed_skills.json','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py']
r=dict(cpu_reference_verified=all(x['passed'] for x in rows),gpu_implemented=False,objective_complete=False,direct_state_queries=True,whole_squad_verified=False,cases=rows,raw_carriers=carriers,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-cover-capacity-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=r['cpu_reference_verified'],cases=len(rows),raw_carriers=carriers,gpu_implemented=False),ensure_ascii=True));raise SystemExit(0 if r['cpu_reference_verified'] else 1)
