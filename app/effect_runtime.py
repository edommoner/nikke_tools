"""Ordered lifecycle hooks and per-manager state; one synchronous event adapter.

Hooks run inline: nested notifications finish before their parent resumes.
Registration order is explicit, sealed, and unrelated to character names.
No process-wide mutable battle state is stored in the catalog.
"""
import ast
from dataclasses import dataclass
from functools import wraps
from types import MappingProxyType
from lifecycle_specs import SPECS,ordered_specs
from impact_specs import EventFrame,Impact,ActorHandle,inherited_impact,inherits_target
from target_counter_specs import CounterCompletion

@dataclass(frozen=True)
class Handler:
    periodic_prepare: object = None
    before_dot_tick: object = None
    prepare_activation: object = None
    activate: object = None
    protection_activate: object = None
    before_body_heal: object = None
    before_notify: object = None
    impact: object = None
    impact_interest: object = None
    after_dispatch: object = None
    after_down: object = None
    instant_stat: str | None = None
    instant: object = None
    body_clamp: object = None
    heal_plan: object = None
    resource_kind: str | None = None
    retain_removed: object = None
    collect_removed: object = None
    discard_owner_on_down: bool = False

class Catalog:
    def __init__(self,specs=SPECS):
        self.specs=ordered_specs(specs);self.handlers={};self.sealed=False
    def register(self,key,handler):
        if self.sealed:raise RuntimeError('Lifecycle catalog is sealed')
        if key not in {s.key for s in self.specs}:raise ValueError('Unknown lifecycle operation: '+key)
        if key in self.handlers:raise ValueError('Duplicate lifecycle handler: '+key)
        spec=next(s for s in self.specs if s.key==key)
        if spec.cpu_phase and not callable(getattr(handler,spec.cpu_phase,None)):
            raise ValueError('Missing CPU lifecycle implementation: '+key)
        for name in ('periodic_prepare','before_dot_tick','prepare_activation','activate','protection_activate','before_body_heal','before_notify','after_dispatch',
                     'after_down','instant','body_clamp','heal_plan','retain_removed','collect_removed','impact','impact_interest'):
            callback=getattr(handler,name)
            if callback is not None and not callable(callback):raise TypeError('Lifecycle callback is not callable: '+name)
        if bool(handler.instant_stat)!=bool(handler.instant):raise ValueError('Incomplete instant handler')
        if handler.impact_interest is not None and handler.impact is None:raise ValueError('Impact interest requires an impact handler')
        if handler.instant_stat and any(h.instant_stat==handler.instant_stat for h in self.handlers.values()):
            raise ValueError('Duplicate instant stat: '+handler.instant_stat)
        for slot in ('body_clamp','heal_plan','resource_kind'):
            if getattr(handler,slot) and any(getattr(h,slot) for h in self.handlers.values()
                if slot!='resource_kind' or h.resource_kind==handler.resource_kind):
                raise ValueError('Duplicate lifecycle provider: '+slot)
        self.handlers[key]=handler
    def seal(self):
        missing={s.key for s in self.specs}-self.handlers.keys()
        if missing:raise ValueError('Missing lifecycle implementations: '+str(sorted(missing)))
        self.handlers=MappingProxyType(dict(self.handlers))
        phases=('periodic_prepare','before_dot_tick','prepare_activation','activate','protection_activate','before_body_heal','before_notify',
                'after_dispatch','after_down','instant','body_clamp','heal_plan','retain_removed','collect_removed','impact')
        self.phase_handlers=MappingProxyType({phase:tuple(callback for spec in self.specs
            if (callback:=getattr(self.handlers[spec.key],phase)) is not None) for phase in phases})
        self.impact_handlers=self.phase_handlers['impact']
        self.impact_interests=tuple((self.handlers[s.key].impact,self.handlers[s.key].impact_interest)
            for s in self.specs if self.handlers[s.key].impact is not None)
        self.sealed=True
    def emit(self,phase,manager,*args):
        if not self.sealed:raise RuntimeError('Lifecycle catalog is not sealed')
        # Stable ordering; callbacks must not change catalog membership mid-event.
        for callback in self.phase_handlers[phase]:callback(manager,*args)

CATALOG=Catalog()

class RuntimeState:
    def __init__(self):
        self.resources={};self.archives={};self.event_stack=[];self.activation_stack=[]
        self.impact_trace=None;self.impact_stack=[]
        self.counter_epoch=0;self.counter_trace=None;self.dead_actors=set()
        self.counter_defined=False
        self.counter_completed=0;self.counter_last=None
        self.model_warnings=[]
    def pool(self,kind):return self.resources.setdefault(kind,{})
    def archive(self,kind,values=None):
        # Compatibility facades can bind their existing per-manager ledger.
        # Archives outlive a carrier; resource maps contain active instances.
        if values is not None:self.archives[kind]=values
        return self.archives.setdefault(kind,{})
    def active_ids(self,manager):
        return {ab.uid for ab in manager._active}
    def retire(self,manager,kind,before,retain=None,owner=None):
        resources=self.pool(kind);active=self.active_ids(manager)
        for uid in before-active:
            record=resources.get(uid)
            if record is not None and not (retain and retain(record)):del resources[uid]
        if owner is not None:
            for uid,record in list(resources.items()):
                if record.caster==owner and uid not in active:del resources[uid]

