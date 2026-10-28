"""Declared named radial selection at real skill creation, existing Actor landing.

Original quantities, event loops, HP and damage arithmetic are not replaced.
Candidate order is the pinned nearest router's logical order, not a new game
proximity metric. Frozen identities cannot hit a subsequent actor generation.
"""
import ast,copy,math
from contextlib import contextmanager
from unittest.mock import patch
from effect_range_policy import query,MODEL
from effect_target_count_policy import _Query
from coordinate_logical_actor_geometry import normalize as shapes
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for
from impact_specs import ActorKind

COUNT='effect_target_count_add'

def capacity(manager,caster,marker,t,base):
    for effect,_ in manager._effects:
        if effect.get('stat')!=COUNT:continue
        value=effect.get('fixed_value');target=effect.get('target')
        if (effect.get('type')!='buff' or type(value) not in (int,float) or not math.isfinite(value) or value<0 or int(value)!=value
            or type(effect.get('target_effect')) is not str or not effect['target_effect']
            or not (target in ('self','all_allies') or type(target) is str and target.startswith('allies_with_buff:') and target.split(':',1)[1])
            or any(effect.get(k) is not None for k in ('scaling','values','tick_interval','tick_start'))):raise ValueError('Explicit fixed integral named capacity required')
    for active in manager._active:
        if active.effect.get('stat')==COUNT and active.target_chars is None:raise ValueError('Unresolved named capacity lifecycle')
    total=_Query(manager,marker,COUNT).get_buffs(caster,'__enemy__',t)[COUNT]
    value=base+total
    if not math.isfinite(value) or value!=int(value) or not 0<=value<=128:raise ValueError('Named capacity outside actor pool')
    return total,int(value)

def normalize(rules,geometry):
    colliders=shapes(geometry)
    if type(rules) is not list or not 1<=len(rules)<=16:raise ValueError('Explicit named battle rules required')
    names=set();out=[]
    for rule in rules:
        if type(rule) is not dict or set(rule)!={'owner','effect','base_radius','base_count','body_shape'}:raise ValueError('Literal named battle binding required')
        key=(rule['owner'],rule['effect'])
        if any(type(x) is not str or not x for x in key) or key in names:raise ValueError('Unique owner/effect binding required')
        radius=rule['base_radius'];count=rule['base_count']
        if type(radius) not in (int,float) or not math.isfinite(radius) or radius<0 or type(count) is not int or not 1<=count<=128:raise ValueError('Finite radius and bounded base capacity required')
        body=shapes([dict(label='__enemy__',shape=rule['body_shape'])])[0]['shape']
        names.add(key);out.append(dict(rule,base_radius=float(radius),body_shape=body))
    return out,colliders

