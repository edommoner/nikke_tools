"""Opt-in sampled ADD geometry using existing actors, pellet math and landing.

This declares collider positions, not game distance or auto-aim rules. No ADD
health, spawn clock, damage formula or attack-group collector is duplicated.
"""
import ast
from contextlib import contextmanager
from functools import wraps
from types import SimpleNamespace
from unittest.mock import patch
from impact_specs import ActorKind
from portable_geometry_specs import number
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for
from world_actor_specs import bindings

PREFIX='__portable_logical_geometry_'

def live_for_handle(registry,rows,handle):
    if handle.kind!=ActorKind.ADD:return []
    return [a for a in rows if registry.view(ActorKind.ADD,a.id).handle==handle]

def normalize(spec):
    if type(spec) is not list or not 1<=len(spec)<=127:raise ValueError('Declare one to127 logical ADD colliders')
    result=[];labels=set()
    for row in spec:
        if type(row) is not dict or set(row)!={'label','shape'} or type(row['label']) is not str or not row['label'] or row['label'].startswith(PREFIX) or row['label'] in labels:raise ValueError('Distinct explicit logical actor labels required')
        labels.add(row['label']);shape=row['shape']
        if type(shape) is not dict or set(shape)-{'x','y','r','w','h','rot','z'} or not {'x','y'}<=set(shape):raise ValueError('Literal logical circle or rectangle required')
        shape={k:float(number(shape.get(k,0))) for k in ('x','y','r','w','h','rot','z')}
        if not (shape['r']>0 and shape['w']==shape['h']==0 or shape['r']==0 and shape['w']>0 and shape['h']>0):raise ValueError('Invalid logical collider dimensions')
        result.append(dict(label=row['label'],shape=shape))
    return result

class LogicalLand(ast.NodeTransformer):
    def __init__(self):self.counts=dict(land=0)
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_land':
            scope=ast.parse('with _nikke_logical_geometry_land(bm,boss,ev,t):\n pass').body[0]
            scope.body=node.body;node.body=[ast.copy_location(scope,node.body[0])];self.counts['land']+=1
        return node

class LogicalPelletChannels(ast.NodeTransformer):
    def __init__(self):self.counts=dict(returns=0)
    def visit_FunctionDef(self,node):
        # The nested scalar/hit helpers retain their exact original returns.
        if node.name=='_coord_pellet':self.generic_visit(node)
        return node
    def visit_Return(self,node):
        self.counts['returns']+=1
        template=ast.parse('_nikke_logical_pellet_channels(locals().get("front"), None)',mode='eval').body
        template.args[1]=node.value;node.value=ast.copy_location(template,node.value);return node

class LogicalShot(ast.NodeTransformer):
    def __init__(self,name):self.name=name;self.counts=dict(shot=0)
    def visit_FunctionDef(self,node):
        if node.name==self.name:
            scope=ast.parse('with _nikke_logical_geometry_shot(self,t,bm):\n pass').body[0]
            scope.body=node.body;node.body=[ast.copy_location(scope,node.body[0])];self.counts['shot']+=1
        return node

