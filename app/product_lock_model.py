"""Declared generation locks at actual acquisition, shot and queue boundaries.

The shared lock policies own target selection. Original damage, HP, carrier and
weapon arithmetic remain in the checked reference executor. No global profiler
or CPU-computed schedule is needed by this product adapter.
"""
import ast,copy
from contextlib import contextmanager,ExitStack
from dataclasses import replace
from unittest.mock import patch
from reference_rewrite import rewrite_reference
from live_lock_delivery_policy import MODEL as DELIVERY_MODEL,select_live
from named_generation_locks import registry_views

ORDER='body-then-add-spawn-v1'
MARKER='록 온'


def normalize(value):
    if type(value) is not dict or set(value)!={'owner','marker','packet_skill','candidate_order','delivery','typed_bindings'}:
        raise ValueError('Lock On requires explicit owner, marker, packet_skill, candidate_order, delivery and typed_bindings')
    if any(type(value[k]) is not str or not value[k] for k in ('owner','packet_skill')) or value['marker']!=MARKER or value['candidate_order']!=ORDER or value['delivery']!=DELIVERY_MODEL:
        raise ValueError('Explicit existing named-lock and live-frozen delivery policies required')
    bindings=value['typed_bindings']
    if type(bindings) is not list or len(bindings)>128 or any(type(r) is not dict for r in bindings):
        raise ValueError('Explicit zero-to-128 typed bindings required')
    # Validate every literal even before the real graph is available. The
    # actual node names and clear semantics are checked again at preparation.
    if bindings:
        from destructible_world_runtime import compile_bindings
        nodes=[]
        for row in bindings:
            node=row.get('node')
            if type(node) is not str or not node:raise ValueError('Typed clock node name required')
            if node not in nodes:nodes.append(node)
        compile_bindings([dict(id=n) for n in nodes],bindings)
    return copy.deepcopy(value)


def validate_effects(effects,owners,spec):
    marker=[i for i,e in enumerate(effects) if e.get('stat')=='lock_on']
    if len(marker)!=1 or owners[marker[0]]!=spec['owner'] or effects[marker[0]].get('name')!=MARKER:
        raise ValueError('Exact original Lock On owner/marker binding required')
    # The existing physical adapter consumes this exact original definition.
    from portable_heavyarms_lock_cases import source_definitions
    if effects[marker[0]]!=source_definitions()[0]:raise ValueError('Unchanged original Lock On acquisition definition required')
    packets=[i for i,e in enumerate(effects) if e.get('name')==spec['packet_skill'] and owners[i]==spec['owner']]
    if len(packets)!=1 or effects[packets[0]]!=source_definitions()[8]:
        raise ValueError('Unchanged original frozen packet definition required')
    typed=[i for i,e in enumerate(effects) if e.get('target')=='all_projectiles']
    if len(typed)!=1 or owners[typed[0]]!=spec['owner'] or effects[typed[0]]!=source_definitions()[24]:
        raise ValueError('Unchanged original projectile damage definition required')
    return marker[0],packets[0],typed[0]


class QueueHooks(ast.NodeTransformer):
    def __init__(self):self.counts=dict(emission=0,landing=0,route=0,clock=0)
    def visit_Assign(self,node):
        self.generic_visit(node)
        if ast.unparse(node)=="enm = {**DEFAULT_ENEMY, **(enemy or {})}":
            self.counts['clock']+=1
            return [node,ast.copy_location(ast.parse('_nikke_product_lock_clock(enm)').body[0],node)]
        return node
    def visit_BoolOp(self,node):
        self.generic_visit(node)
        if ast.unparse(node)=='boss is not None and boss.has_summons and (ev.to is not None or boss.has_adds)':
            self.counts['route']+=1
            return ast.copy_location(ast.parse('boss is not None and (boss.has_summons or _nikke_product_lock_pending(ev)) and (ev.to is not None or boss.has_adds)',mode='eval').body,node)
        return node
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_handle_damage_eff':
            wrapper=ast.parse('with _nikke_product_lock_emission(bm,eff,caster,t,_dot_events):\n pass').body[0]
            wrapper.body=node.body;node.body=[ast.copy_location(wrapper,node.body[0])];self.counts['emission']+=1
        if node.name=='_land':
            wrapper=ast.parse('with _nikke_product_lock_landing(ev):\n pass').body[0]
            wrapper.body=node.body;node.body=[ast.copy_location(wrapper,node.body[0])];self.counts['landing']+=1
        return node


def public(data,typed):
    return dict(pulses=copy.deepcopy(data['lock_pulses']),shots=copy.deepcopy(data['lock_shots']),
        clears=len(data['lock_clears']),shot_quotas=copy.deepcopy(data['target_count_shots']),typed=copy.deepcopy(typed))


