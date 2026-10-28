"""Declared magazines on real BODY/ADD generations, using the native clock.

The unchanged native percentage operator supplies arithmetic and completion
notification. Existing scheduled attack attempts are gated at their original
delivery boundary; they are never retimed or replaced. Fixed capacities and
whole-magazine reloads are a declared CPU model, not game/default admission.
"""
import ast,math
from contextlib import contextmanager
from dataclasses import dataclass,asdict
from types import FunctionType
from unittest.mock import patch
from impact_specs import ActorKind
from portable_geometry_specs import number
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for
from world_actor_specs import bindings


def normalize(spec):
    if type(spec) is not list or not 1<=len(spec)<=128:raise ValueError('One to128 declared enemy magazines required')
    rows=[];labels=set()
    for r in spec:
        if type(r) is not dict or set(r)!={'label','capacity','initial','reload_seconds','cancel_on_full'}:raise ValueError('Literal magazine fields required')
        if type(r['label']) is not str or not r['label'] or r['label'] in labels:raise ValueError('Distinct enemy magazine labels required')
        if type(r['capacity']) is not int or not 1<=r['capacity']<=2147483647:raise ValueError('Positive i32 magazine capacity required')
        if type(r['initial']) is not int or not 0<=r['initial']<=r['capacity']:raise ValueError('Initial rounds must fit capacity')
        seconds=float(number(r['reload_seconds'],nonnegative=True))
        if seconds<=0 or type(r['cancel_on_full']) is not bool:raise ValueError('Positive reload duration and explicit cancellation control required')
        rows.append(dict(r,reload_seconds=seconds));labels.add(r['label'])
    return rows


def rebind_percentage_operator(original,states,resolve):
    expected={'_cancel_reload_if_full','_effective_max_ammo','_resolve_targets','bm','char_states'}
    if original.__name__!='handle_ammo_charge_pct' or set(original.__code__.co_freevars)!=expected:raise ValueError('Native ammo percentage operator changed')
    def cell(value):return (lambda:value).__closure__[0]
    replacement={'char_states':states,'_resolve_targets':resolve}
    closure=tuple(cell(replacement[n]) if n in replacement else c for n,c in zip(original.__code__.co_freevars,original.__closure__,strict=True))
    result=FunctionType(original.__code__,original.__globals__,original.__name__,original.__defaults__,closure)
    result.__kwdefaults__=original.__kwdefaults__
    assert result.__code__ is original.__code__
    return result


@dataclass
class Magazine:
    name:str
    actor:object
    capacity:int
    ammo:int
    reload_seconds:float
    reload_cancel_on_full:bool
    reloading_until:float=-1.
    _sim_log:object=None
    def _full_ammo(self,manager,t):return self.capacity
    def _cancel_reload(self,t,manager):
        from calculator import timeline
        timeline.CharState._cancel_reload(self,t,manager)


def handle_value(h):return [int(h.kind),h.identity,h.generation]


def source_label(hit):
    # AttackHit.source is an unprefixed source name; registry labels use the
    # ADD_PREFIX format defined by the configured world actor bindings.
    from calculator.boss_pattern import ADD_PREFIX
    return ADD_PREFIX+hit.source if hit.source else '__enemy__'


def validate_enemy_effects(effects,squad_names):
    """Shared native/static boundary of the fixed enemy magazine model."""
    for eff,_ in effects:
        target=eff.get('target','self')
        allied=target in ('self','all_allies') if isinstance(target,str) else False
        if isinstance(target,str):allied|=target in squad_names or target.startswith('allies_')
        if allied:continue
        if eff.get('stat')=='ammo_charge_pct' and target!='all_enemies':raise ValueError('Only all_enemies percentage routing is connected')
        if eff.get('type')=='weapon_change' or eff.get('stat') in ('max_ammo_pct','max_ammo_flat','infinite_ammo','force_reload','ammo_charge_flat'):raise ValueError('Enemy weapon/capacity/other ammo operators are outside the fixed magazine model')


