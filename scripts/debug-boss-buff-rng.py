"""Locate the first differing MT index at identical CPU/GPU frame boundaries.

The GPU inputs are authored definitions, ticks and read-only RNG queries only.
CPU values are computed independently afterwards and are never GPU inputs.
"""
import argparse,ast,hashlib,importlib.util,inspect,json,random,sys,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('buff_rng',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator import timeline
ap=argparse.ArgumentParser();ap.add_argument('--duration',type=float,default=180);ap.add_argument('--full-end-damage',action='store_true');args=ap.parse_args()
n,b,e=next(x for x in v.fixtures() if x[0]=='random-caster-ranking-and-world-transitions');b['duration']=args.duration
if args.full_end_damage:e[v.v.NAMES[0]].append(v.E('full end damage','damage','damage',100,'target',event='full_burst_end'))
script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[0,0,5,i,0,-1,0,0] for i in range(5)];at=0.;times=[]
while at<=args.duration:
 script.extend([[at,4,0,0,0,-1,0,0],[at,2,110,0,13,len(times),0,0]]);times.append(at);at+=1/60
script.append([args.duration,5,0,0,0,-1,0,0]);d=v.v.Cuda()
try:
 with v.v.t.raw.injected_effects(e):
  c=v.a.evaluate({**b,'_compile_gpu_detail':True});gpu=v.g.run(d,[c['program']],script,[c['enemy']],[c['base_stats']],module_backend='native',seeds=[12345])
finally:d.close()
indices=[int(r[0]) for r in gpu['queries'][0]];cpu_indices=[]
lines,first=inspect.getsourcelines(timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
nodes=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(nodes)==1
line=first+nodes[0].lineno-1;code=timeline.simulate.__code__
def trace(frame,event,arg):
 if frame.f_code is not code:return None
 if event=='line' and frame.f_lineno==line:cpu_indices.append(random.getstate()[1][-1])
 return trace
old=sys.gettrace()
try:
 with v.v.t.raw.injected_effects(e):sys.settrace(trace);cpu=v.a.evaluate(b)
finally:sys.settrace(old)
assert len(cpu_indices)==len(indices)==len(times)
diff=next((i for i,(x,y) in enumerate(zip(cpu_indices,indices)) if x!=y),None)
rows=[dict(frame=i,time=times[i],cpu_index=cpu_indices[i],gpu_index=indices[i]) for i in range(max(0,(diff or 0)-5),min(len(times),(diff or 0)+12))]
r=dict(duration=args.duration,frames=len(times),first_difference=diff,first_time=None if diff is None else times[diff],cpu_total=cpu['total_damage'],gpu_total=round(sum(gpu['totals'][0])),nearby=rows,cpu_indices=cpu_indices,gpu_indices=indices,cpu_trace_used_as_gpu_input=False)
suffix='-full-end-damage' if args.full_end_damage else ''
(ROOT/f'research/detail-boss-buffs-rng-{args.duration:g}{suffix}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:r[k] for k in ('duration','frames','first_difference','first_time','cpu_total','gpu_total','nearby')}),flush=True)
