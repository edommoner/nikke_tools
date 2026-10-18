import importlib.util,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('rng_fb',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator import timeline,buff_manager
n,b,e=next(x for x in v.fixtures() if x[0]=='random-caster-ranking-and-world-transitions');b['duration']=30
code=timeline.simulate.__code__;rows=[]
def trace(frame,event,arg):
 if frame.f_code.co_name not in ('get_buffs','_invalidate_buffs_cache') or frame.f_globals.get('__name__')!=buff_manager.__name__:return None
 parent=frame.f_back;names=[];at=None
 while parent is not None:
  names.append(parent.f_code.co_name)
  if parent.f_code is code:at=parent.f_locals.get('t');break
  parent=parent.f_back
 if at is None or not 20.52<at<20.54:return None
 if event in ('call','return'):
  d=frame.f_locals;bm=d['self'];rows.append(dict(event=event,function=frame.f_code.co_name,time=at,caster=d.get('caster'),full=bm.state.get('full_burst'),rng_index=random.getstate()[1][-1],stack=names[:5]))
 return trace
old=sys.gettrace()
try:
 with v.v.t.raw.injected_effects(e):sys.settrace(trace);cpu=v.a.evaluate(b)
finally:sys.settrace(old)
r=dict(rows=rows,burst_timeline=cpu['burst_timeline']);(ROOT/'research/detail-boss-buffs-fb-end-rng-cpu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in rows:print(json.dumps(r,ensure_ascii=True))
