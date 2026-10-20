"""Next enemy-target family:actual native taunters semantics;CPU only,no admission."""
import copy,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES

def main():
 rows=[]
 for owner in range(5):
  for target in ('self','all_allies','boss'):
   for value in (-5,0,100):
    for duration in (-1,2):
     for conditional in (False,True):
      e=dict(name='taunt-study',source='스킬1',type='buff',stat='taunt',fixed_value=value,target=target,duration=duration,trigger=dict(timing=['battle_start'],condition=['not_self_state:released'] if conditional else []))
      marker=dict(name='released',source='스킬2',type='buff',stat='',target='self',duration=-1,trigger=dict(timing=['on_attack'],condition=[]))
      class BM(BuffManager):
       def _register_all(self):self._effects=[(copy.deepcopy(e),NAMES[owner]),(copy.deepcopy(marker),NAMES[owner])];self._build_notify_index()
      chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
      bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000,**{'def':0}) for n in NAMES},enemy={'def':0},full_burst=False,rng_acc={}))
      for n in NAMES:bm.notify('battle_start',0,n)
      obs=[]
      for phase,t in [('initial',0),('condition-disabled',.5),('expired',2.5)]:
       bm.tick(t)
       if phase=='condition-disabled':bm.notify('on_attack',t,NAMES[owner])
       active=duration==-1 or t<duration
       if conditional and phase!='initial' and duration==-1 and target!='boss':active=False
       expected=[NAMES[0] if target=='all_allies' else NAMES[owner]] if active else []
       actual=bm.taunters(t);assert actual==expected,(owner,target,value,duration,conditional,phase,actual,expected)
       obs.append(dict(phase=phase,actual=actual,expected=expected))
      rows.append(dict(owner=owner,target=target,value=value,duration=duration,conditional=conditional,observations=obs))
 orders=[]
 for order in itertools.permutations(range(5)):
  raw=[(dict(name=f'taunt-{i}',source='스킬1',type='buff',stat='taunt',fixed_value=0,target='self',duration=-1,trigger=dict(timing=['on_attack'],condition=[])),NAMES[i]) for i in range(5)]
  class OrderedBM(BuffManager):
   def _register_all(self):self._effects=copy.deepcopy(raw);self._build_notify_index()
  chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
  bm=OrderedBM(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000,**{'def':0}) for n in NAMES},enemy={'def':0},full_burst=False,rng_acc={}))
  seen=set();observations=[]
  for j,who in enumerate(order):
   t=j/10;bm.tick(t);bm.notify('on_attack',t,NAMES[who]);seen.add(who);expected=[NAMES[i] for i in range(5) if i in seen];actual=bm.taunters(t);assert actual==expected,(order,j,actual,expected);observations.append(dict(time=t,actual=actual,expected=expected))
  orders.append(dict(activation_order=order,observations=observations))
 paths=['research/characterize-taunt-native.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
 report=dict(passed=True,cpu_only=True,gpu_admission_enabled=False,gpu_execution_performed=False,cases=rows,activation_order_cases=orders,
  rules=['Quantity sign/zero ignored','All-allies taunt contributes the first live recipient,not every member','Enemy-target taunt contributes the caster','Native enemy branch skips _live runtime-condition checks;allied branch rechecks eligible infinite conditions','Expiry always checked','Output order is squad order,not activation order'],
  scope='180 single-carrier cases plus120 multi-carrier activation orders;does not certify boss targeting,damage,death,stealth,RNG or GPU behavior',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
 (ROOT/'research/portable-taunt-native-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(rows),'single-carrier and',len(orders),'activation-order native cases passed;GPU admission unchanged')
if __name__=='__main__':main()
