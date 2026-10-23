"""Observe existing duration and ref_count calls once; never add a query."""
from contextlib import contextmanager
from unittest.mock import patch
import hashlib,json
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names,*,stack_refresh=False):
    expiry=BuffManager._expires_at;reference=BuffManager.ref_count;checks=[];pending=[];managers=[]
    def observed_expiry(bm,effect,caster,t):
        managers[:]=[bm]
        if effect.get('duration_scaling')!='stack_count':return expiry(bm,effect,caster,t)
        indices=[i for i,(e,c) in enumerate(bm._effects) if e is effect and c==caster];assert len(indices)==1
        row=dict(definition=indices[0],name=effect.get('name'),stat=effect.get('stat'),owner=names.index(caster),time=t,duration=effect.get('duration'),duration_values=effect.get('duration_values'),reference=effect.get('duration_scaling_ref',''),reads=[])
        checks.append(row);pending.append(row);managers[:]=[bm]
        try:row['expires_at']=expiry(bm,effect,caster,t);return row['expires_at']
        finally:assert pending.pop() is row
    def observed_reference(bm,caster,ref):
        result=reference(bm,caster,ref)
        if pending:pending[-1]['reads'].append(dict(owner=names.index(caster),name=ref,value=result))
        return result
    operation=BuffManager._apply_buff_max_stack_add;operations=[]
    def observed_operation(bm,effect,caster,t):
        snapshot=lambda:[dict(name=a.effect.get('name'),stack=a.stack,expires_at=a.expires_at) for a in bm._active]
        row=dict(time=t,before=snapshot()) if stack_refresh else None
        result=operation(bm,effect,caster,t)
        if row is not None:row['after']=snapshot();operations.append(row)
        return result
    with patch.object(BuffManager,'_expires_at',observed_expiry),patch.object(BuffManager,'ref_count',observed_reference),patch.object(BuffManager,'_apply_buff_max_stack_add',observed_operation):yield checks,managers,operations

def observe(case):
    names=case['body']['squad'] if 'body' in case else roster_names(case)
    with capture(names,stack_refresh=case.get('observe_stack_refresh',False)) as (checks,managers,operations):
        if 'body' in case:
            import importlib.util
            from pathlib import Path
            s=importlib.util.spec_from_file_location('duration_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
            battle,shots=m.native_reference(case['body']);native=dict(battle=battle,projectile_shots=shots);trace=[]
        else:native,trace=plain(case)
    assert managers,'Native expiry handler was not reached'
    bm=managers[0];carriers=[]
    for ab in bm._active:
        if ab.effect.get('duration_scaling')!='stack_count':continue
        indices=[i for i,(e,c) in enumerate(bm._effects) if e is ab.effect and c==ab.caster];assert len(indices)==1
        carriers.append(dict(definition=indices[0],owner=names.index(ab.caster),stack=ab.stack,activated=ab.activated_at,expires_at=ab.expires_at))
    native['duration_scaling']=dict(checks=checks,carriers=carriers,definitions=len(bm._effects),trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
    if case.get('observe_stack_refresh'):native['duration_scaling']['stack_refresh']=operations
    return native,trace
