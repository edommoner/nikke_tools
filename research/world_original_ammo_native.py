"""Passive real ammo handler snapshots and capacities from existing native calls."""
import sys
from contextlib import contextmanager

@contextmanager
def capture(case):
    rows=[];pending={};previous=sys.getprofile()
    def snapshot(values):
        actors=values['char_states']
        return [dict(ammo=actors[name].ammo,reload_until=actors[name].reloading_until,post_reload=actors[name]._post_reload_end_t) for name in case['names']]
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        name=frame.f_code.co_name
        if name=='_effective_max_ammo' and event=='return' and frame.f_back is not None and id(frame.f_back) in pending:
            owner=case['names'].index(frame.f_locals['cs'].name);pending[id(frame.f_back)]['capacities'][str(owner)]=answer;return
        if name not in ('handle_ammo_charge_pct','handle_ammo_charge_flat'):return
        values=frame.f_locals
        if event=='call':
            effect=values['eff'];index=effect.get('_portable_observer_row');caster=values['caster']
            if type(index) is not int or not 0<=index<len(case['effects']) or effect['name']!=case['effects'][index]['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original ammo dispatch identity mismatch')
            pending[id(frame)]=dict(row=index,owner=case['names'].index(caster),time=values['t'],stat=effect['stat'],value=values['val'],before=snapshot(values),capacities={})
        elif event=='return':
            row=pending.pop(id(frame));row.update(after=snapshot(values),targets=[case['names'].index(n) for n in values['target_names']]);rows.append(row)
    sys.setprofile(profile)
    try:yield rows
    finally:sys.setprofile(previous)
    if pending:raise ValueError('Unfinished actual ammo handler')
