"""Independent hand-derived buffer arithmetic and guarded CPU AST installation."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from calculator.buff_manager import BuffManager,ActiveBuff
path=ROOT/'research/staging/v40/app/healing_storage_compat.py';sp=importlib.util.spec_from_file_location('storage_cpu_reference',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.install()
rows=[]
def setup(hp=90,source_hp=1000):
    bm=object.__new__(BuffManager);bm.state={'hp':{'receiver':hp},'base_stats':{'receiver':{'hp':100}}};bm.squad_names=['source','receiver','other'];bm._active=[]
    bm.is_down=lambda who:False;bm.effective_max_hp=lambda who:source_hp if who=='source' else 100
    bm._get_value=lambda eff,ab,*args:eff['fixed_value']*ab.stack
    bm._by_stat=lambda stat:[a for a in bm._active if a.effect.get('stat')==stat]
    bm._live=lambda a,n,t:t<a.expires_at and n in (a.target_chars or [])
    return bm
def carrier(bm,name='buffer',value=20,at=0,end=1,targets=None):
    e=dict(name=name,type='buff',stat=m.STAT,fixed_value=value);a=ActiveBuff(e,'source',targets or ['receiver'],at,end);bm._active.append(a);m.snapshot(bm,e,'source',at);return a
def check(name,actual,expected):
    ok=actual==expected;rows.append(dict(name=name,actual=actual,expected=expected,passed=ok));assert ok,(name,actual,expected)
bm=setup();a=carrier(bm);check('new-buffer-is-empty-not-a-heal',[bm.heal_storage_amount('receiver',0),bm.heal_storage_capacity('receiver',0),bm.state['hp']['receiver']],[0,200,90])
hp=bm.apply_storage_body_heal('receiver',30,.1);bm.state['hp']['receiver']=hp;check('only-excess-enters-buffer',[hp,bm.heal_storage_amount('receiver',.1)],[100,20])
check('body-bound-damage-uses-buffer-first',[bm.absorb_heal_storage('receiver',15,.2),bm.heal_storage_amount('receiver',.2)],[0,5])
check('damage-overflow-passes-to-body',[bm.absorb_heal_storage('receiver',17,.3),bm.heal_storage_amount('receiver',.3)],[12,0])
bm.fill_heal_storage('receiver',999,.4);check('overfill-clamps',bm.heal_storage_amount('receiver',.4),200)
check('capacity-does-not-change-max-HP',bm.effective_max_hp('receiver'),100)
check('expiry-loses-reserve',[bm.heal_storage_amount('receiver',1),bm.heal_storage_capacity('receiver',1)],[0,0])
bm=setup(hp=100);a=carrier(bm);bm.fill_heal_storage('receiver',80,.1);check('HP-drain-is-based-on-body-HP-and-spends-reserve',[bm.reduce_storage_body_hp('receiver',100,10,.2),bm.heal_storage_amount('receiver',.2)],[100,70])
check('HP-drain-overflow',[bm.reduce_storage_body_hp('receiver',100,80,.3),bm.heal_storage_amount('receiver',.3)],[90,0])
bm=setup();a=carrier(bm);bm.apply_storage_body_heal('receiver',-5,.1);check('negative-heal-does-not-fill',bm.heal_storage_amount('receiver',.1),0)
check('missing-recipient-does-not-create-buffer',bm.fill_heal_storage('other',100,.1),0)
bm=setup(hp=100);a=carrier(bm,'old',at=0);b=carrier(bm,'new',at=.1);bm.fill_heal_storage('receiver',250,.2);check('newest-carrier-filled-first',[a.heal_store_current['receiver'],b.heal_store_current['receiver']],[50,200])
bm.absorb_heal_storage('receiver',80,.3);check('newest-carrier-spent-first',[a.heal_store_current['receiver'],b.heal_store_current['receiver']],[50,120])
bm=setup();a=carrier(bm,'same-a');b=carrier(bm,'same-b');bm.fill_heal_storage('receiver',50,.1);check('equal-time-preserves-resident-order',[a.heal_store_current['receiver'],b.heal_store_current['receiver']],[50,0])
a.effect['fixed_value']=2;a.expires_at=2;m.snapshot(bm,a.effect,'source',.2);check('refresh-keeps-quantity-clamped-to-new-capacity',[a.heal_store_current['receiver'],a.heal_store_capacity['receiver']],[20,20])
a.expires_at=3;m.snapshot(bm,a.effect,'source',2);check('expired-quantity-not-resurrected-on-refresh',a.heal_store_current['receiver'],0)
bm=setup(hp=100);a=carrier(bm,targets=['receiver','other']);bm.fill_heal_storage('receiver',50,.1);check('recipients-have-separate-quantities',[bm.heal_storage_amount('receiver',.1),bm.heal_storage_amount('other',.1)],[50,0])
bm.is_down=lambda who:who=='receiver';check('down-recipient-cannot-use-reserve',[bm.heal_storage_amount('receiver',.2),bm.absorb_heal_storage('receiver',20,.2)],[0,20])
from calculator import timeline
from runner import sim
m.install();check('both-simulation-entry-points-bound',sim.simulate is timeline.simulate,True)
heal={'source':'스킬2','type':'instant','stat':'heal_hp_pct','trigger':{'timing':['burst_cast']}};storage={'source':'스킬3','type':'buff','stat':m.STAT,'trigger':{'timing':['burst_cast']}};unrelated={'name':'other'}
check('same-cast-storage-before-passive-heal',[id(x) for x in m.storage_before_burst_heal([unrelated,heal,storage])],[id(x) for x in [unrelated,storage,heal]])
ordered=[storage,unrelated,heal];check('already-correct-definition-order-is-unchanged',m.storage_before_burst_heal(ordered) is ordered,True)
data=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
raw=[dict(character=name,name=e.get('name'),target=e.get('target'),trigger=e.get('trigger'),max_stack=e.get('max_stack',1),duration=e.get('duration')) for name,es in data.items() for e in es if e.get('stat')==m.STAT]
files=['research/probe-healing-storage-cpu-reference.py','research/staging/v40/app/healing_storage_compat.py','app/outgoing_healing_compat.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
if (ROOT/'app/healing_storage_compat.py').exists():
    assert (ROOT/'app/healing_storage_compat.py').read_bytes()==path.read_bytes()
    files.append('app/healing_storage_compat.py')
r=dict(passed=True,cpu_model_extended=True,in_game_rules_verified=False,gpu_verified_by_this_report=False,whole_squad_verified=False,objective_complete=False,cases=rows,raw_carriers=raw,reference_urls=['https://www.prydwen.gg/nikke/characters/marciana','https://nikke.gg/characterguides/marciana/','https://wiki3.jp/nikke/page/3640'],model_choices=['Separate overheal buffer, no changes to max HP or HP-percent predicates.','Snapshot source final maximum HP on activation.','Reapplication retains quantity up to new cap; distinct carriers fill/consume newest first with stable ties.','Body-bound attack damage and current-HP drain spend reserve first; ATK-storage/discharge and sharing remain separate.','S3-storage/S2-self-burst-heal pair is normalized to storage-before-heal, preserving unrelated clauses and effect object identities.'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-healing-storage-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,independent_cases=len(rows),raw_carriers=raw,gpu_verified_by_this_report=False),ensure_ascii=True))
