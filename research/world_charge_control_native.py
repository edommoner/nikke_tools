"""Observe native state and notifications without producing a GPU schedule."""
import math
from unittest.mock import patch
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_team_native import observe as team_native

def observe(case):
 names=roster_names(case);notes=[];frames=[];managers=[];characters={};notify=BuffManager.notify;arbitrate=timeline._arbitrate_control
 def notified(bm,event,t,caster,*a,**kw):
  if event.startswith('charge_hold:'):notes.append(dict(owner=names.index(caster),event=event,time=t,full_time=characters[caster]._charge_full_t))
  return notify(bm,event,t,caster,*a,**kw)
 def arbitrated(t,bm,squad,states,static):
  answer=arbitrate(t,bm,squad,states,static);managers[:]=[bm];characters.update(states)
  row=dict(time=t,owner=names.index(bm.state['ctrl_owner']) if bm.state['ctrl_owner'] else -1,camera_mask=sum(1<<names.index(n) for n in bm.state['camera']),preemptions=[bm.state['ctrl_preempt'].get(n,0) for n in names])
  if not frames or any(row[k]!=frames[-1][k] for k in ('owner','camera_mask','preemptions')):frames.append(row)
  return answer
 with patch.object(BuffManager,'notify',notified),patch.object(timeline,'_arbitrate_control',arbitrated):native,trace=team_native(case)
 state=managers[0].state
 native['manual_control']=dict(owner=names.index(state['ctrl_owner']) if state['ctrl_owner'] else -1,camera_mask=sum(1<<names.index(n) for n in state['camera']),owner_since=state['ctrl_owner_since'],preemptions=[state['ctrl_preempt'].get(n,0) for n in names],burst_users=[sum(1<<names.index(n) for n in state.get('burst_cycle_users',{}).get(str(stage),set())) for stage in (1,2,3)],notifications=notes,arbitration=frames,characters=[dict(owner=i,phase=characters[n]._charge_phase,full_time=characters[n]._charge_full_t,release_time=None if math.isinf(characters[n]._hold_release_t) else characters[n]._hold_release_t,release_until_close=math.isinf(characters[n]._hold_release_t),sequence_index=characters[n]._ctrl_seq_i,fired=sorted(characters[n]._charge_hold_fired),reentry_anchors=sorted(v for kind,v in characters[n]._reentry_used if kind=='hold')) for i,n in enumerate(names)])
 return native,trace