def state(manager):
    if not hasattr(manager,'_effect_runtime_state'):manager._effect_runtime_state=RuntimeState()
    return manager._effect_runtime_state

def pool(manager,kind):return state(manager).pool(kind)

def publish_impact(manager,packet,t):
    """Synchronous delivery with immutable, nested target context."""
    if not isinstance(packet,Impact):raise TypeError('Expected an Impact')
    runtime=state(manager)
    runtime.impact_stack.append(packet)
    try:
        if runtime.impact_trace is not None:runtime.impact_trace.record(packet,t)
        for callback,interest in CATALOG.impact_interests:
            if interest is None or interest(manager):callback(manager,packet,t)
    finally:runtime.impact_stack.pop()

def observes_impacts(manager):
    return state(manager).impact_trace is not None or any(test is None or test(manager) for _,test in CATALOG.impact_interests)
def preparation(manager,effect,caster,t,carrier,initialized=False):CATALOG.emit('prepare_activation',manager,effect,caster,t,carrier,initialized)
_UNSPECIFIED=object()
def active_carrier(manager,effect,caster,carrier=_UNSPECIFIED):
    """Resolve only this activation, never another instance of its definition."""
    if carrier is _UNSPECIFIED:
        stack=state(manager).activation_stack
        carrier=stack[-1] if stack else None
    if carrier is None or carrier.effect is not effect or carrier.caster!=caster:return None
    return carrier if any(ab is carrier for ab in manager._active) else None

def _carrier_event(phase,manager,carrier,*args):
    runtime=state(manager);runtime.activation_stack.append(carrier)
    try:CATALOG.emit(phase,manager,*args)
    finally:runtime.activation_stack.pop()

def activation(manager,effect,caster,t,carrier=None):
    return _carrier_event('activate',manager,carrier,effect,caster,t)

class ActivationPreparation(ast.NodeTransformer):
    """Checked insertion points used by the existing single activation rewrite.

    The caller provides stack/count tracking and exact expected edit counts.
    Prepare after instance creation or stack update, before named child events.
    """
    def prepare_statements(self,node,carrier,effect='eff',initialized=False):
        statements=ast.parse('_runtime_carrier='+carrier+'\nself.effect_runtime_prepare('+effect+',caster,t,_runtime_carrier,'+str(initialized)+')').body
        return [ast.copy_location(statement,node) for statement in statements]
    def visit_AugAssign(self,node):
        self.generic_visit(node)
        if self.stack and self.stack[-1]=='_activate' and isinstance(node.target,ast.Attribute) and node.target.attr=='trigger_count' and isinstance(node.target.value,ast.Name) and node.target.value.id=='existing':
            self.counts['prepare_refresh']+=1;return [node,*self.prepare_statements(node,'existing')]
        return node
    def visit_Expr(self,node):
        self.generic_visit(node)
        call=node.value
        if self.stack and self.stack[-1]=='_activate' and isinstance(call,ast.Call) and ast.dump(call.func)==ast.dump(ast.parse('self._active.append',mode='eval').body) and len(call.args)==1 and isinstance(call.args[0],ast.Call) and any(keyword.arg=='trigger_count' for keyword in call.args[0].keywords):
            self.counts['prepare_new']+=1;return [node,*self.prepare_statements(node,'self._active[-1]')]
        if self.stack and self.stack[-1]=='_dispatch_instant' and isinstance(call,ast.Call) and ast.dump(call.func)==ast.dump(ast.parse('self._active.append',mode='eval').body) and len(call.args)==1 and isinstance(call.args[0],ast.Name) and call.args[0].id=='ab_new':
            self.counts['prepare_init']+=1;return [node,*self.prepare_statements(node,'ab_new','target_eff',True)]
        return node

class DispatchPreparation(ActivationPreparation):
    def __init__(self):self.stack=[];self.counts=dict(prepare_new=0,prepare_refresh=0,prepare_init=0)
    def visit_FunctionDef(self,node):
        self.stack.append(node.name);self.generic_visit(node);self.stack.pop();return node
def protection_activation(manager,effect,caster,t,targets,carrier=None):
    return _carrier_event('protection_activate',manager,carrier,effect,caster,t,targets)

def body_heal(manager,name,amount,t):
    CATALOG.emit('before_body_heal',manager,name,amount,t)
    # Quantity/clamp arithmetic belongs to the resource implementation.
    for spec in CATALOG.specs:
        handler=CATALOG.handlers[spec.key]
        if handler.body_clamp:return handler.body_clamp(manager,name,amount,t)
    raise RuntimeError('No body healing implementation registered')

