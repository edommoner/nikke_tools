"""Independent hand-derived link arithmetic; no GPU acceptance claim."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sharing_runtime',ROOT/'scripts/staged-heal-sharing-runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime);runtime.install()
from calculator.buff_manager import BuffManager,ActiveBuff
N=['a','b','c','d','e'];rows=[]
def setup():
    bm=object.__new__(BuffManager);bm.squad_names=N;bm._active=[];bm.state={'hp':{n:0 for n in N},'base_stats':{n:{'hp':1000} for n in N}}
    bm.is_down=lambda n:False;bm.effective_max_hp=lambda n:1000
    bm._by_stat=lambda stat:[a for a in bm._active if a.effect.get('stat')==stat]
    bm._live=lambda a,n,t:t<a.expires_at and n in (a.target_chars or [])
    bm.sync_hp=lambda n:None
    return bm
def carrier(bm,targets,end=10,stack=1,stat='heal_split'):
    a=ActiveBuff(dict(name='links'+str(len(bm._active)),type='buff',stat=stat,fixed_value=20),'a',targets,0,end);a.stack=stack;bm._active.append(a);return a
def check(name,actual,expected):
    ok=actual==expected;rows.append(dict(name=name,actual=actual,expected=expected,passed=ok));assert ok,(name,actual,expected)
def healed(bm,name='a',amount=80,t=0):
    bm.apply_shared_body_heal(name,amount,t);return list(bm.state['hp'].values())
bm=setup();check('no-links-exact-original',healed(bm),[80,0,0,0,0])
bm=setup();carrier(bm,['a']);carrier(bm,N);check('Rem-zero-RL-weights',bm.heal_share_plan('a',0),[('a',2),('b',1),('c',1),('d',1),('e',1)])
check('Rem-zero-RL-arithmetic',healed(bm,amount=60),[20,10,10,10,10])
bm=setup();carrier(bm,['a','b','c']);carrier(bm,N);check('Rem-two-RL-arithmetic',healed(bm),[20,20,20,10,10])
bm=setup();carrier(bm,['a','b']);carrier(bm,N);check('Rem-one-RL-arithmetic',healed(bm,amount=70),[20,20,10,10,10])
bm=setup();carrier(bm,['a','b','a','b'],stack=3);check('duplicates-and-stacks-are-one-link',healed(bm),[40,40,0,0,0])
bm=setup();carrier(bm,['a','b']);carrier(bm,['b','c']);carrier(bm,['d','e']);check('transitive-component-excludes-disconnected',healed(bm),[20,40,20,0,0])
bm=setup();carrier(bm,['a','b']);bm.state['hp']['a']=1000;check('full-HP-still-dilutes',healed(bm),[1000,40,0,0,0])
bm=setup();carrier(bm,['a','b']);carrier(bm,['a','c'],end=1);check('expired-links-removed',healed(bm,t=1),[40,40,0,0,0])
bm=setup();carrier(bm,['a','b','c']);bm.is_down=lambda n:n=='b';check('down-member-excluded',healed(bm),[40,0,40,0,0])
bm.is_down=lambda n:False;check('revived-member-rejoins',bm.heal_share_plan('a',0),[('a',1),('b',1),('c',1)])
bm=setup();carrier(bm,['a','b']);a=carrier(bm,['b','c']);base_live=bm._live;bm._live=lambda a,n,t:base_live(a,n,t) and n!='c';check('runtime-condition-per-member',healed(bm,amount=90),[30,60,0,0,0])
bm=setup();carrier(bm,['a','b']);order=[]
def mutate_on_first_sync(n):
    order.append(n)
    if n=='a':bm.is_down=lambda n:n=='b'
bm.sync_hp=mutate_on_first_sync;check('plan-frozen-before-HP-edges',healed(bm),[40,40,0,0,0]);check('delivery-in-squad-order',order,['a','b'])
bm=setup();carrier(bm,['a','b']);check('external-heal-enters-associated-component',healed(bm,'b'),[40,40,0,0,0])
bm=setup();carrier(bm,['a','b']);check('negative-amount-is-not-shared',healed(bm,amount=-5),[-5,0,0,0,0])
bm=setup();carrier(bm,['a','b']);s=carrier(bm,['b'],stat='heal_overcharge_store');bm.snapshot_heal_storage(s.effect,'a',0);bm.state['hp']['b']=990
check('allocated-overheal-fills-recipient-storage',healed(bm),[40,1000,0,0,0]);check('only-allocated-overflow-is-stored',bm.heal_storage_amount('b',0),30)
from calculator import timeline
from runner import sim
check('simulation-entry-points-bound',timeline.simulate is sim.simulate,True)
raw=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
carriers=[dict(character=n,effect=e) for n,es in raw.items() for e in es if e.get('stat')=='heal_split']
files=['research/probe-heal-sharing-cpu-reference.py','research/staging/v41/app/heal_sharing_compat.py','scripts/staged-heal-sharing-runtime.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
report=dict(passed=True,stage_only=True,cpu_model_extended=True,in_game_rules_verified=False,gpu_verified=False,whole_squad_verified=False,objective_complete=False,cases=rows,raw_carriers=carriers,reference_urls=['https://www.prydwen.gg/nikke/characters/rem','https://nikke.gg/rem-best-builds-teams-and-how-to-play/','https://nikke.gg/characterguides/crown/'],model_choices=['Connected component of live carriers, one weight per distinct live recipient per carrier, stacks do not multiply links.','Full HP consumes its share, no overflow redistribution.','Original target received multiplier and healer outgoing multiplier applied once before division; no extra recipient multipliers.','Frozen plan, squad-order synchronous HP edges, original-target heal_received only; portions do not recursively share.','Repair, revival, max-HP grants and negative amounts excluded.'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-heal-sharing-cpu-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,cases=len(rows),raw_carriers=[dict(character=c['character'],name=c['effect'].get('name')) for c in carriers]),ensure_ascii=True))
