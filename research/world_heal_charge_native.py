"""Observe existing pool lifecycle returns and fields without extra semantic queries."""
import sys
import engine_worker,heal_charge_compat as charge
from world_frame_native import roster_names
from world_projectile_native import observe as plain

def observe(case):
    names=roster_names(case);previous=sys.getprofile();events=[];pending={}
    codes={getattr(charge,k).__code__:k for k in ('snapshot','capacity','collect','take','latch_end','discharge','discard_removed')}
    def pools(manager):
        active={a.uid for a in manager._active}
        return [dict(row=a.effect['_portable_observer_row'],owner=names.index(a.caster),base=a.heal_charge_base_cap,current=a.heal_charge_current,done=a.heal_charge_done,ended=a.heal_charge_ended,active=a.uid in active) for a in getattr(manager,'_heal_charge_records',{}).values()]
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        kind=codes.get(frame.f_code)
        if kind is None or event not in ('call','return'):return
        v=frame.f_locals;manager=v['self']
        if kind=='snapshot' and (v['eff'].get('type')!='buff' or v['eff'].get('stat')!=charge.STAT):return
        if event=='call':
            row=dict(kind=kind,time=v.get('t'),before=pools(manager))
            if kind in ('collect','take','latch_end'):row.update(name=v.get('name'),owner=names.index(v['caster']) if 'caster' in v else names.index(v['name']),amount=v.get('amount'))
            if kind=='discharge':row['owner']=names.index(v['caster'])
            events.append(row);pending[id(frame)]=row
        else:
            row=pending.pop(id(frame));row.update(after=pools(manager))
            if kind in ('take','capacity'):row['value']=value
            if kind=='capacity':row['row']=v['ab'].effect['_portable_observer_row']
            if kind=='discharge':row.update(returned_sequence=len(events),targets=[names.index(n) for n in v['targets']],taken=v['amount'])
    sys.setprofile(profile)
    try:n,t=plain(case)
    finally:sys.setprofile(previous)
    if pending:raise ValueError('Incomplete healing-charge observation')
    n['healing_charge']=dict(events=events);return n,t
