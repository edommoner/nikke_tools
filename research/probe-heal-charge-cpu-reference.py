"""Hand-derived received-healing charge arithmetic; no GPU/game parity claim."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('charge_runtime',ROOT/'scripts/staged-heal-charge-runtime.py');runtime=importlib.util.module_from_spec(sp);sp.loader.exec_module(runtime);runtime.install()
from calculator.buff_manager import BuffManager,ActiveBuff
import heal_charge_compat as m
N=['a','b','c'];rows=[]
def setup(hp=100):
    bm=object.__new__(BuffManager);bm.squad_names=N;bm._active=[];bm.state={'hp':{n:hp for n in N},'base_stats':{n:{'hp':100,'atk':200} for n in N}}
    bm.is_down=lambda n:False;bm.effective_max_hp=lambda n:100;bm.final_atk=lambda n,t:200
    bm._by_stat=lambda stat:[a for a in bm._active if a.effect.get('stat')==stat]
    bm._get_value=lambda eff,ab,*args:eff.get('fixed_value',0)*ab.stack
    bm._live=lambda a,n,t:t<a.expires_at and n in (a.target_chars or [])
    bm.sync_hp=lambda n:None
    return bm
def carrier(bm,name='pool',owner='a',value=150,targets=None,end=1,stat=None,ref=None):
    eff=dict(name=name,type='buff',stat=stat or m.STAT,fixed_value=value)
    if ref is not None:eff['target_effect']=ref
    ab=ActiveBuff(eff,owner,targets or [owner],0,end);bm._active.append(ab)
    bm.snapshot_heal_charge(eff,owner,0);return ab
def check(name,actual,expected):
    ok=actual==expected;rows.append(dict(name=name,actual=actual,expected=expected,passed=ok));assert ok,(name,actual,expected)
bm=setup();a=carrier(bm);check('empty-pool-ATK-capacity-not-HP',[a.heal_charge_current,a.heal_charge_base_cap,bm.state['hp']['a']],[0,300,100])
check('full-HP-positive-healing-enters-pool',bm.apply_storage_body_heal('a',50,.1),100);check('full-amount-not-only-overheal',a.heal_charge_current,50)
bm.state['hp']['a']=90;bm.apply_storage_body_heal('a',50,.2);check('full-amount-not-only-effective-HP-gain',[bm.state['hp']['a'],a.heal_charge_current],[90,100])
# The underlying v40 helper returns HP; its caller commits it. The new hook
# must preserve that contract while observing the complete allocated amount.
bm.collect_heal_charge('a',10000,.3);check('deposit-saturates-at-cap',a.heal_charge_current,300)
bm.collect_heal_charge('a',-50,.4);bm.collect_heal_charge('a',0,.4);check('nonpositive-does-not-charge',a.heal_charge_current,300)
check('pool-is-not-a-damage-buffer',bm.absorb_heal_storage('a',50,.4),50)
check('discharge-consumes-before-delivery',bm.take_heal_charge('pool','a',.5),300)
check('repeat-discharge-is-zero',bm.take_heal_charge('pool','a',.5),0)
bm.collect_heal_charge('a',50,.6);check('live-consumed-pool-does-not-refill',a.heal_charge_current,0)
bm.final_atk=lambda n,t:400;bm.snapshot_heal_charge(a.effect,'a',.7);check('reactivation-resets-and-resnapshots',[a.heal_charge_current,a.heal_charge_base_cap,a.heal_charge_done],[0,600,False])
bm=setup();a=carrier(bm);bm.final_atk=lambda n,t:999;check('later-ATK-does-not-change-base-snapshot',bm.heal_charge_capacity(a,.2),300)
boost=carrier(bm,'capacity bonus',value=20,stat=m.BOOST,ref='pool');check('named-live-capacity-bonus',bm.heal_charge_capacity(a,.2),360)
bm.collect_heal_charge('a',340,.2);boost.expires_at=.3;bm.collect_heal_charge('a',50,.4);check('capacity-decrease-keeps-already-collected-amount',a.heal_charge_current,340)
check('expired-bonus-no-longer-opens-deposit-room',bm.heal_charge_capacity(a,.4),300)
carrier(bm,'wrong pool',value=100,stat=m.BOOST,ref='different');check('named-capacity-bonus-is-scoped',bm.heal_charge_capacity(a,.4),300)
carrier(bm,'other member',owner='b',value=100,stat=m.BOOST);check('bonus-must-affect-pool-owner',bm.heal_charge_capacity(a,.4),300)
bm=setup();a=carrier(bm);bm.collect_heal_charge('a',80,.2);bm.collect_heal_charge('a',100,1);check('expiry-boundary-no-new-deposit',a.heal_charge_current,80)
bm._active=[];check('removed-without-state-end-does-not-discharge',bm.take_heal_charge('pool','a',1),0)
bm.latch_heal_charge_end('pool','a');check('removed-pool-survives-state-end-for-release',bm.take_heal_charge('pool','a',1),80)
bm=setup();a=carrier(bm);bm.collect_heal_charge('a',80,.1);bm._active=[];bm.discard_removed_heal_charge({a.uid});bm.latch_heal_charge_end('pool','a');check('later-same-name-end-cannot-resurrect-cleansed-pool',bm.take_heal_charge('pool','a',1),0)
bm=setup();a=carrier(bm);b=carrier(bm,owner='b');bm.collect_heal_charge('a',50,.1);bm.collect_heal_charge('b',80,.1)
check('same-name-other-owner-cannot-be-consumed',bm.take_heal_charge('pool','a',.2),50);check('other-owner-keeps-own-quantity',bm.take_heal_charge('pool','b',.2),80)
bm=setup();a=carrier(bm);b=carrier(bm,name='second');bm.collect_heal_charge('a',90,.1);check('distinct-carriers-each-receive-amount',[a.heal_charge_current,b.heal_charge_current],[90,90])
bm.is_down=lambda n:n=='a';bm.collect_heal_charge('a',50,.2);check('down-recipient-does-not-charge',a.heal_charge_current,90);check('down-source-cannot-release',bm.take_heal_charge('pool','a',.2),0)
bm._active=[];bm.latch_heal_charge_end('pool','a');check('down-at-end-discards-retained-quantity',[a.heal_charge_current,a.heal_charge_done],[0,True])
bm=setup();a=carrier(bm);bm.collect_heal_charge('a',50,.1);calls=[]
bm._resolve_target=lambda target,caster:['a','b','a']
bm.heal_received_mult=lambda name,t,heal_source:2 if name=='a' else 3
bm.apply_shared_body_heal=lambda name,amount,t:calls.append(('heal',name,amount))
bm.notify=lambda event,t,name,heal_source:calls.append(('notify',name,heal_source))
m.discharge(bm,{'target_effect':'pool'},'a',.2,None)
check('fresh-release-potency-ordered-duplicates-and-notifications',calls,[('heal','a',100),('notify','a','a'),('heal','b',150),('notify','b','a'),('heal','a',100),('notify','a','a')])
check('release-clears-before-first-recipient',a.heal_charge_done,True)
from calculator import timeline
from runner import sim
check('runner-simulation-binding-preserved',timeline.simulate is sim.simulate,True)
m.install();check('installation-is-idempotent',getattr(BuffManager,'_nikke_heal_charge',False),True)
raw=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
effects=[dict(character=n,effect=e) for n,es in raw.items() for e in es if e.get('stat') in (m.STAT,m.BOOST,'heal_overcharge_discharge')]
files=['research/probe-heal-charge-cpu-reference.py','scripts/staged-heal-charge-runtime.py','research/staging/v42/app/heal_charge_compat.py','app/engine_compat.py','app/heal_sharing_compat.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
report=dict(passed=True,stage_only=True,cpu_model_extended=True,in_game_rules_verified=False,gpu_verified=False,whole_squad_verified=False,objective_complete=False,cases=rows,raw_effects=effects,reference_urls=['https://www.prydwen.gg/nikke/characters/delta-ninja-thief','https://nikke.gg/characters/delta-ninja-thief/','https://trashif.com/nikke/delta-ninja-thief-analysis/'],model_choices=['Full positive allocated body healing enters, including full HP, before HP clamp.','Final ATK is snapshotted at activation; live named capacity bonuses control deposit room. Capacity reductions do not destroy already collected amounts.','Refresh resets quantity and source snapshot. Owner/name scoped discharge consumes matching pools before new heals and original-target notifications.','New release healing receives current outgoing/received potency and normal sharing/storage rules. Repair, revive, max-HP grants and damage do not charge or spend this pool.','State-end retains removed pool; cleanse/down without state-end does not. Snapshot and cross-effect interactions are declared reference rules, not universal in-game proof.'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-heal-charge-cpu-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows),raw_effects=len(effects),gpu_verified=False)))