class EnemyAmmo:
    allows_self_destruct=False

    def retired_queue_allowed(self,hit,t,key):
        return False

    def __init__(self,spec):
        self.spec=normalize(spec);self.manager=None;self.boss=None;self.registry=None
        self.bound={};self.current={};self.history={};self.pending={}
        self.data=dict(model='declared-enemy-magazine-attempt-v1',capacity_model='fixed-declared',
            reload_policy='start on empty attempt; refill on the first existing frame at/after deadline',
            source_schedule_policy='retain original scheduled attempts and counters; never retime blocked attempts',
            operator_code_reused=False,generations=[],charges=[],attempts=[],reloads=[])

    def bind(self,manager,boss):
        if self.boss is not None:
            if self.boss is not boss or self.manager is not manager:raise ValueError('One native world per enemy ammo scope')
            return
        configured={b.label:b for b in bindings([run.p for run in boss._runs])}
        labels={r['label'] for r in self.spec}
        for row in self.spec:
            b=configured.get(row['label'])
            if b is None or b.kind not in (ActorKind.BODY,ActorKind.ADD):raise ValueError('Magazine must bind a real BODY/ADD actor')
            if b.kind==ActorKind.ADD and boss._runs[b.run].p.summon.self_destruct and not self.allows_self_destruct:raise ValueError('Self-destruct launch timing is outside this magazine model')
            self.bound[b.label]=b
        for run in boss._runs:
            if run.p.kind=='attack' and '__enemy__' not in labels:raise ValueError('Every body attack needs its declared magazine')
            if run.p.summon is not None and run.p.summon.attack is not None:
                if any(b.label not in labels for b in configured.values() if b.kind==ActorKind.ADD and boss._runs[b.run] is run):raise ValueError('Every attacking ADD needs its declared magazine')
        # Capacity/mode changes need a richer provider, not silent fixed values.
        validate_enemy_effects(manager._effects,manager.squad_names)
        self.manager=manager;self.boss=boss;self.registry=registry_for(manager,boss)

    def refresh(self,t):
        if self.boss is None:raise ValueError('Enemy magazines require the native world frame')
        for rule in self.spec:
            label=rule['label'];b=self.bound[label]
            if b.kind==ActorKind.ADD and self.boss._runs[b.run].opens==0:continue
            view=self.registry.view(b.kind,label);key=view.handle
            if key not in self.history:
                mag=Magazine(label,key,rule['capacity'],rule['initial'],rule['reload_seconds'],rule['cancel_on_full'])
                self.history[key]=mag
                self.data['generations'].append(dict(time=t,label=label,actor=handle_value(key),initial=mag.ammo,capacity=mag.capacity))
            mag=self.history[key]
            if view.alive:
                self.current[label]=mag
                if mag.reloading_until>0 and t>=mag.reloading_until:
                    due=mag.reloading_until;before=mag.ammo;mag.ammo=mag.capacity;mag.reloading_until=-1.
                    self.data['reloads'].append(dict(kind='complete',time=t,deadline=due,label=label,actor=handle_value(key),before=before,after=mag.ammo))
            else:self.current.pop(label,None)

    def targets(self,eff,caster):
        ranked=self.boss._ranked('all_enemies',None,caster)
        if ranked is None:raise ValueError('Native all-enemy ranking changed')
        return [label for label in ranked[0][:ranked[1]] if label in self.current]

    def install(self,manager,original):
        if self.manager is not None and self.manager is not manager:raise ValueError('One native manager per magazine scope')
        self.manager=manager
        bound=rebind_percentage_operator(original,self.current,self.targets)
        self.data['operator_code_reused']=bound.__code__ is original.__code__
        def handler(eff,caster,t,val):
            if eff.get('target')!='all_enemies':return original(eff,caster,t,val)
            if type(val) not in (float,int) or not math.isfinite(val):raise ValueError('Finite enemy ammo percentage required')
            self.refresh(t);targets=self.targets(eff,caster)
            before={n:(self.current[n].ammo,self.current[n].reloading_until) for n in targets}
            record=dict(time=t,name=eff.get('name',''),caster=caster,value=val,targets=[],completion=[])
            self.data['charges'].append(record);notify=manager.notify
            def completed(event,t,caster,*args,**kwargs):
                if event=='event:'+record['name'] and record['name'] and caster==record['caster']:
                    record['completion'].append(dict(event=event,time=t,remaining={n:self.current[n].ammo for n in targets}))
                return notify(event,t,caster,*args,**kwargs)
            with patch.object(manager,'notify',completed):bound(eff,caster,t,val)
            if len(record['completion'])!=int(bool(record['name'])):raise ValueError('Exactly one original named completion required')
            for n in targets:
                mag=self.current[n];old,due=before[n]
                record['targets'].append(dict(label=n,actor=handle_value(mag.actor),capacity=mag.capacity,before=old,after=mag.ammo,change=mag.ammo-old))
                if due>0 and mag.reloading_until<0:self.data['reloads'].append(dict(kind='cancel',time=t,label=n,actor=handle_value(mag.actor),before=old,after=mag.ammo))
        return handler

    def frame(self,manager,boss,t,enemy):
        from calculator.boss_pattern import AttackSpec
        self.bind(manager,boss);events=boss.begin_frame(t,enemy);self.refresh(t)
        for hit in boss.attacks:
            if not isinstance(hit.spec,AttackSpec):continue
            label=source_label(hit)
            if label not in self.bound:raise ValueError('Queued attack source has no declared magazine')
            if id(hit) in self.pending:continue
            b=self.bound[label];view=self.registry.view(b.kind,label)
            self.pending[id(hit)]=(hit,view.handle)
        return events

    def attack(self,original,hit,t):
        self.refresh(t);label=source_label(hit);captured=self.pending.pop(id(hit),None)
        if captured is None or captured[0] is not hit:raise ValueError('Every enemy attack needs its original queued actor generation')
        key=captured[1];record=dict(time=t,label=label,actor=handle_value(key),pattern=hit.pattern,index=hit.index,status='stale')
        self.data['attempts'].append(record)
        try:view=self.registry.exact(key)
        except ValueError as error:
            if str(error)!='Stale world actor generation':raise
            return
        if not view.alive:
            if not self.retired_queue_allowed(hit,t,key):record['status']='dead';return
            record['retired_queue']=True
        mag=self.history[key] if not view.alive else self.current[label];record.update(before=mag.ammo,after=mag.ammo)
        if mag.reloading_until>0:record['status']='reloading';return
        if mag.ammo==0:
            mag.reloading_until=t+mag.reload_seconds
            self.data['reloads'].append(dict(kind='start',time=t,deadline=mag.reloading_until,label=label,actor=handle_value(key),before=0,after=0))
            record['status']='empty';return
        mag.ammo-=1;record.update(status='fired',after=mag.ammo)
        return original(hit,t)

    def finish(self):
        self.data['final']=[]
        for key,mag in self.history.items():
            snapshot=self.registry.view(key.kind,mag.name);alive=snapshot.handle==key and snapshot.alive
            self.data['final'].append(dict(label=mag.name,actor=handle_value(key),alive=alive,capacity=mag.capacity,remaining=mag.ammo,reloading_until=mag.reloading_until))
        if self.pending:raise ValueError('Queued attacks were not consumed by the native delivery boundary')

    def result(self,result):
        self.data['public_squad_hits']=[asdict(hit) for hit in result.squad_hits]
        return result


