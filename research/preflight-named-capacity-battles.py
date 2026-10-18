"""Capture CPU duration-extension dispatches before differential GPU runs."""
import importlib.util,json
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('preflight',ROOT/'scripts/verify-named-capacity-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager
rows=[]
for name,body,extra in v.battles():
    dots=[];calls=[];register=BuffManager.register_damage_handler;dispatch=BuffManager._dispatch_instant
    def observe(self,eff,caster,t,*args,**kwargs):
        if eff.get('stat')=='named_buff_duration_extend':calls.append(t)
        return dispatch(self,eff,caster,t,*args,**kwargs)
    def hook(self,handler):
        def damage(eff,caster,t,*args,**kw):
            if eff.get('name')=='high dot':dots.append(t)
            return handler(eff,caster,t,*args,**kw)
        return register(self,damage)
    configured=body.pop('_named_controls',None)
    with v.t.raw.injected_effects(extra),v.ctrl.configured(configured) if configured is not None else v.nullcontext():
        compiled=v.t.a.evaluate({**body,'_compile_gpu_detail':True})
        with patch.object(BuffManager,'register_damage_handler',hook),patch.object(BuffManager,'_dispatch_instant',observe):cpu=v.t.a.evaluate(body)
    rows.append(dict(name=name,effects=len(compiled['program']['effects']),states=len(compiled['program']['states']),state_index=compiled['program']['states']['마이야르' if name.startswith('real-') else 'high '+name.split('-')[0]],total=cpu['total_damage'],dot_times=dots,extension_times=calls))
(ROOT/'research/detail-named-capacity-cpu-preflight.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows))
