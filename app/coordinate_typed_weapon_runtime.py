"""Declared typed geometry inside canonical sampled weapon packet production.

The canonical pellet owns sampling, critical draws, scalar arguments and packet
order. Typed impacts are deferred to that packet's real landing boundary.
"""
import sys
from contextlib import contextmanager
from functools import wraps
from types import SimpleNamespace
from unittest.mock import patch
from impact_specs import classify_hit

class CoordinateWeaponShots:
    def __init__(self,timeline,data,spec):
        self.timeline=timeline;self.data=data;self.spec=spec;self.frames=[];self.shots={};self.last_time=None;self.pending={}
        if spec is None or spec.get('point_source')!='caster_aim' or spec.get('grow',0)!=0:raise ValueError('Coordinate weapon targets require live aim and zero authored growth')
        self.code=timeline.CharState._coord_pellet.__code__
        self.data['coordinate_weapon_shots']=[];self.data['coordinate_weapon_attacks']=[]

    def snapshot(self,character,geom,t,manager,buffs,caller):
        from calculator import aim,boss_pattern
        from portable_typed_geometry_specs import normalize
        if not self.data['worlds'] or not self.data['managers'] or manager is not self.data['managers'][-1]:raise ValueError('Coordinate weapon requires its owning manager')
        world=self.data['worlds'][-1]
        if world.last!=t or world.finished or geom is None:raise ValueError('Coordinate weapon left its live coordinate frame')
        if t!=self.last_time:self.shots.clear();self.last_time=t
        key=(id(caller),id(buffs),character.name)
        if key in self.shots:return self.shots[key]
        literal=normalize(self.spec,len(world.bindings),int(world.bindings[0].handle.kind));rows=[];typed={}
        canonical={}
        for run in world.clock._runs:
            for j,target in enumerate(run.targets):canonical[target.spec.name]=(target.spec.z,run.start_t,run.p.idx,j,0)
        for target in geom.targets:
            if target.name not in canonical:raise ValueError('Canonical geometry lost its world identity')
            rows.append((canonical[target.name],target))
        for slot,(binding,shape) in enumerate(zip(world.bindings,literal['shapes'],strict=True)):
            target=world.targets.rows[slot]
            if target is None or not target.alive:continue
            if binding.label in canonical:raise ValueError('Typed and canonical target labels must be distinct')
            run=world.clock._runs[binding.node]
            if not run.active or run.opens!=target.handle.generation:raise ValueError('Typed weapon requires the owning live generation')
            sh=aim.Shape(**{k:shape[k] for k in ('x','y','r','w','h','rot')})
            g=boss_pattern.GeomTarget(binding.label,'typed_projectile' if int(target.handle.kind)==2 else 'typed_hp_shield',sh)
            rows.append(((shape['z'],run.start_t,binding.node,slot,1),g));typed[id(g)]=(slot,target.handle)
        rows.sort(key=lambda row:row[0],reverse=True)
        proxy=SimpleNamespace(targets=tuple(g for _,g in rows),core=geom.core,auto_aim=geom.auto_aim,pierce_px=geom.pierce_px,explosion_scale=geom.explosion_scale)
        record=dict(identity=len(self.data['coordinate_weapon_shots'])+1,owner=character.name,time=t,
            targets=[dict(label=g.name,kind=g.kind,key=list(rank),handle=None if id(g) not in typed else [int(typed[id(g)][1].kind),typed[id(g)][1].identity,typed[id(g)][1].generation]) for rank,g in rows])
        self.data['coordinate_weapon_shots'].append(record)
        result=dict(world=world,manager=manager,character=character,time=t,geom=proxy,typed=typed,record=record,caller=caller,buffs=buffs)
        self.shots[key]=result;return result

    @contextmanager
    def scope(self):
        original=self.timeline.CharState._coord_pellet
        @wraps(original)
        def pellet(character,geom,t,manager,enemy,buffs,ht,expected,tag_of,extra):
            if expected is not False:raise ValueError('Typed coordinate weapons require actual sampled packets')
            caller=sys._getframe(1)
            if caller.f_code.co_name not in ('_fire','_charge_fire'):raise ValueError('Unknown coordinate weapon producer')
            shot=self.snapshot(character,geom,t,manager,buffs,caller)
            frame=dict(shot=shot,pending=None);self.frames.append(frame)
            try:
                result=original(character,shot['geom'],t,manager,enemy,buffs,ht,expected,tag_of,extra)
                if frame['pending'] is not None:raise ValueError('Typed weapon scalar has no packet')
                return result
            finally:assert self.frames.pop() is frame
        try:
            with patch.object(self.timeline.CharState,'_coord_pellet',pellet):yield
        finally:
            self.shots.clear()
            if self.frames or self.pending:raise ValueError('Coordinate weapon packet/frame scope leaked')

    def scalar(self,original,*args,**kwargs):
        if not self.frames:return original(*args,**kwargs)
        frame=self.frames[-1];shot=frame['shot'];calc=sys._getframe(2);pellet=calc.f_back
        if calc.f_code.co_name!='calc' or pellet is None or pellet.f_code is not self.code:raise ValueError('Typed weapon requires the canonical pellet scalar boundary')
        values=pellet.f_locals;over=calc.f_locals['over']
        target=values.get('g') if values['grow']>0 and over.get('is_core_damage') is False else values.get('front') if values['grow']==0 else None
        selected=shot['typed'].get(id(target))
        if selected is None:return original(*args,**kwargs)
        if frame['pending'] is not None:raise ValueError('Typed weapon packet scalar was replaced')
        from destructible_damage_policy import calculate
        hit=kwargs.get('hit_type',args[3] if len(args)>3 else None);weapon=kwargs.get('weapon',args[2] if len(args)>2 else None)
        if not isinstance(hit,dict) or not isinstance(weapon,dict):raise ValueError('Actual weapon scalar arguments required')
        value=calculate(*args,**kwargs,kind=selected[1].kind)
        frame['pending']=dict(manager=shot['manager'],world=shot['world'],caster=shot['character'].name,time=shot['time'],
            kind=selected[1].kind,selected=selected,coefficient=float(hit['coeff'] if hit.get('coeff') is not None else weapon['damage_coeff']),
            name='weapon:'+shot['character'].name,weapon_mode_skill=bool(hit.get('is_weapon_mode_skill')),coordinate_weapon=True,
            shot_identity=shot['record']['identity'])
        return value

    def take(self,event):
        if not self.frames:return None
        frame=self.frames[-1];context=frame['pending']
        if context is None:return None
        if event.caster!=context['caster'] or event.t!=context['time']:raise ValueError('Coordinate weapon scalar/packet identity differs')
        frame['pending']=None;context['family']=int(classify_hit(event.hit_tag));context['hit_tag']=event.hit_tag;context['extra']=event.extra;context['critical']=event.is_crit
        self.pending[id(event)]=(event,context);return context

    def landing(self,event):
        item=self.pending.pop(id(event),None)
        if item is None:return None
        if item[0] is not event:raise ValueError('Coordinate packet identity was reused')
        return item[1]