def shared_body_heal(manager,name,amount,t):
    portions=[(name,1)]
    if amount>0:
        for spec in CATALOG.specs:
            plan=CATALOG.handlers[spec.key].heal_plan
            if plan:portions=plan(manager,name,t);break
    total=sum(weight for _,weight in portions)
    for recipient,weight in portions:
        part=amount if len(portions)==1 else amount*weight/total
        manager.state['hp'][recipient]=body_heal(manager,recipient,part,t)
        manager.sync_hp(recipient)

def retire(manager,before,owner=None):
    for spec in CATALOG.specs:
        handler=CATALOG.handlers[spec.key]
        if handler.resource_kind:
            state(manager).retire(manager,handler.resource_kind,before,handler.retain_removed,
                owner if handler.discard_owner_on_down else None)

def collect_inactive(manager):
    runtime=state(manager);active=runtime.active_ids(manager)
    for spec in CATALOG.specs:
        handler=CATALOG.handlers[spec.key]
        if not handler.resource_kind:continue
        resources=runtime.pool(handler.resource_kind)
        for uid,record in list(resources.items()):
            # A bulk expiry removes every carrier before delivering each
            # state-end event. An earlier sibling notification must not erase
            # a retained resource whose own end event has not arrived yet.
            if handler.retain_removed and not (handler.collect_removed and handler.collect_removed(record)):
                continue
            if uid not in active and not (handler.retain_removed and handler.retain_removed(record)):
                del resources[uid]

def install_adapter():
    from calculator import buff_manager,timeline
    bm=buff_manager.BuffManager
    if getattr(bm,'_nikke_lifecycle_runtime',False):return
    CATALOG.seal()
    from reference_rewrite import rewrite_reference
    original_notify=bm.notify
    original_dispatch=rewrite_reference(bm._dispatch_instant,DispatchPreparation(),dict(prepare_new=0,prepare_refresh=0,prepare_init=1),
        compose=getattr(bm._dispatch_instant,'_nikke_reference_code',None) is bm._dispatch_instant.__code__)
    from resource_runtime import prepare_dispatch
    original_dispatch=prepare_dispatch(bm,original_dispatch)
    original_down=bm.knock_down;original_register=timeline._register_instant_handlers
    @wraps(original_notify)
    def notify(self,event,t,caster,*args,**kwargs):
        runtime=state(self)
        packet=kwargs.get('impact')
        if packet is None and 'impact' not in kwargs:
            parent=runtime.event_stack[-1].impact if runtime.event_stack else (runtime.impact_stack[-1] if runtime.impact_stack else None)
            packet=inherited_impact(event,parent)
            if packet is not None:kwargs['impact']=packet
        if packet is not None and not isinstance(packet,Impact):raise TypeError('Expected an Impact event context')
        completion=kwargs.get('completion')
        if completion is not None and not isinstance(completion,CounterCompletion):raise TypeError('Expected a counter completion event context')
        target=packet.target if packet is not None else completion.actor if completion is not None else None
        explicit=kwargs.get('target_context')
        if explicit is not None:
            if not isinstance(explicit,ActorHandle):raise TypeError('Expected a target handle context')
            if target is not None and target!=explicit:raise ValueError('Conflicting event target contexts')
            target=explicit
        if target is None and inherits_target(event) and runtime.event_stack:target=runtime.event_stack[-1].target
        runtime.event_stack.append(EventFrame(event,caster,t,packet,completion,target))
        try:
            CATALOG.emit('before_notify',self,event,t,caster)
            return original_notify(self,event,t,caster,*args,**kwargs)
        finally:
            runtime.event_stack.pop()
            collect_inactive(self)
    @wraps(original_dispatch)
    def dispatch(self,*args,**kwargs):
        before=state(self).active_ids(self)
        try:return original_dispatch(self,*args,**kwargs)
        finally:
            CATALOG.emit('after_dispatch',self,before)
            retire(self,before)
    @wraps(original_down)
    def down(self,*args,**kwargs):
        before=state(self).active_ids(self)
        try:return original_down(self,*args,**kwargs)
        finally:
            name=args[0] if args else kwargs['name']
            CATALOG.emit('after_down',self,before,name)
            retire(self,before,name)
    @wraps(original_register)
    def register(manager,*args,**kwargs):
        result=original_register(manager,*args,**kwargs)
        for spec in CATALOG.specs:
            handler=CATALOG.handlers[spec.key]
            if handler.instant_stat:
                # Default argument binds this handler rather than the loop cell.
                def execute(eff,caster,t,val,callback=handler.instant):
                    return callback(manager,eff,caster,t,val)
                manager.register_instant_handler(handler.instant_stat,execute)
        return result
    bm.effect_runtime_prepare=preparation;bm.effect_runtime_activate=activation;bm.apply_storage_body_heal=body_heal
    bm.effect_runtime_carrier=active_carrier;bm.effect_runtime_protection=protection_activation
    bm.apply_shared_body_heal=shared_body_heal
    bm.notify=notify;bm._dispatch_instant=dispatch;bm.knock_down=down
    timeline._register_instant_handlers=register;bm._nikke_lifecycle_runtime=True
