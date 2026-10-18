"""Generation-bound staged stack applications with a scoped damage override."""
import ast,math,heapq
from dataclasses import dataclass
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,state
from reference_rewrite import rewrite_reference
from staged_dot_specs import specification,resolved_count,MODEL_WARNING

@dataclass
class StagedDot:
    caster:str
    effect:object
    carrier:object
    spec:object
    generation:int
    sequence:int
    start:float
    total:int
    index:int=0
    @property
    def next_at(self):return self.start+(self.index+1)*self.spec.gap

def get_spec(manager,effect,caster):return specification(effect,caster,manager._effects)
@dataclass(frozen=True)
class StagedBinding:
    effect:object
    caster:str
    spec:object
    count:int

def binding(manager,effect,caster,t=None):
    spec=get_spec(manager,effect,caster)
    if spec is None:return None
    if t is not None:manager._cur_t=t
    return StagedBinding(effect,caster,spec,resolved_count(manager,spec,caster))

def zero(manager,effect,caster):
    bound=binding(manager,effect,caster)
    return bound is not None and bound.count==0

def prepare(manager,effect,caster,t,bound=None):
    bound=binding(manager,effect,caster,t) if bound is None else bound
    if bound is None:return
    if not isinstance(bound,StagedBinding) or bound.effect is not effect or bound.caster!=caster:raise ValueError('Staged binding changed identity')
    spec=bound.spec
    carrier=next((a for a in manager._active if a.effect is effect and a.caster==caster),None)
    if carrier is None:raise ValueError('Staged application has no current carrier')
    resources=pool(manager,'staged_dot');previous=resources.get(carrier.uid);total=bound.count
    if total==0:raise ValueError('Zero-count staged attachment must be rejected before activation')
    runtime=state(manager);sequence=getattr(runtime,'staged_sequence',0)+1;runtime.staged_sequence=sequence
    record=StagedDot(caster,effect,carrier,spec,previous.generation+1 if previous else 1,sequence,t,total)
    resources[carrier.uid]=record;carrier.stack=0
    if not hasattr(runtime,'staged_heap'):runtime.staged_heap=[]
    heapq.heappush(runtime.staged_heap,(record.next_at,record.sequence,record.index,record))
    if len(runtime.staged_heap)>max(128,4*len(resources)):
        runtime.staged_heap[:]=[(r.next_at,r.sequence,r.index,r) for r in resources.values() if r.index<r.total and valid(manager,r)]
        heapq.heapify(runtime.staged_heap)
    last=t+total*spec.gap;end=math.inf if spec.duration<0 else last+spec.duration
    carrier.expires_at=end;manager._bump_value_version()
    manager._dot_timers[id(effect)]=(caster,last+spec.post_delay,end)

def valid(manager,record):
    return pool(manager,'staged_dot').get(record.carrier.uid) is record and any(a is record.carrier for a in manager._active)

def tick(manager,t):
    if not manager._damage_handler:return
    runtime=state(manager);heap=getattr(runtime,'staged_heap',None);steps=0
    while heap and heap[0][0]<=t:
        _,_,index,record=heapq.heappop(heap)
        if index!=record.index or not valid(manager,record):continue
        steps+=1
        if steps>4096:raise ValueError('Staged callbacks exceed per-frame capacity')
        record.index+=1;record.carrier.stack=record.spec.stack(record.index);manager._bump_value_version()
        if record.index<record.total:heapq.heappush(heap,(record.next_at,record.sequence,record.index,record))
        if not hasattr(runtime,'damage_stack_scopes'):runtime.damage_stack_scopes=[]
        runtime.damage_stack_scopes.append(record)
        try:manager._damage_handler(record.effect,record.caster,t)
        finally:runtime.damage_stack_scopes.pop()

