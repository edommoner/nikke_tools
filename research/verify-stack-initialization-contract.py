"""Native-only initialization, zero-refresh and shared-recipient edge contracts."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES

def seed(**extra):return dict(name='seed',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=2,max_stack=5,polarity='beneficial',trigger=dict(timing=['event:full_reload'],condition=[]),**extra)
def op(stat,value,target='self'):return dict(name='operation',source='스킬1',type='buff' if stat=='buff_max_stack_add' else 'instant',stat=stat,fixed_value=value,target=target,target_effect='seed',trigger=dict(timing=['on_attack'],condition=[]))
def main():
 rows=[]
 for value,want in [(0.,1),(-0.,1),(.5,0),(-.5,0),(-1.,0),(3.9,3),(9.,5)]:
  bm=manager([seed(),op('buff_stack_init',value)]);seen=[];notify=bm.notify
  def record(event,t,caster,**ctx):
   seen.append(event);return notify(event,t,caster,**ctx)
  bm.notify=record;bm.notify('on_attack',1,NAMES[0]);active=[a for a in bm._active if a.effect['name']=='seed']
  assert len(active)==bool(want) and (not active or active[0].stack==want)
  assert seen==['on_attack'];rows.append(dict(name='init-'+repr(value),stack=want,notifications=seen))
 e=seed(duration_bullets=3);e['trigger']['condition']=['during_full_burst'];e['max_trigger']=0
 bm=manager([e,op('buff_stack_init',3)]);bm.notify('on_attack',1,NAMES[0]);a=bm._active[0]
 assert a.stack==3 and a.bullets_left==-1 and a.bullets_per_target=={} and a.per_char_stacks=={} and a.expires_at==3
 assert bm._trigger_counts.get(id(a.effect),0)==0
 rows.append(dict(name='init-bypasses-target-gates-and-bullet-initialization',stack=a.stack,bullets_left=a.bullets_left,expiry=a.expires_at))
 e=seed();e['max_stack']=1;e['trigger']['timing']=['battle_start']
 bm=manager([e,op('debuff_stack_remove',1)]);bm.notify('battle_start',0,NAMES[0]);bm.notify('on_attack',.5,NAMES[0]);a=bm._active[0];assert a.stack==0
 bm.notify('battle_start',1,NAMES[0]);assert a.stack==0 and a.expires_at==3
 rows.append(dict(name='single-stack-zero-survives-normal-refresh',stack=a.stack,expiry=a.expires_at))
 for target,want,skip in [('self',1,1),('all_allies',3,0)]:
  e=seed();e['target']='all_allies';e['trigger']['timing']=['battle_start']
  bm=manager([e,op('buff_max_stack_add',2,target)]);bm.notify('battle_start',0,NAMES[0]);bm.notify('on_attack',1,NAMES[0]);a=bm._active[0]
  assert a.stack==want and bm.partial_skips==skip and a.expires_at==(2 if skip else 3)
  rows.append(dict(name='shared-max-add-'+target,stack=a.stack,partial_skips=bm.partial_skips,expiry=a.expires_at))
 result=dict(passed=True,scope='Native CPU contract only; corresponding GPU effect kinds remain unadmitted',cases=rows,cpu_trace_used_as_gpu_input=False)
 (R/'research/portable-stack-initialization-contract.json').write_text(json.dumps(result,indent=2)+'\n');print('Native initialization/refresh/shared edges:',len(rows),'passed')
if __name__=='__main__':main()
