"""Add storage-only GPU readback and make authored fixture definitions importable."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/probe-healing-storage-squads.py';s=p.read_text(encoding='utf-8');needle='\nfor name,b,x in fixtures():\n';assert s.count(needle)==1
head,tail=s.split(needle);s=head+'\ndef main():\n'+''.join('    '+line+'\n' for line in ('for name,b,x in fixtures():\n'+tail).splitlines())+"\nif __name__=='__main__':main()\n";p.write_text(s,encoding='utf-8')
p=ROOT/'research/staging/v40/app/detail_gpu.py';s=p.read_text(encoding='utf-8');assert '_debug_storage_frames' not in s
needle=' decoy_offset=scalar_offset+(len(frame_times) if scalar is not None else 0);decoy_times=[]'
assert needle in s;s=s.replace(needle,needle+"\n if '_debug_storage_frames' in body and type(body['_debug_storage_frames']) is not bool:raise ValueError('Invalid storage frame witness')\n storage_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==74}) if body.get('_debug_storage_frames') else []\n storage_offset=decoy_offset+(len(frame_times)*(1+len(decoy_keys)) if body.get('_debug_decoy_frames') else 0);storage_times=[]")
needle='   for key in [-1]+decoy_keys:script.append([t,2,121,0,key,decoy_offset+len(decoy_times),0,0]);decoy_times.append((t,key))'
assert needle in s;s=s.replace(needle,needle+"\n  if body.get('_debug_storage_frames'):\n   for key in [-1]+storage_keys:script.append([t,2,122,0,key,storage_offset+len(storage_times),0,0]);storage_times.append((t,key))")
needle=" if decoy_times:payload['_decoy_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(decoy_times,logs[decoy_offset:decoy_offset+len(decoy_times)])]"
assert needle in s;s=s.replace(needle,needle+"\n if storage_times:payload['_storage_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(storage_times,logs[storage_offset:storage_offset+len(storage_times)])]")
p.write_text(s,encoding='utf-8');print('Storage frame readback added; fixture import performs no CPU simulation.')