@contextmanager
def execution(value,names):
    import engine_worker  # Resolve aliases and private reader before rewriting.
    from calculator import timeline
    from calculator.buff_manager import BuffManager
    from runner import sim
    from effect_runtime import state
    from world_physical_locks_native import capture
    from world_actor_pool_native import actor_bindings
    from destructible_battle_runtime import typed_battle
    import importlib.util
    from pathlib import Path
    # Reuse the existing independent typed observation projection, not its
    # authored fixtures, schedules, damage or weapon metadata.
    path=Path(__file__).resolve().parents[1]/'research/verify-destructible-battle-short.py'
    loader=importlib.util.spec_from_file_location('product_lock_typed_reader',path);reader=importlib.util.module_from_spec(loader);loader.loader.exec_module(reader)
    spec=normalize(value)
    if spec['owner'] not in names:raise ValueError('Lock On owner must be in the original roster')
    case=dict(names=list(names),lock_owner=names.index(spec['owner']))
    shots=[];pending={};empty_finished=[];answer={};initialize=BuffManager.__init__
    def checked(manager,*args,**kwargs):
        initialize(manager,*args,**kwargs)
        validate_effects([e for e,_ in manager._effects],[owner for _,owner in manager._effects],spec)
    def shot(manager,t,snapshot):shots.append((manager,t,snapshot))
    @contextmanager
    def emission(manager,effect,caster,t,queue):
        selected=caster==spec['owner'] and effect.get('name')==spec['packet_skill'];first=len(queue)
        try:yield
        finally:
            if selected:
                own=[(i,e) for i,e in enumerate(queue) if i>=first and e.skill_name==spec['packet_skill'] and e.caster==caster]
                if own and (not shots or shots[-1][0] is not manager or shots[-1][1]!=t):raise ValueError('Frozen packet requires its same-shot snapshot')
                for hit,(index,event) in enumerate(own,1):
                    event=replace(event,to=());queue[index]=event
                    pending[id(event)]=(event,manager,shots[-1][2],hit,len(own))
    @contextmanager
    def landing(event):
        try:yield
        finally:pending.pop(id(event),None)
    @contextmanager
    def hooks():
        original=timeline.simulate
        if original is not sim.simulate:raise ValueError('Native lock executor aliases differ')
        rewritten=rewrite_reference(original,QueueHooks(),dict(emission=1,landing=1,route=1,clock=1),compose=True)
        route=timeline.BossScript.route
        def routed(boss,event,*args,**kwargs):
            row=pending.get(id(event))
            if row is None:return route(boss,event,*args,**kwargs)
            _,manager,snapshot,hit,hits=row;bound=state(manager).world_actor_registry
            if bound[0] is not boss:raise ValueError('Lock packet left its owning battle')
            chosen=select_live(snapshot,hit,hits,registry_views(bound[1]),model=spec['delivery'])
            if chosen.handle is None:return []
            h=chosen.handle
            binding=next(b for b in actor_bindings(boss) if int(b.kind)==int(h.kind) and b.identity==h.identity)
            return [(binding.label,1.)]
        def clock(enemy):
            if not enemy.get('patterns'):enemy['patterns']=[dict(id='portable-empty-world',kind='idle')]
            if spec['typed_bindings']:
                from destructible_world_runtime import compile_bindings
                compile_bindings([dict(id=r['id']) for r in enemy['patterns']],spec['typed_bindings'])
        functions=dict(_nikke_product_lock_clock=clock,_nikke_product_lock_emission=emission,_nikke_product_lock_landing=landing,_nikke_product_lock_pending=lambda event:id(event) in pending)
        with patch.dict(original.__globals__,functions),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten),patch.object(timeline.BossScript,'route',routed):yield
    with ExitStack() as stack:
        stack.callback(timeline.random.setstate,timeline.random.getstate())
        stack.enter_context(patch.object(BuffManager,'__init__',checked))
        typed=stack.enter_context(typed_battle(spec['typed_bindings'],max_attacks=128)) if spec['typed_bindings'] else None
        if typed is None:
            finish=timeline.BossScript.finish
            def finished(boss,t):
                result=finish(boss,t);empty_finished.append(t);return result
            stack.enter_context(patch.object(timeline.BossScript,'finish',finished))
        data=stack.enter_context(capture(case,shot_observer=shot,primary_observer=hooks(),enemy_carrier=True))
        yield answer
    if pending:raise ValueError('Undrained frozen product packet')
    if typed is None:
        if len(empty_finished)!=1:raise ValueError('One completed empty typed world required')
        observation=dict(time=empty_finished[0],finished=True,state=[],attacks=[])
    else:observation=reader.typed_observation(case,typed)
    answer.update(public(data,observation))