class LogicalGeometry:
    def __init__(self,spec):
        self.spec=normalize(spec);self.boss=None;self.bindings={};self.frame_time=None;self.frames=[];self.pending={};self.routing=[];self.suspended=0
        self.data=dict(shots=[],packets=[],pellets=[],bosses=[],managers=[])

    def channels(self,front,answer):
        if getattr(front,'kind',None)=='logical_add':answer=(answer[0],answer[1],1.,answer[3],answer[4])
        frame=self.frames[-1]
        self.data['pellets'].append(dict(owner=frame['character'].name,time=frame['time'],front_kind=getattr(front,'kind',None),parts=answer[1],body=answer[2],core=answer[3]))
        return answer

    def geometry(self,manager,geom,t):
        from calculator import aim,boss_pattern
        boss=self.boss
        if boss is None or self.frame_time!=t or geom is None:raise ValueError('Logical geometry requires its live coordinate frame')
        registry=registry_for(manager,boss);configured=self.bindings
        original={}
        for run in boss._runs:
            for slot,target in enumerate(run.targets):original[target.spec.name]=(target.spec.z,run.start_t,run.p.idx,slot,0)
        rows=[];logical={}
        for target in geom.targets:
            if target.name not in original or target.name.startswith(PREFIX):raise ValueError('Canonical collider identity is ambiguous')
            rows.append((original[target.name],target))
        for slot,row in enumerate(self.spec):
            binding=configured[row['label']];run=boss._runs[binding.run]
            if not run.active or run.opens<1 or binding.slot>=len(run.adds) or not run.adds[binding.slot].alive:continue
            actor=registry.view(ActorKind.ADD,row['label']);shape=row['shape'];label=PREFIX+str(slot)
            target=boss_pattern.GeomTarget(label,'logical_add',aim.Shape(**{k:shape[k] for k in ('x','y','r','w','h','rot')}))
            rows.append(((shape['z'],run.start_t,run.p.idx,binding.slot,1),target));logical[label]=(actor.handle,actor.label)
        rows.sort(key=lambda row:row[0],reverse=True)
        proxy=SimpleNamespace(targets=tuple(g for _,g in rows),core=geom.core,auto_aim=geom.auto_aim,pierce_px=geom.pierce_px,explosion_scale=geom.explosion_scale)
        if manager not in self.data['managers']:self.data['managers'].append(manager)
        return proxy,logical,registry.view(ActorKind.BODY,'__enemy__').handle

    @contextmanager
    def shot(self,character,t,manager):
        frame=dict(character=character,manager=manager,time=t,snapshot=None,normal=not character._wc_is_skill_damage())
        self.frames.append(frame)
        try:yield
        finally:assert self.frames.pop() is frame

    def fire(self,original):
        # Keep the real method's self/t/bm locals and code identity boundary
        # available to existing passive full-battle profilers.
        from calculator import timeline
        if original.__globals__ is not timeline.__dict__:raise ValueError('Install logical geometry before passive shot/group wrappers')
        return rewrite_reference(original,LogicalShot(original.__name__),dict(shot=1),compose=getattr(original,'_nikke_reference_code',None) is original.__code__)

    def pellet(self,original,fallback):
        @wraps(original)
        def call(character,geom,t,manager,enemy,buffs,ht,expected,tag_of,extra):
            if not self.frames or not self.frames[-1]['normal']:return fallback(character,geom,t,manager,enemy,buffs,ht,expected,tag_of,extra)
            if expected:raise ValueError('Logical geometry currently requires sampled canonical pellets')
            frame=self.frames[-1]
            if (frame['character'],frame['manager'],frame['time'])!=(character,manager,t):raise ValueError('Logical pellet left its shot owner')
            if frame['snapshot'] is None:
                frame['snapshot']=self.geometry(manager,geom,t)
                self.data['shots'].append(dict(owner=character.name,time=t,targets=[list((int(h.kind),h.identity,h.generation)) for h,_ in frame['snapshot'][1].values()]))
            proxy,logical,body=frame['snapshot'];answer=original(character,proxy,t,manager,enemy,buffs,ht,expected,tag_of,extra)
            for event in answer[0]:
                target=logical.get(event.target) if event.target else (body,'__enemy__')
                if target is not None:
                    if id(event) in self.pending:raise ValueError('Logical packet identity reused')
                    self.pending[id(event)]=(event,manager,*target)
            return answer
        return call

    @contextmanager
    def land(self,manager,boss,event,t):
        item=self.pending.pop(id(event),None)
        if item is None:yield;return
        if item[0] is not event or item[1] is not manager or boss is not self.boss or event.to is not None or event.rule or event.split:raise ValueError('Logical packet ownership or explicit route changed')
        handle,label=item[2:];saved=(event.target,event.to);event.target='';event.to=(label,);self.routing.append((event,handle,manager))
        self.data['packets'].append(dict(owner=event.caster,time=t,target=[int(handle.kind),handle.identity,handle.generation],label=label,damage=event.damage))
        try:yield
        finally:
            assert self.routing.pop()==(event,handle,manager)
            event.target,event.to=saved

@contextmanager
def logical_actor_geometry(spec):
    import engine_worker
    from calculator import timeline
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    runtime=LogicalGeometry(spec);original=timeline.simulate;boss_type=timeline.BossScript
    if getattr(boss_type,'_nikke_logical_geometry',False):raise ValueError('Nested logical geometry scope')
    class Boss(boss_type):
        _nikke_logical_geometry=True
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            if runtime.boss is not None:raise ValueError('One logical world per scope')
            runtime.bindings={b.label:b for b in bindings([run.p for run in self._runs]) if b.kind==ActorKind.ADD}
            if any(row['label'] not in runtime.bindings for row in runtime.spec):raise ValueError('Logical collider must bind a configured ADD, never a PART or typed proxy')
            runtime.boss=self;runtime.data['bosses'].append(self)
        def begin_frame(self,t,enemy):
            runtime.frame_time=t;return super().begin_frame(t,enemy)
        def live_adds(self):
            rows=super().live_adds()
            if not runtime.routing or runtime.suspended:return rows
            _,handle,manager=runtime.routing[-1];registry=registry_for(manager,self)
            return live_for_handle(registry,rows,handle)
        def route(self,event,has_state=None):
            suspend=bool(runtime.routing and runtime.routing[-1][0] is not event)
            runtime.suspended+=int(suspend)
            try:return super().route(event,has_state)
            finally:runtime.suspended-=int(suspend)
    rewritten=rewrite_reference(original,LogicalLand(),dict(land=1),compose=True)
    pellet=timeline.CharState._coord_pellet
    rewritten_pellet=rewrite_reference(pellet,LogicalPelletChannels(),dict(returns=5),compose=getattr(pellet,'_nikke_reference_code',None) is pellet.__code__)
    try:
        with patch.object(timeline,'BossScript',Boss),patch.object(timeline.CharState,'_fire',runtime.fire(timeline.CharState._fire)),patch.object(timeline.CharState,'_charge_fire',runtime.fire(timeline.CharState._charge_fire)),patch.object(timeline.CharState,'_coord_pellet',runtime.pellet(rewritten_pellet,pellet)),patch.dict(original.__globals__,{'_nikke_logical_geometry_land':runtime.land,'_nikke_logical_pellet_channels':runtime.channels,'_nikke_logical_geometry_shot':runtime.shot}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):
            yield runtime.data
            if runtime.pending or runtime.frames or runtime.routing or runtime.suspended:raise ValueError('Logical geometry packet or frame leaked')
    finally:runtime.pending.clear()
