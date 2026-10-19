"""Native-only contract audit before admitting new common GPU effect kinds."""
import copy,json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES

def base(polarity='beneficial',cap=5):
 return dict(name='stack',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=2,max_stack=cap,polarity=polarity,trigger=dict(timing=['battle_start'],condition=[]))
def main():
 rows=[]
 values=[0.,-0.,.5,-.5,1.9,-1.9,1e308,-1e308]
 for stat in ('buff_stack_add','buff_stack_remove','debuff_stack_add','debuff_stack_remove'):
  for named in ([True] if stat.startswith('buff_') else [False,True]):
   for value in values:
    effect=base('harmful' if stat.startswith('debuff_') else 'beneficial')
    op=dict(name='operation',source='스킬1',type='instant',stat=stat,fixed_value=value,target='self',trigger=dict(timing=['on_attack'],condition=[]))
    if named:op['target_effect']='stack'
    bm=manager([effect,op])
    for _ in range(3):bm.notify('battle_start',0,NAMES[0])
    reached=[];notify=bm.notify
    def record(event,t,caster,**ctx):
     if event.startswith('stack_reach:'):reached.append(event)
     return notify(event,t,caster,**ctx)
    bm.notify=record;bm.notify('on_attack',1,NAMES[0]);ab=next(a for a in bm._active if a.effect['name']=='stack')
    delta=int(value or 1)*(-1 if stat.endswith('remove') else 1)
    expected=max(0 if stat.startswith('debuff_') and named else 1,min(3+delta,5))
    assert ab.stack==expected,(stat,named,value,ab.stack,expected)
    expiry=3 if stat.startswith('buff_') and delta>0 else 2
    assert ab.expires_at==expiry
    notices=[f'stack_reach:stack:{expected}'] if stat.startswith('buff_') and delta>0 and expected!=3 else []
    assert reached==notices,(stat,value,reached,notices)
    rows.append(dict(stat=stat,named=named,value=value,stacks=ab.stack,expiry=ab.expires_at,notices=reached))
 for stat in ('buff_stack_add','buff_stack_remove','debuff_stack_add','debuff_stack_remove','buff_max_stack_add'):
  effect=base();immune=base();immune.update(name='immune',stat='stack_change_immune',max_stack=1,duration=-1)
  op=dict(name='operation',source='스킬1',type='buff' if stat=='buff_max_stack_add' else 'instant',stat=stat,fixed_value=2,target='self',target_effect='stack',trigger=dict(timing=['on_attack'],condition=[]))
  bm=manager([effect,immune,op]);bm.notify('battle_start',0,NAMES[0]);bm.notify('on_attack',1,NAMES[0])
  ab=next(a for a in bm._active if a.effect['name']=='stack');assert ab.stack==1 and ab.expires_at==2
  rows.append(dict(stat=stat,immune=True,stacks=ab.stack,expiry=ab.expires_at))
 result=dict(passed=True,scope='CPU source contract only; new GPU effect kinds remain unadmitted',cases=rows,cpu_trace_used_as_gpu_input=False)
 (R/'research/portable-stack-native-contract.json').write_text(json.dumps(result,indent=2)+'\n');print('Native stack contract cases',len(rows),'passed')
if __name__=='__main__':main()
