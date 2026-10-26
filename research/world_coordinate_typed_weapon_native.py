"""Actual native pellet production, followed by generation-fixed typed landings."""
from world_destructible_weapon_roster_native import capture_typed,snapshot_typed
from world_coordinate_sampled_parent_native import observe as parent_observe
from unittest.mock import patch

def observe(case,*,observer=None):
    if 'original_run' not in case:
        from portable_coordinate_typed_weapon_cases import prepare
        case,_=prepare(case)
    from calculator.buff_manager import BuffManager
    notices=[];notify=BuffManager.notify
    with capture_typed(case) as (data,samples,heals):
        def notification(manager,event,t,caster,**kwargs):
            if event=='full_charge_hit':
                notices.append(dict(owner=case['names'].index(caster),time=t,
                    landed_same_shot=sum(row['caster']==caster and row['time']==t for row in data['coordinate_weapon_attacks'])))
            return notify(manager,event,t,caster,**kwargs)
        with patch.object(BuffManager,'notify',notification):native,trace=(parent_observe if observer is None else observer)(case)
    legacy=snapshot_typed(case,data,[],heals,{},[])
    assert not data['attacks'],'Ordinary boss skills must retain their original target'
    rows=[]
    names=case['names']
    for raw in data['coordinate_weapon_attacks']:
        row={key:raw[key] for key in ('attack_id','time','damage','completed','family','hit_tag','weapon_mode_skill','coefficient','shot_identity','extra','critical')}
        row['owner']=names.index(raw['caster'])
        row['receipts']=[dict(slot=slot,handle=[int(handle.kind),handle.identity,handle.generation],**receipt) for slot,handle,receipt in raw['receipts']]
        rows.append(row)
    native['coordinate_typed_weapon']=dict(typed=legacy['typed'],attacks=rows,
        shots=data['coordinate_weapon_shots'],modifier_samples=samples,healing=heals,full_charge_boundaries=notices,
        scope='Declared sampled typed geometry; no automatic typed aim or gameplay certification')
    return native,trace
