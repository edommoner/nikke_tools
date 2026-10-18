"""Collect then latch completions before synchronous child delivery.

Progress belongs to (carrier UID, refresh epoch, exact actor generation). An old
completion can never remove a refreshed or replaced marker after its callbacks.
"""
import ast
from dataclasses import dataclass
from functools import wraps
from effect_runtime import CATALOG,Handler,state,pool
from target_counter_specs import STAT,SINGLE_BODY_WARNING,CounterCompletion,specification
from reference_rewrite import rewrite_reference

@dataclass
class Counter:
    carrier:object
    spec:object
    caster:str
    epoch:int
    expires:float
    credit:float=0
    done:bool=False

def prepare(manager,effect,caster,t,carrier,initialized=False):
    spec=specification(effect)
    if spec is None:return
    if initialized:raise ValueError('Stack initialization cannot initialize a target counter')
    if carrier is None or carrier.effect is not effect or carrier.caster!=caster or not any(ab is carrier for ab in manager._active):raise RuntimeError('Counter preparation requires the exact carrier')
    if carrier.target_chars!=['__enemy__']:raise ValueError('Counter carrier must resolve to the enemy sentinel; actor binding is explicit')
    runtime=state(manager);resources=pool(manager,'target_hit_counter');old=resources.get(carrier.uid)
    runtime.counter_defined=True
    credit=old.credit if spec.preserve and old and not old.done and old.spec.actor==spec.actor and old.expires>t else 0
    runtime.counter_epoch+=1
    resources[carrier.uid]=Counter(carrier,spec,caster,runtime.counter_epoch,carrier.expires_at,credit)

def _live(manager,record,t):
    return not record.done and record.expires>t and any(ab is record.carrier for ab in manager._active)

def _complete(manager,ready,t):
    runtime=state(manager);resources=pool(manager,'target_hit_counter')
    for record,completion in ready:
        if completion.reason!='cancel':
            runtime.counter_completed+=1;runtime.counter_last=(t,completion)
            if runtime.counter_trace is not None:runtime.counter_trace.append((t,completion))
        # The old marker remains visible throughout its completion children.
        try:
            if completion.reason!='cancel':manager.notify('event:target_counter_complete:'+completion.name,t,completion.owner,
                                 completion=completion,impact=completion.impact)
        finally:
            current=resources.get(completion.uid)
            if current is record and current.epoch==completion.epoch:
                present=any(ab is record.carrier for ab in manager._active)
                manager._active=[ab for ab in manager._active if ab is not record.carrier]
                resources.pop(completion.uid,None)
                if present:
                    manager._invalidate_buffs_cache()
                    manager.notify('event:state_end:'+completion.name,t,completion.owner)

def _collect(manager,t,impact=None,dead=None):
    runtime=state(manager);ready=[]
    for record in tuple(pool(manager,'target_hit_counter').values()):
        if not _live(manager,record,t):continue
        spec=record.spec
        if dead is not None:
            if spec.actor!=dead:continue
        else:
            if impact.target in runtime.dead_actors or not spec.accepts(impact) or impact.credit<=0:continue
            if impact.attacker not in manager.squad_names or spec.owner_only and impact.attacker!=record.caster:continue
            record.credit=min(spec.threshold,record.credit+impact.credit)
            if record.credit<spec.threshold:continue
        record.done=True # All ready siblings latch before any nested child can hit them.
        ready.append((record,CounterCompletion(record.carrier.uid,record.epoch,record.caster,
            record.carrier.effect['name'],spec.actor,record.credit,('death' if spec.on_death else 'cancel') if dead else 'threshold',impact)))
    _complete(manager,ready,t)

def impact(manager,packet,t):_collect(manager,t,impact=packet)

def target_death(manager,actor,t):
    runtime=state(manager)
    if actor in runtime.dead_actors:return
    if len(runtime.dead_actors)>=512:raise ValueError('Target death registry exceeds its verified capacity')
    runtime.dead_actors.add(actor)
    _collect(manager,t,dead=actor)

def actor_dead(manager,effect):return specification(effect).actor in state(manager).dead_actors

class BindingGuard(ast.NodeTransformer):
    def __init__(self):self.counts={'guard':0}
    def visit_FunctionDef(self,node):
        if node.name!='_activate':return node
        statement=ast.parse('if eff.get("stat")=="target_hit_counter" and self.counter_actor_dead(eff):\n return').body[0]
        node.body.insert(0,ast.copy_location(statement,node.body[0]));self.counts['guard']+=1;return node

class ModelWarnings(ast.NodeTransformer):
    def __init__(self):self.counts={'warnings':0}
    def visit_Assign(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='SimResult':
            statement=ast.parse('result.effect_model_warnings=bm.effect_model_warnings()').body[0]
            self.counts['warnings']+=1;return [node,ast.copy_location(statement,node)]
        return node

def install():
    if 'target_hit_counter' in CATALOG.handlers:return
    from calculator import buff_manager
    manager=buff_manager.BuffManager;original=manager._register_all
    manager.counter_actor_dead=actor_dead
    manager._activate=rewrite_reference(manager._activate,BindingGuard(),{'guard':1},compose=True)
    manager.effect_model_warnings=lambda self:list(state(self).model_warnings)
    from calculator import timeline
    from runner import sim
    assert timeline.simulate is sim.simulate
    simulate=rewrite_reference(timeline.simulate,ModelWarnings(),{'warnings':1},compose=True)
    timeline.simulate=sim.simulate=simulate
    @wraps(original)
    def register(self,*args,**kwargs):
        result=original(self,*args,**kwargs);definitions={}
        for effect,owner in self._effects:
            spec=specification(effect)
            if spec is None:continue
            if spec.single_body and any(p.get('kind') not in ('idle','groggy','core','move','buff','attack') for p in self.state.get('enemy',{}).get('patterns',[])):raise ValueError('Single-body capture credit is not defined for parts, adds or enemy barriers')
            key=(owner,effect['name'])
            if key in definitions and definitions[key]!=spec:raise ValueError('Same named counter requires identical actor and credit policies')
            definitions[key]=spec
        state(self).counter_defined=bool(definitions)
        state(self).model_warnings=[SINGLE_BODY_WARNING] if any(spec.single_body for spec in definitions.values()) else []
        for effect,owner in self._effects:
            if effect.get('stat') in ('buff_stack_add','buff_stack_remove','buff_stack_init','buff_max_stack_add','debuff_stack_add','debuff_stack_remove') and (owner,effect.get('target_effect')) in definitions:raise ValueError('Counter progress is separate from named buff stack manipulation')
        return result
    manager._register_all=register
    buff_manager._DIRECT_READ_STATS=buff_manager._DIRECT_READ_STATS|{STAT}
    CATALOG.register('target_hit_counter',Handler(prepare_activation=prepare,impact=impact,
        impact_interest=lambda manager:state(manager).counter_defined,resource_kind='target_hit_counter'))
