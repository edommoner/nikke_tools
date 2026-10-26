"""Explicit v1 typed candidates at the canonical frame aim boundary.

Canonical named/ADD choices and manual arbitration retain priority. Only an
otherwise-BODY fallback opts into the first live typed shape. This is a declared
model, not a canonical gameplay claim or an enemy-recipient implementation.
"""
from coordinate_typed_geometry_runtime import live_rows

POLICY='typed-before-body-v1'
def normalize(policy):
    if not isinstance(policy,dict) or set(policy)!={'mode'} or policy['mode']!=POLICY:raise ValueError('Explicit typed-before-body-v1 aim policy required')
    return dict(policy)

class AimGeometry:
    """Add named aim centers without adding targets to ordinary skill geometry."""
    def __init__(self,world,base,targets):
        self._nikke_typed_world=world;self._nikke_canonical_geometry=base
        self._typed={target.name:target for target in targets}
    def __getattr__(self,name):
        base=self.__dict__.get('_nikke_canonical_geometry')
        if base is None:raise AttributeError(name)
        return getattr(base,name)
    def center(self,name):
        target=self._typed.get(name)
        return (target.shape.x,target.shape.y) if target is not None else self._nikke_canonical_geometry.center(name)
    def kind(self,name):
        target=self._typed.get(name)
        return target.kind if target is not None else self._nikke_canonical_geometry.kind(name)

class TypedCoordinateAim:
    def __init__(self,data,spec,policy):
        self.policy=normalize(policy);self.data=data;self.spec=spec;self.owner=None;self.time=None;self.base=None;self.proxy=None;self.targets=();self.candidate=''
        data['coordinate_typed_aim_frames']=[]
    def validate_effects(self,manager):
        from enemy_recipient_specs import CURRENT_TARGETS
        for effect,_ in manager._effects:
            if effect.get('target') in CURRENT_TARGETS:raise ValueError('Typed aim logical enemy recipient requires its own actor policy')
    def validate_namespace(self,boss):
        for binding in boss._nikke_typed_world.bindings:
            if binding.label=='core' or binding.label in boss.target_kinds:raise ValueError('Typed aim label cannot alias canonical core/target')
    def accepts_name(self,boss,label):
        world=getattr(boss,'_nikke_typed_world',None)
        return bool(world is not None and self.data['worlds'] and world is self.data['worlds'][-1] and any(binding.label==label for binding in world.bindings))
    def restore(self,boss,t,enemy):
        if self.owner is not None and self.owner is not boss:raise ValueError('Typed aim cannot switch its owning clock')
        if self.owner is boss and t!=self.time:
            from calculator.timeline import GEOM_KEY
            # A canonical part/core update may have replaced the proxy during
            # the preceding frame. Never restore its older canonical geometry.
            if boss.geom is self.proxy:boss.geom=self.base
            elif getattr(boss.geom,'_nikke_typed_world',None) is not None:raise ValueError('Unexpected typed geometry replacement')
            enemy[GEOM_KEY]=boss.geom
    def capture(self,boss,t,enemy):
        from calculator import timeline
        if self.owner is boss and t==self.time:
            if boss.geom is not self.proxy:
                self.base=boss.geom;self.proxy=AimGeometry(boss._nikke_typed_world,self.base,self.targets)
                boss.geom=self.proxy;enemy[timeline.GEOM_KEY]=self.proxy
            return
        world=boss._nikke_typed_world
        if world.last!=t or world.finished or boss.geom is None:raise ValueError('Typed aim requires the current coordinate frame')
        if any(binding.label=='core' for binding in world.bindings):raise ValueError('Typed aim label cannot alias canonical core')
        rows,typed,base=live_rows(world,boss.geom,self.spec)
        self.targets=tuple(g for _,g in rows if id(g) in typed)
        proxy=AimGeometry(world,base,self.targets)
        candidates=[]
        for rank,g in rows:
            if id(g) not in typed:continue
            slot,handle=typed[id(g)];candidates.append(dict(label=g.name,slot=slot,handle=[int(handle.kind),handle.identity,handle.generation],point=[g.shape.x,g.shape.y],key=list(rank)))
        self.owner=boss;self.time=t;self.base=base;self.proxy=proxy;self.candidate=candidates[0]['label'] if candidates else ''
        boss.geom=proxy;enemy[timeline.GEOM_KEY]=proxy
        self.data['coordinate_typed_aim_frames'].append(dict(time=t,candidate=self.candidate,candidates=candidates,canonical_auto=list(base.auto_aim),canonical_must_break=list(base.must_break)))
    def choose(self,boss,original):
        if self.owner is not boss:raise ValueError('Typed candidate read before its frame capture')
        return original or self.candidate