class Capture(ast.NodeTransformer):
    def __init__(self):self.counts=dict(event=0,land=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='HitEvent' and any(k.arg=='rule' and isinstance(k.value,ast.Name) and k.value.id=='hit_rule' for k in node.keywords):
            self.counts['event']+=1
            return ast.copy_location(ast.Call(func=ast.Name(id='_nikke_named_range_capture',ctx=ast.Load()),args=[ast.Name(id=x,ctx=ast.Load()) for x in ('bm','boss','cs','eff','enm','t')]+[node],keywords=[]),node)
        return node
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_land':
            w=ast.parse('with _nikke_named_range_landing(ev,t):\n pass').body[0];w.body=node.body;node.body=[ast.copy_location(w,node.body[0])];self.counts['land']+=1
        return node

class NamedRangeBattle:
    def __init__(self,rules,geometry):
        rules,self.geometry=normalize(rules,geometry);self.rules={(r['owner'],r['effect']):r for r in rules};self.pending={};self.data=dict(casts=[],landings=[]);self.manager=None;self.boss=None
    def capture(self,manager,boss,cs,effect,enemy,t,event):
        rule=self.rules.get((cs.name,effect.get('name')))
        if rule is None:return event
        if effect.get('type')!='damage' or effect.get('target')!='enemies_nearest:'+str(rule['base_count']) or effect.get('tick_interval') or effect.get('hits_parts') or event.extra or event.to is not None:raise ValueError('Named range supports original plain nearest damage packets')
        if self.boss is None:self.boss=boss;self.manager=manager
        if self.boss is not boss or self.manager is not manager:raise ValueError('Named range requires one live battle')
        from calculator.timeline import GEOM_KEY
        geom=enemy.get(GEOM_KEY)
        if geom is None:raise ValueError('Named range needs live coordinate aim')
        ax,ay=cs._aim_point(manager,geom)
        value=query(manager,cs.name,effect['name'],t,base_radius=rule['base_radius'],model=MODEL)
        addition,limit=capacity(manager,cs.name,effect['name'],t,rule['base_count'])
        registry=registry_for(manager,boss);colliders={row['label']:row['shape'] for row in self.geometry};colliders['__enemy__']=rule['body_shape']
        # Preserve the canonical logical candidate order; geometry only filters.
        ranked=boss._ranked('enemies_nearest:128',None,cs.name)
        if ranked is None:raise ValueError('Bounded logical nearest candidates required')
        from coordinate_geometry_reference import evaluate
        selected=[];handles=[];distances=[]
        for label in ranked[0]:
            if label not in colliders:raise ValueError('Missing configured logical collider')
            shape=colliders[label];kind=1 if shape['r']>0 else 2
            answer=evaluate((kind,shape['x'],shape['y'],shape['r'],shape['w'],shape['h'],shape['rot'],ax,ay,0.,value['radius']))
            actor=registry.view(ActorKind.BODY if label=='__enemy__' else ActorKind.ADD,label)
            distances.append(dict(label=label,handle=[int(actor.handle.kind),actor.handle.identity,actor.handle.generation],distance=answer['distance'],inside=answer['contains']))
            if actor.alive and answer['contains'] and len(selected)<limit:selected.append(label);handles.append(actor.handle)
        row=dict(owner=cs.name,effect=effect['name'],time=t,aim=[ax,ay],**value,base_count=rule['base_count'],additional_targets=addition,capacity=limit,candidates=distances,recipients=[dict(label=n,handle=[int(h.kind),h.identity,h.generation]) for n,h in zip(selected,handles)])
        self.data['casts'].append(row);self.pending[id(event)]=(tuple(selected),tuple(handles),len(self.data['casts'])-1)
        # Preserve the exact HitEvent object observed by native creation tracing.
        event.to=tuple(selected);return event
    def route(self,boss,event,fallback,*args,**kwargs):
        pending=self.pending.get(id(event))
        if pending is None:return fallback(boss,event,*args,**kwargs)
        labels,handles,_=pending;registry=registry_for(self.manager,boss);out=[]
        for label,handle in zip(labels,handles):
            view=registry.view(handle.kind,label)
            if view.alive and view.handle==handle:out.append((label,1.))
        return out
    @contextmanager
    def landing(self,event,t):
        pending=self.pending.get(id(event))
        if pending is not None:
            accepted=self.route(self.boss,event,lambda *_:None)
            self.data['landings'].append(dict(cast=pending[2],created=event.t,landed=t,damage=event.damage,recipients=[label for label,_ in accepted]))
        try:yield
        finally:self.pending.pop(id(event),None)

@contextmanager
def named_range_battle(rules,geometry):
    from calculator import timeline,boss_pattern
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    runtime=NamedRangeBattle(rules,geometry);original=timeline.simulate;route=boss_pattern.BossScript.route
    rewritten=rewrite_reference(original,Capture(),dict(event=1,land=1),compose=True)
    def routed(boss,event,*args,**kwargs):return runtime.route(boss,event,route,*args,**kwargs)
    with patch.dict(original.__globals__,{'_nikke_named_range_capture':runtime.capture,'_nikke_named_range_landing':runtime.landing}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten),patch.object(boss_pattern.BossScript,'route',routed):
        yield runtime.data
    if runtime.pending:raise ValueError('Named range packets remained beyond the battle boundary')
