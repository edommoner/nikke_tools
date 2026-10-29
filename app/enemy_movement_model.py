"""Declared movement on existing live ADD colliders and native duration carriers.

No new clock, actor, buff lifetime, hit selector or damage formula lives here.
Motion and simultaneous-status policies are explicit inputs, not game claims.
"""
import ast,copy,math
from contextlib import contextmanager
from unittest.mock import patch
from impact_specs import ActorKind
from portable_geometry_specs import number
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for

STATS=('enemy_movement_disable','force_move')


def normalize(spec):
    if type(spec) is not dict or set(spec)!={'precedence','force_policy','recipient_policy','actors'}:
        raise ValueError('Explicit movement, overlap and recipient policies required')
    if spec['precedence'] not in ('disable-before-force','force-before-disable') or spec['force_policy']!='snap-to-declared-center':
        raise ValueError('Unsupported declared movement policy')
    if spec['recipient_policy']!='canonical-all-in-range':raise ValueError('Declare the canonical all-in-range approximation explicitly')
    if type(spec['actors']) is not list or not 1<=len(spec['actors'])<=127:raise ValueError('One to127 existing ADD colliders required')
    actors=[];seen=set()
    for row in spec['actors']:
        if type(row) is not dict or set(row)!={'label','velocity','force_center'} or type(row['label']) is not str or not row['label'] or row['label'] in seen:
            raise ValueError('Distinct explicit actor motion rows required')
        seen.add(row['label']);out=dict(label=row['label'])
        for key in ('velocity','force_center'):
            v=row[key]
            if type(v) is not list or len(v)!=2:raise ValueError('Two finite screen-space components required')
            out[key]=[float(number(x)) for x in v]
        actors.append(out)
    return dict(spec,actors=actors)


def integrate(position,velocity,center,dt,disabled,forced,precedence):
    """Ordered binary64 arithmetic; no normalization, distance or trig formula."""
    if type(disabled) is not bool or type(forced) is not bool or precedence not in ('disable-before-force','force-before-disable'):
        raise ValueError('Explicit movement status and precedence required')
    if type(dt) not in (int,float) or not math.isfinite(dt) or dt<0:raise ValueError('Finite nonnegative movement interval required')
    if disabled and (not forced or precedence=='disable-before-force'):answer=list(position)
    elif forced:answer=list(center)
    else:answer=[position[0]+velocity[0]*dt,position[1]+velocity[1]*dt]
    if any(not math.isfinite(x) for x in answer):raise ValueError('Movement coordinate overflow')
    return answer


class MovementFrame(ast.NodeTransformer):
    def __init__(self):self.counts=dict(frame=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and ast.unparse(node.func)=='boss.begin_frame':
            if len(node.args)!=2 or node.keywords:raise ValueError('Original world frame boundary changed')
            call=ast.parse('_nikke_enemy_movement_frame(bm,boss,None,None)',mode='eval').body
            call.args[2:]=node.args;self.counts['frame']+=1;return ast.copy_location(call,node)
        return node


class EnemyMovement:
    def __init__(self,spec):
        self.spec=normalize(spec);self.geometry=None;self.boss=None;self.manager=None;self.states={};self.last_time=None
        self.data=dict(model='declared-add-motion-v1',policies={k:self.spec[k] for k in ('precedence','force_policy','recipient_policy')},generations=[],frames=[])

    def attach(self,geometry):
        if self.geometry is not None:raise ValueError('One logical geometry per movement scope')
        labels={r['label'] for r in geometry.spec}
        if labels!={r['label'] for r in self.spec['actors']}:raise ValueError('Every moving actor must own exactly one actual logical collider')
        self.geometry=geometry;self.initial={r['label']:copy.deepcopy(r['shape']) for r in geometry.spec}

    def fields(self,manager,label):
        return [(stat,ab) for stat in STATS for ab in manager._by_stat(stat)
                if label in (ab.target_chars or ()) and manager.enemy_field_visible(ab,label)]

    def frame(self,manager,boss,t,enemy):
        self.validate_frame(manager,boss,t)
        events=boss.begin_frame(t,enemy)
        self.advance(manager,boss,t)
        return events

    def validate_frame(self,manager,boss,t):
        if self.geometry is None or self.geometry.boss is not boss:raise ValueError('Movement needs the existing logical geometry world')
        if self.boss is not None and (self.boss is not boss or self.manager is not manager):raise ValueError('One native clock/manager per movement scope')
        if type(t) not in (int,float) or not math.isfinite(t) or self.last_time is not None and t<self.last_time:raise ValueError('Monotonic native frame time required')

    def advance(self,manager,boss,t):
        """Consume the already advanced owning clock, before geometry capture."""
        self.validate_frame(manager,boss,t)
        self.boss=boss;self.manager=manager
        if self.last_time==t:return
        registry=registry_for(manager,boss);shapes={r['label']:r['shape'] for r in self.geometry.spec}
        for rule in self.spec['actors']:
            label=rule['label'];binding=self.geometry.bindings[label];run=boss._runs[binding.run]
            if run.opens==0:continue
            view=registry.view(ActorKind.ADD,label);old=self.states.get(label)
            if old is None or old['handle']!=view.handle:
                initial=self.initial[label];old=dict(handle=view.handle,position=[initial['x'],initial['y']],time=t)
                self.states[label]=old
                self.data['generations'].append(dict(label=label,actor=[5,view.handle.identity,view.handle.generation],time=t,position=list(old['position'])))
            previous=old['time'];position=list(old['position']);segments=[]
            if view.alive:
                fields=self.fields(manager,label)
                cuts=sorted({previous,t,*[float(x) for _,ab in fields for x in (ab.activated_at,ab.expires_at) if previous<x<t]})
                for left,right in zip(cuts,cuts[1:]):
                    active=[(stat,ab) for stat,ab in fields if ab.activated_at<=left and manager._live(ab,label,left)]
                    disabled=any(stat==STATS[0] for stat,_ in active);forced=any(stat==STATS[1] for stat,_ in active)
                    before=list(position);position=integrate(position,rule['velocity'],rule['force_center'],right-left,disabled,forced,self.spec['precedence'])
                    segments.append(dict(start=left,end=right,disabled=disabled,forced=forced,before=before,after=list(position),
                        fields=[dict(stat=stat,name=ab.effect['name'],caster=ab.caster,activated_at=ab.activated_at,expires_at=ab.expires_at) for stat,ab in active]))
            old.update(position=position,time=t)
            shapes[label]['x'],shapes[label]['y']=position
            if len(self.data['frames'])>=262144:raise ValueError('Movement observation capacity exceeded; no history truncation')
            self.data['frames'].append(dict(time=t,label=label,actor=[5,view.handle.identity,view.handle.generation],alive=view.alive,position=list(position),segments=segments))
        self.last_time=t


@contextmanager
def enemy_movement_runtime(spec):
    from calculator import timeline
    from runner import sim
    from coordinate_logical_actor_geometry import LogicalGeometry
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    original=timeline.simulate;runtime=EnemyMovement(spec);initialize=LogicalGeometry.__init__
    def attach(geometry,literal):
        initialize(geometry,literal);runtime.attach(geometry)
    rewritten=rewrite_reference(original,MovementFrame(),dict(frame=2),compose=True)
    with patch.object(LogicalGeometry,'__init__',attach),patch.dict(original.__globals__,{'_nikke_enemy_movement_frame':runtime.frame}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):
        yield runtime


@contextmanager
def enemy_movement(spec):
    with enemy_movement_runtime(spec) as runtime:yield runtime.data
