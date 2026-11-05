"""Observe native memo reads/ref_count/mode ticks without additional queries."""
import sys
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_native

def observe(case):
    names=roster_names(case);previous=sys.getprofile();calls=[];refs=[];frames=[];fires=[];pending={};errors=[]
    codes={timeline.CharState._full_ammo.__code__:'capacity',BuffManager.ref_count.__code__:'ref',timeline.CharState._tick_weapon_change.__code__:'mode',timeline.CharState._fire.__code__:'fire',timeline.CharState._charge_fire.__code__:'fire'}
    def state(actor):return dict(memo=actor._wc_ammo_full,ammo=actor.ammo,shots=actor._wc_shots,new_session=actor._wc_new_session,restored=actor._wc_ammo_restored,reload_until=actor.reloading_until)
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        kind=codes.get(frame.f_code)
        if kind is None or event not in ('call','return'):return
        v=frame.f_locals
        try:
            if event=='call':
                if kind=='ref':
                    if v['ref']!=case['effects'][-1]['max_ammo_scaling_ref']:return
                    row=dict(owner=names.index(v['caster']),ref=v['ref']);refs.append(row)
                else:
                    row=dict(owner=names.index(v['self'].name),time=v['t'],before=state(v['self']))
                    if kind=='fire':row['mode_session']=v['self']._in_weapon_change
                    (calls if kind=='capacity' else fires if kind=='fire' else frames).append(row)
                pending[id(frame)]=row
            elif id(frame) in pending:
                row=pending.pop(id(frame))
                if kind=='ref':row['value']=answer
                else:
                    row['after']=state(v['self'])
                    if kind=='capacity':row.update(value=answer,reference_mode=bool(v.get('wc_eff',{}).get('max_ammo_scaling_ref')) if v.get('wc_eff') else False)
                    else:row['hits']=len(answer)
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:native,trace=projectile_native(case)
    finally:sys.setprofile(previous)
    if errors or pending:raise ValueError('Native mode-capacity observation failed: '+str(errors))
    native['mode_capacity']=dict(queries=calls,references=refs,frames=frames,fires=fires)
    return native,trace
