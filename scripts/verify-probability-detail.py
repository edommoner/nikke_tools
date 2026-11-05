"""Expected probability accumulators and isolated hit contexts on CPU/GPU."""
import json,sys,math,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,coverage
spec=importlib.util.spec_from_file_location('probability_predicate_oracle',ROOT/'scripts/verify-predicates-detail.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;oracle=base.oracle;periodic=base.periodic;NAMES=base.NAMES

def primitives():
 out=[]
 def build(name,effects,events,expected,who=0,diagnostic=0):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  for t,event,actor,core,crit in events:script.append([t,0,event,actor,0,-1,core,crit])
  t=events[-1][0]+.01 if events else .1;script.extend([[t,2,0,who,-1,0,0,0],[t,2,106,who,diagnostic,1,0,0]])
  out.append((name,p,script,expected))
 events=lambda n,event=7,who=0,core=0,crit=0:[(.1*(i+1),event,who,core,crit) for i in range(n)]
 buff=lambda conditions,**kw:E('count','buff','atk_pct',1,event='on_attack',condition=conditions,max_stack=100,**kw)
 build('quarter-probability-count-and-remainder',[(0,buff(['prob:25']))],events(9),2)
 build('decimal-accumulation-keeps-python-threshold-phase',[(0,buff(['prob:10']))],events(10),0)
 build('negative-probability-remains-negative-without-clamping',[(0,buff(['prob:-25']))],events(4),0)
 build('above-hundred-fires-once-and-keeps-excess',[(0,buff(['prob:250']))],events(3),3)
 build('level-dependent-probability',[(0,buff(['prob:{0}'],trigger_values={'1':25,'10':50}))],events(5),2)
 build('missing-probability-placeholder-is-false-without-accumulation',[(0,buff(['prob:{0}']))],events(5),0)
 build('repeated-probability-conditions-share-one-effect-accumulator',[(0,buff(['prob:50','prob:50']))],events(8),0)
 build('earlier-state-gate-does-not-advance-probability',[(0,buff(['self_state:missing','prob:25']))],events(3),0)
 build('later-state-gate-still-advances-probability',[(0,buff(['prob:25','self_state:missing']))],events(3),0)
 build('earlier-stat-gate-does-not-advance-probability',[(0,buff(['self_stat_above:atk_pct:100','prob:25']))],events(3),0)
 build('later-stat-gate-still-advances-probability',[(0,buff(['prob:25','self_stat_above:atk_pct:100']))],events(3),0)
 build('spent-activation-budget-still-evaluates-probability',[(0,buff(['prob:25'],max_trigger=1))],events(7),1)
 build('distinct-identically-named-effects-keep-independent-accumulators',[(0,buff(['prob:25'])),(0,buff(['prob:50']))],events(4),3)
 build('different-casters-keep-independent-accumulators',[(0,buff(['prob:50'])),(1,buff(['prob:50']))],[(.1,7,0,0,0),(.2,7,1,0,0),(.3,7,0,0,0)],1)
 build('not-core-half-probability-with-context',[(0,E('count','buff','atk_pct',1,event='hit_count',condition=['not_core'],max_stack=100))],events(7,8,core=.5),3)
 build('not-core-default-context-is-one',[(0,buff(['not_core']))],events(3),3)
 build('not-core-full-core-never-fires',[(0,E('count','buff','atk_pct',1,event='hit_count',condition=['not_core'],max_stack=100))],events(4,8,core=1),0)
 build('probability-and-noncore-use-separate-state',[(0,E('count','buff','atk_pct',1,event='hit_count',condition=['prob:50','not_core'],max_stack=100))],events(8,8,core=.5),2)
 build('root-hit-context-is-restored-after-nested-named-events',[(0,E('mark','buff','',0,event='hit_count')),(0,E('nested','buff','atk_pct',10,event='event:mark',condition=['not_core'],max_stack=100)),(0,E('outer','buff','atk_pct',1,event='hit_count',condition=['not_core'],max_stack=100))],events(3,8,core=1),10)
 build('nested-notify-does-not-inherit-crit-hit-context',[(0,E('mark','buff','',0,event='hit_count')),(0,E('nested','buff','atk_pct',10,event='event:mark',condition=['trigger_hit_crit'],max_stack=100)),(0,E('outer','buff','atk_pct',1,event='hit_count',condition=['trigger_hit_crit'],max_stack=100))],events(3,8,crit=1),3)
 build('permanent-passive-probability-evaluates-on-registration',[(0,E('count','buff','atk_pct',1,event='passive',condition=['prob:25']))],[],1)
 p=buff(['prob:50']);p['trigger']['timing']=['on_attack','on_attack']
 build('duplicate-event-index-entries-share-probability-state',[(0,p)],events(3),3)
 return out

def full_scenarios():
 n=NAMES
 yield 'full-ordered-probability-gates-and-nested-events',{n[0]:[E('mark','buff','',0,event='on_attack'),E('chance','buff','atk_pct',5,'all_allies',event='on_attack',condition=['prob:12.5'],duration=2,max_stack=10),E('nested chance','buff','crit_dmg',2,'all_allies',event='event:mark',condition=['prob:25'],duration=2,max_stack=10)]},12,{}
 yield 'full-finite-passive-probability-and-expiry',{n[0]:[E('passive chance','buff','atk_pct',20,'all_allies',event='passive',condition=['prob:12.5'],duration=.1)]},5,{}
 yield 'full-probability-periodic-and-instant-timer',{n[0]:[E('pulse','buff','atk_pct',2,'all_allies',event='every:0.5s',condition=['prob:25'],duration=3,max_stack=10),E('heal','instant','heal_hp_pct',1,'all_allies',event='on_attack_count:2',condition=['prob:50'],tick_interval=.5,duration=1)]},10,{}
 for core in (0,2,50):
  yield 'full-noncore-context-'+str(core),{n[0]:[E('three pellets','buff','pellet_count_fixed',3,'all_allies'),E('hit chance','buff','atk_pct',10,'all_allies',event='hit_count',condition=['not_core'],duration=.5,max_stack=3),E('outer mark','buff','',0,event='hit_count'),E('nested default','buff','crit_dmg',5,'all_allies',event='event:outer mark',condition=['not_core'],duration=.5,max_stack=3)],n[2]:[E('charge chance','buff','charge_dmg_pct',10,event='hit_count',condition=['prob:50','not_core'],duration=1,max_stack=3)]},10,{'core_px':core}