def damage_stack(manager,effect,caster):
    for record in reversed(getattr(state(manager),'damage_stack_scopes',())):
        if record.effect is effect and record.caster==caster and valid(manager,record):
            return record.spec.damage_stack if record.spec.damage_stack is not None else record.carrier.stack
    return next((a.stack for a in manager._active if a.caster==caster and a.effect.get('name')==effect.get('name','')),None)

class ActivationRewrite(ast.NodeTransformer):
    def __init__(self):self.counts={'guard':0,'lookup':0,'prepare':0}
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_activate':
            statements=ast.parse('_staged_binding=self.staged_dot_binding(eff,caster,t)\nif _staged_binding is not None and _staged_binding.count==0:\n return').body
            node.body[:0]=[ast.copy_location(statement,node.body[0]) for statement in statements];self.counts['guard']+=1
        return node
    def visit_Assign(self,node):
        if any(isinstance(target,ast.Name) and target.id=='ramp_n' for target in node.targets):self.counts['lookup']+=1;return None
        return self.generic_visit(node)
    def visit_If(self,node):
        if isinstance(node.test,ast.Name) and node.test.id=='ramp_n':
            self.counts['prepare']+=1;return ast.copy_location(ast.parse('self.effect_runtime_periodic_prepare(eff,caster,t,_staged_binding)').body[0],node)
        return self.generic_visit(node)

class TickRewrite(ast.NodeTransformer):
    def __init__(self):self.counts={'tick':0}
    def visit_If(self,node):
        if isinstance(node.test,ast.BoolOp) and any(isinstance(n,ast.Attribute) and n.attr=='_ramp_pending' for n in ast.walk(node.test)):
            self.counts['tick']+=1;return ast.copy_location(ast.parse('self.effect_runtime_before_dot_tick(t)').body[0],node)
        return self.generic_visit(node)

class StackQueryRewrite(ast.NodeTransformer):
    def __init__(self):self.counts={'stack':0}
    def visit_For(self,node):
        if isinstance(node.target,ast.Name) and node.target.id=='ab' and any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scale' for t in n.targets) for n in ast.walk(node)):
            self.counts['stack']+=1;return ast.copy_location(ast.parse('scale=bm.staged_damage_stack(eff,caster)').body[0],node)
        return self.generic_visit(node)

def install():
    if 'staged_dot' in CATALOG.handlers:return
    from calculator import buff_manager,timeline
    from runner import sim
    manager=buff_manager.BuffManager
    manager._activate=rewrite_reference(manager._activate,ActivationRewrite(),dict(guard=1,lookup=1,prepare=1),compose=True)
    manager.tick=rewrite_reference(manager.tick,TickRewrite(),dict(tick=1),compose=True)
    assert timeline.simulate is sim.simulate
    timeline.simulate=sim.simulate=rewrite_reference(timeline.simulate,StackQueryRewrite(),dict(stack=1),compose=True)
    manager.staged_dot_binding=binding;manager.staged_damage_stack=damage_stack
    manager.effect_runtime_periodic_prepare=lambda self,*args:CATALOG.emit('periodic_prepare',self,*args)
    manager.effect_runtime_before_dot_tick=lambda self,t:CATALOG.emit('before_dot_tick',self,t)
    original=manager.reset
    @wraps(original)
    def reset(self,*args,**kwargs):
        result=original(self,*args,**kwargs);pool(self,'staged_dot').clear();state(self).staged_sequence=0
        if hasattr(state(self),'staged_heap'):state(self).staged_heap.clear()
        return result
    manager.reset=reset
    original_register=manager._register_all
    @wraps(original_register)
    def register(self,*args,**kwargs):
        result=original_register(self,*args,**kwargs)
        descriptors=[specification(e,owner,self._effects) for e,owner in self._effects]
        if any(spec is not None for spec in descriptors):state(self).model_warnings.append(MODEL_WARNING)
        return result
    manager._register_all=register
    CATALOG.register('staged_dot',Handler(periodic_prepare=prepare,before_dot_tick=tick,resource_kind='staged_dot'))
