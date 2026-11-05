"""Observe actual packet creation and notify/handler order; add no queries."""
import sys
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    old=sys.getprofile();events=[];pending={};active=[];instant={};last=[None];data=dict(events=events)
    notify=BuffManager.notify;hit=timeline.HitEvent
    def carriers(manager):
        if manager is None:return []
        return [dict(name=a.effect.get('name',''),owner=names.index(a.caster),stat=a.effect.get('stat'),stack=a.stack,recipients=None if a.target_chars is None else list(a.target_chars),expires=a.expires_at) for a in manager._active if a.effect.get('name') in ('carrier','heard','near-miss') or a.effect.get('stat')=='buff_stack_add']
    def profile(frame,event,value):
        if old is not None:old(frame,event,value)
        if frame.f_code.co_name=='_dispatch_instant' and frame.f_code.co_filename.endswith('/calculator/buff_manager.py') and event in ('call','return'):
            v=frame.f_locals;eff=v.get('eff',{})
            if eff.get('stat')=='buff_stack_add':
                manager=v['self'];last[0]=manager
                if event=='call':
                    row=dict(kind='instant-stack-op',name=eff.get('name',''),owner=names.index(v['caster']),time=v['t'],sequence=len(events),before=carriers(manager));events.append(row);instant[id(frame)]=row
                else:instant.pop(id(frame)).update(after=carriers(manager),returned_sequence=len(events))
        if frame.f_code.co_name!='_handle_damage_eff' or not frame.f_code.co_filename.endswith('/calculator/timeline.py') or event not in ('call','return'):return
        v=frame.f_locals
        if event=='call':
            effect=v['eff'];last[0]=v.get('bm');row=dict(kind='handler',name=effect.get('name',''),stat=effect.get('stat'),declared_weapon=effect.get('weapon_type'),owner=names.index(v['caster']),time=v['t'],sequence=len(events));events.append(row);pending[id(frame)]=row;active.append(row)
        else:
            row=pending.pop(id(frame));assert active.pop() is row;cs=v.get('cs');row.update(returned_sequence=len(events),hit_count=v.get('hit_count'),is_normal=v.get('is_normal'),current_weapon=cs.weapon.get('weapon_type') if cs else None,base_weapon=getattr(cs,'base_weapon_type',None))
    def notified(manager,event,t,caster,*args,**kwargs):
        last[0]=manager
        if event.startswith(('weapon_hit:','hit_count:')):
            prefix='weapon_hit:' if event.startswith('weapon_hit:') else 'hit_count:'
            row=dict(kind='weapon-hit' if prefix=='weapon_hit:' else 'named-hit',name=event.removeprefix(prefix),owner=names.index(caster),time=t,sequence=len(events),handler=active[-1]['sequence'] if active else None,before=carriers(manager));events.append(row)
            result=notify(manager,event,t,caster,*args,**kwargs);row.update(after=carriers(manager),returned_sequence=len(events));return result
        return notify(manager,event,t,caster,*args,**kwargs)
    def packet(*args,**kwargs):
        p=hit(*args,**kwargs);events.append(dict(kind='packet',name=p.skill_name,tag=p.hit_tag,owner=names.index(p.caster),time=p.t,amount=p.damage,split=p.split,critical=p.is_crit,sequence=len(events),handler=active[-1]['sequence'] if active else None));return p
    with patch.object(BuffManager,'notify',notified),patch.object(timeline,'HitEvent',packet):
        sys.setprofile(profile)
        try:yield data
        finally:sys.setprofile(old)
    if pending or active or instant:raise ValueError('Incomplete projectile handler observation')
    data['final_carriers']=carriers(last[0])
    data['definitions']=[dict(owner=names.index(owner),name=e.get('name'),stat=e.get('stat'),kind=e.get('type')) for e,owner in last[0]._effects] if last[0] is not None else []
def plain_original(case):
    import importlib.util
    from pathlib import Path
    s=importlib.util.spec_from_file_location('projectile_chain_original_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    n,shots=m.native_reference(case['body']);return dict(battle=n,projectile_shots=shots),[]
def observe(case):
    original='body' in case;names=case['body']['squad'] if original else roster_names(case)
    with capture(names) as data:n,t=(plain_original if original else plain)(case)
    n['projectile_chain']=data;return n,t