class AmmoFrame(ast.NodeTransformer):
    def __init__(self):self.counts=dict(frame=0,attack=0,result=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and ast.unparse(node.func)=='boss.begin_frame':
            if len(node.args)!=2 or node.keywords:raise ValueError('Native source frame call changed')
            call=ast.Call(func=ast.Name(id='_nikke_enemy_ammo_frame',ctx=ast.Load()),args=[ast.Name(id='bm',ctx=ast.Load()),ast.Name(id='boss',ctx=ast.Load()),*node.args],keywords=[]);self.counts['frame']+=1;return ast.copy_location(call,node)
        if isinstance(node.func,ast.Name) and node.func.id=='_boss_attack':
            if len(node.args)!=2 or node.keywords:raise ValueError('Native attack delivery call changed')
            call=ast.Call(func=ast.Name(id='_nikke_enemy_ammo_attack',ctx=ast.Load()),args=[node.func,*node.args],keywords=[]);self.counts['attack']+=1;return ast.copy_location(call,node)
        return node
    def visit_Return(self,node):
        if isinstance(node.value,ast.Name) and node.value.id=='result':
            self.counts['result']+=1
            return ast.copy_location(ast.Return(ast.Call(func=ast.Name(id='_nikke_enemy_ammo_result',ctx=ast.Load()),args=[node.value],keywords=[])),node)
        return self.generic_visit(node)


@contextmanager
def enemy_ammo(spec,*,runtime_class=EnemyAmmo):
    from calculator import timeline
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    runtime=runtime_class(spec);original=timeline.simulate;register=timeline._register_instant_handlers
    rewritten=rewrite_reference(original,AmmoFrame(),dict(frame=2,attack=1,result=1),compose=True)
    def install(manager,states,burst):
        answer=register(manager,states,burst)
        manager.register_instant_handler('ammo_charge_pct',runtime.install(manager,manager._instant_handlers['ammo_charge_pct']))
        return answer
    with patch.dict(original.__globals__,{'_nikke_enemy_ammo_frame':runtime.frame,'_nikke_enemy_ammo_attack':runtime.attack,'_nikke_enemy_ammo_result':runtime.result}),patch.object(timeline,'_register_instant_handlers',install),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):
        yield runtime.data
        runtime.finish()
