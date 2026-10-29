"""Passive original source receipts; never resolve targets or apply effects."""
from contextlib import contextmanager
from unittest.mock import patch
from world_original_source_native import identity

def threshold(case):return case['catalogue_profile'].get('scene_witness',{}).get('family')=='Original-threshold'

def captures(case):return case['catalogue_profile'].get('scene_witness',{}).get('family') in ('Original-support','Original-threshold')

def selected(case):
    if threshold(case):
        return [i for i,(e,o) in enumerate(zip(case['effects'],case['owners'])) if o==0 and
                e.get('max_trigger')==2 and e.get('stat') in ('invincible','heal_hp_pct')]
    return [i for i,(e,o) in enumerate(zip(case['effects'],case['owners']))
            if case['names'][o] in ('나가','티아') and e.get('type')=='buff' and
            (e.get('stat') in ('shield_from_max_hp_pct','lifesteal_pct','burst_cooldown') or
             'during_shield' in e.get('trigger',{}).get('condition',[]) or
             'event:shield_applied' in e.get('trigger',{}).get('timing',[]))]

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    activate=BuffManager._activate;dispatch=BuffManager._dispatch_instant
    wanted=set(selected(case));result=dict(activations=[],heals=[])
    limited=threshold(case)
    if limited:result['attempts']=[]
    def snapshot(manager):
        return {key:[manager.state[key][name] for name in case['names']] for key in (('hp','cover_hp','hp_pct') if limited else ('hp','cover_hp'))}
    def activated(manager,effect,caster,t,*args,**kwargs):
        row=effect.get('_portable_observer_row')
        if limited and row in wanted:
            row=identity(case,effect,caster);before=manager._trigger_counts.get(id(effect),0);hp_pct=snapshot(manager)['hp_pct']
            answer=activate(manager,effect,caster,t,*args,**kwargs)
            after=manager._trigger_counts.get(id(effect),0)
            result['attempts'].append(dict(row=row,owner=case['names'].index(caster),time=t,before=before,after=after,hp_pct=hp_pct))
            if after>before:result['activations'].append(dict(row=row,owner=case['names'].index(caster),time=t))
            return answer
        answer=activate(manager,effect,caster,t,*args,**kwargs)
        row=effect.get('_portable_observer_row')
        if row in wanted:
            row=identity(case,effect,caster)
            if any(ab.effect.get('_portable_observer_row')==row and ab.caster==caster for ab in manager._active):
                result['activations'].append(dict(row=row,owner=case['names'].index(caster),time=t))
        return answer
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        if caster not in (('비스킷',) if limited else ('나가','티아')) or effect.get('stat') not in ('heal_hp_pct','cover_heal_pct'):
            return dispatch(manager,effect,caster,t,*args,**kwargs)
        row=identity(case,effect,caster);before=snapshot(manager)
        answer=dispatch(manager,effect,caster,t,*args,**kwargs)
        result['heals'].append(dict(row=row,owner=case['names'].index(caster),time=t,stat=effect['stat'],name=effect['name'],before=before,after=snapshot(manager)))
        return answer
    with patch.object(BuffManager,'_activate',activated),patch.object(BuffManager,'_dispatch_instant',dispatched):yield result
