"""Observe actual condition entry/exit and nested notify context; no new query."""
from contextlib import contextmanager
from unittest.mock import patch
import hashlib,inspect,json
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain


@contextmanager
def capture(names):
    checks=[];notifications=[];managers=[];instants=[];condition=BuffManager._condition_ok;notify=BuffManager.notify;instant=BuffManager._dispatch_instant;instant_signature=inspect.signature(instant)
    def observed_notify(bm,event,t,caster,**ctx):
        notifications.append((event,t,caster))
        try:return notify(bm,event,t,caster,**ctx)
        finally:notifications.pop()
    def identity(bm,eff,caster):
        indices=[i for i,(e,owner) in enumerate(bm._effects) if e is eff and owner==caster]
        assert len(indices)==1,'Ambiguous native effect identity'
        return indices[0]
    def accum(bm,eff,caster):
        data=bm.state.get('rng_acc',{})
        return {tag:dict(created=(tag,id(eff),caster) in data,value=data.get((tag,id(eff),caster),0.)) for tag in ('not_core','prob')}
    def observed_condition(bm,conditions,caster,t,eff=None):
        if 'not_core' not in conditions:return condition(bm,conditions,caster,t,eff)
        assert eff is not None;managers[:]=[bm]
        row=dict(definition=identity(bm,eff,caster),name=eff.get('name'),owner=names.index(caster),time=t,event=notifications[-1][0] if notifications else None,notify_depth=len(notifications),core_fraction=bm._notify_ctx.get('core_frac'),conditions=list(conditions),before=accum(bm,eff,caster));checks.append(row)
        try:row['result']=bool(condition(bm,conditions,caster,t,eff));return row['result']
        finally:row['after']=accum(bm,eff,caster)
    def observed_instant(bm,*args,**kwargs):
        values=instant_signature.bind(bm,*args,**kwargs).arguments;effect=values.get('eff',values.get('effect'))
        if effect is not None and 'not_core' in effect.get('trigger',{}).get('condition',[]):
            instants.append(dict(definition=identity(bm,effect,values['caster']),owner=names.index(values['caster']),name=effect.get('name'),stat=effect.get('stat'),time=values['t']))
        return instant(bm,*args,**kwargs)
    with patch.object(BuffManager,'notify',observed_notify),patch.object(BuffManager,'_condition_ok',observed_condition),patch.object(BuffManager,'_dispatch_instant',observed_instant):yield checks,managers,instants


def observe(case):
    names=case['body']['squad'] if 'body' in case else roster_names(case)
    with capture(names) as (checks,managers,instants):
        if 'body' in case:
            import importlib.util
            from pathlib import Path
            s=importlib.util.spec_from_file_location('not_core_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
            battle,shots=real.native_reference(case['body']);native=dict(battle=battle,projectile_shots=shots);trace=[]
        else:native,trace=plain(case)
    assert checks and managers
    bm=managers[0];states=[]
    for key,value in bm.state.get('rng_acc',{}).items():
        if len(key)!=3 or key[0]!='not_core':continue
        tag,identity,caster=key
        indices=[i for i,(e,owner) in enumerate(bm._effects) if id(e)==identity and owner==caster];assert len(indices)==1
        states.append(dict(definition=indices[0],owner=names.index(caster),value=value))
    carriers=[]
    for active in bm._active:
        if 'not_core' not in active.effect.get('trigger',{}).get('condition',[]):continue
        indices=[i for i,(e,owner) in enumerate(bm._effects) if e is active.effect and owner==active.caster];assert len(indices)==1
        carriers.append(dict(definition=indices[0],owner=names.index(active.caster),stack=active.stack))
    native['not_core_condition']=dict(checks=checks,states=sorted(states,key=lambda r:(r['definition'],r['owner'])),carriers=carriers,instant_calls=instants,definitions=len(bm._effects),expected_mode=bool(bm.state.get('rng_expected')),trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
    return native,trace
