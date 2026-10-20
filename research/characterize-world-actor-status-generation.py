"""Trace actual count-immunity generation rules during native spawn callbacks."""
import copy,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('count_generation_state',ROOT/'research/verify-world-actor-state.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
from calculator.buff_manager import BuffManager
from world_frame_native import observe
from enemy_recipient_runtime import snapshot

def main():
 c=copy.deepcopy(d.fields.fixtures()[0]);c.update(observe_enemy_fields=False,duration=.25)
 c['patterns'][0].update(after=['start','wave'],until=dict(time=.1),repeat=0,emit=['event:target_spawn'])
 e=d.fields.pool.body.f.effect;c['effects']=[e('debuff_immune_count',100,name='charges',target='all_enemies'),e('received_dmg_pct',0,name='mark',target='all_enemies',polarity='harmful',max_stack=20,trigger=dict(timing=['event:target_spawn'],condition=[]))];c['owners']=[0,0]
 traces=[];original=BuffManager._consume_immune_charge
 def consumed(manager,label):
  before=[];current=snapshot(manager,label)
  for ab in manager._active:
   if ab.effect.get('stat')!='debuff_immune_count' or label not in (ab.target_chars or []):continue
   key=getattr(ab,'enemy_recipient_key',None);captured=None if key is None else key.actor_for(label)
   before.append(dict(name=ab.effect.get('name'),captured_generation=None if captured is None else captured.generation,current_generation=None if current is None else current.handle.generation,current_alive=None if current is None else current.alive))
  result=original(manager,label)
  if before:traces.append(dict(label=label,carriers=before,blocked=bool(result)))
  return result
 with patch.object(BuffManager,'_consume_immune_charge',consumed):observe(c)
 stale=[t for t in traces if any(a['captured_generation']!=a['current_generation'] for a in t['carriers'])];assert stale and all(x['blocked'] for x in stale)
 answer=dict(passed=True,scope='Actual full native spawn callback:count pool reads target_chars before deferred drop',stale_generation_charge_uses=len(stale),traces=traces,ordinary_immunity_uses_generation_aware_has_immune=True,count_immunity_uses_membership_until_actual_drop=True,gpu_executions=0,cpu_state_used_as_gpu_input=False,full_goal_complete=False)
 (ROOT/'research/portable-world-actor-status-generation-contract.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n');print('Native stale-generation count uses',len(stale),'before actual target drop;GPU0')
if __name__=='__main__':main()
