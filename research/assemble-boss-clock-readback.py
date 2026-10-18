"""Attach GPU-produced boss timeline and optional frame witnesses to results."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'app/detail_gpu.py';t=p.read_text(encoding='utf-8')
changes=[
 ("prepared=compiled['prepared'];body=compiled['body'];duration=float(body.get('duration',180));script=[]", "prepared=compiled['prepared'];body=compiled['body'];duration=float(body.get('duration',180));script=[]\n patterns=compiled.get('patterns',[]);parts=compiled.get('parts',[])\n witness_base=267+(14 if body.get('_debug_random_state') else 0)+len(parts)+(BLOG if patterns else 0)\n witness_times=[]"),
 ("script.append([t,4,0,0,0,-1,0,0]);t+=1/60", "script.append([t,4,0,0,0,-1,0,0])\n  if patterns and body.get('_debug_boss_frames'):\n   script.append([t,2,116,0,0,witness_base+len(witness_times),0,0]);witness_times.append(t)\n  t+=1/60"),
 ("for i in range(len(parts)):script.append([duration,2,114,0,i,part_offset+i,0,0])", "for i in range(len(parts)):script.append([duration,2,114,0,i,part_offset+i,0,0])\n boss_offset=part_offset+len(parts)\n if patterns:\n  for i in range(BLOG):script.append([duration,2,115,0,i,boss_offset+i,0,0])"),
 ("payload['seed']=body.get('seed',0)", "if patterns:\n  payload['boss_patterns']=copy.deepcopy(body.get('enemy',{}).get('patterns',[]))\n  outcomes={1:'expired',2:'followed',3:'cleared',4:'end'}\n  payload['boss_timeline']=[dict(time=round(r[0],6),pattern=patterns[int(r[1])]['id'],kind=patterns[int(r[1])]['kind'],event='start' if r[2]==0 else 'end',outcome=outcomes.get(int(r[2]))) for r in logs[boss_offset:boss_offset+int(logs[boss_offset][3])]]\n  if witness_times:payload['_boss_frames']=[dict(time=at,core=r[0],distance=r[1],weapon_mask=int(r[2]),log_count=int(r[3]),active_mask=int(r[4]),opens=[int(v) for v in r[5:5+len(patterns)]]) for at,r in zip(witness_times,logs[witness_base:])]\n payload['seed']=body.get('seed',0)")
]
for a,b in changes:
    assert a in t,a;t=t.replace(a,b)
# The readback copies definitions only; it does not interpret gameplay on the CPU.
t=t.replace('from types import SimpleNamespace\n import engine_worker as adapter','from types import SimpleNamespace\n import copy\n import engine_worker as adapter')
p.write_text(t,encoding='utf-8');print('Boss timeline readback assembled')
