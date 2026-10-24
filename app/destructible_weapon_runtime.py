"""Scope actual native fire methods; use each pellet's original scalar inputs.

No clock, weapon simulator, damage formula or effect list is reproduced here.
Only body-aimed plain geometry is declared. A pellet may choose another shield
after a synchronous child, but its buffs remain the native shot's snapshot.
"""
from contextlib import ExitStack,contextmanager
from functools import wraps
from unittest.mock import patch
from impact_specs import ActorKind,classify_hit
from destructible_shield_policy import select

class WeaponShots:
    def __init__(self,timeline,data,owner,hit_shields):
        self.timeline=timeline;self.data=data;self.owner=owner;self.hit_shields=hit_shields;self.frames=[]

    def geometry(self,character,manager,enemy):
        if enemy.get(self.timeline.GEOM_KEY) is not None or enemy.get(self.timeline.PART_REACH_KEY,0) or enemy.get(self.timeline.INTERRUPT_REACH_KEY,0) or character._stage_aim(manager) is not None:
            raise ValueError('Weapon shield geometry/part/interrupt policy is not declared')

    def validate_effects(self,manager):
        from damage_accum_runtime import STATS
        if any(e.get('stat')=='lifesteal_pct' or e.get('stat') in STATS for e,_ in manager._effects):
            raise ValueError('Weapon shield post-landing lifesteal/accumulation policy is not declared')

    def wrap(self,method):
        @wraps(method)
        def fire(character,t,manager,enemy,config,*args,**kwargs):
            if not self.data['worlds']:raise ValueError('Weapon shield capture requires the owning battle frame and manager')
            world=self.data['worlds'][-1]
            if not self.data['managers'] or manager is not self.data['managers'][-1] or world.last!=t or world.finished:
                raise ValueError('Weapon shield capture requires the owning battle frame and manager')
            self.geometry(character,manager,enemy)
            frame=dict(character=character,manager=manager,world=world,enemy=enemy,caster=character.name,time=t,pending=None)
            self.frames.append(frame)
            try:
                result=method(character,t,manager,enemy,config,*args,**kwargs)
                if frame['pending'] is not None:raise ValueError('Weapon scalar has no corresponding packet')
                return result
            finally:assert self.frames.pop() is frame
        return fire

    @contextmanager
    def scope(self):
        with ExitStack() as stack:
            cls=self.timeline.CharState
            for name in ('_fire','_charge_fire'):stack.enter_context(patch.object(cls,name,self.wrap(getattr(cls,name))))
            try:yield
            finally:
                if self.frames:raise ValueError('Weapon fire scope leaked')

    def scalar(self,original,*args,**kwargs):
        if not self.frames:return original(*args,**kwargs)
        frame=self.frames[-1]
        if frame['pending'] is not None:raise ValueError('Weapon scalar projection requires its own declared policy')
        self.geometry(frame['character'],frame['manager'],frame['enemy'])
        if frame['world'].last!=frame['time'] or frame['world'].finished:raise ValueError('Weapon scalar left its owning battle frame')
        hit=kwargs.get('hit_type',args[3] if len(args)>3 else None)
        if not isinstance(hit,dict) or hit.get('is_part') or hit.get('is_intercept') or hit.get('is_pierce_damage'):
            raise ValueError('Weapon shield scalar requires a plain nonpiercing body packet')
        selected=select(frame['world'],self.owner,hit_shields=self.hit_shields)
        if selected is None:return original(*args,**kwargs)
        weapon=kwargs.get('weapon',args[2] if len(args)>2 else None)
        if not isinstance(weapon,dict):raise ValueError('Actual sampled weapon required')
        coefficient=hit.get('coeff')
        if coefficient is None:coefficient=weapon['damage_coeff']
        kind=selected[1].kind
        from destructible_damage_policy import calculate
        result=calculate(*args,**kwargs,kind=ActorKind.BODY if kind==ActorKind.HIT_SHIELD else kind)
        frame['pending']=dict(manager=frame['manager'],world=frame['world'],caster=frame['caster'],time=frame['time'],kind=kind,selected=selected,coefficient=float(coefficient),name='weapon:'+frame['character'].name,weapon_mode_skill=bool(hit.get('is_weapon_mode_skill')))
        return result

    def take(self,event):
        if not self.frames:return None
        frame=self.frames[-1];context=frame['pending']
        if context is None:return None
        if event.caster!=context['caster'] or event.t!=context['time']:raise ValueError('Weapon scalar/packet caster or time mismatch')
        frame['pending']=None
        context['family']=int(classify_hit(event.hit_tag));context['hit_tag']=event.hit_tag
        return context
