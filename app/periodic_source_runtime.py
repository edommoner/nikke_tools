"""Shared owned periodic resources; callbacks may atomically replace a generation."""
import ast,math
from dataclasses import dataclass
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,state
from periodic_source_specs import specification,MAX_SOURCES,LEGACY_WARNING
from reference_rewrite import rewrite_reference

@dataclass
class PeriodicSource:
    caster:str
    spec:object
    expiry:tuple
    next_at:float|None
    epoch:int
    def count(self,t):return sum(end>t for end in self.expiry)

def refresh(manager,effect,caster,t,value=0):
    spec=specification(effect);resources=pool(manager,'periodic_sources');key=(caster,spec.name)
    if key not in resources and len(resources)>=MAX_SOURCES:raise ValueError('Periodic source capacity exceeded')
    epoch=resources[key].epoch+1 if key in resources else 1
    resources[key]=PeriodicSource(caster,spec,tuple(math.inf if d<0 else t+d for d in spec.lifetimes),t+spec.interval(len(spec.lifetimes)),epoch)

def tick(manager,t):
    resources=pool(manager,'periodic_sources')
    # Preserve owner insertion order, then resource insertion order. Snapshot keys
    # prevents new child-created resources from joining an in-progress phase.
    keys=tuple(resources);owners=tuple(dict.fromkeys(owner for owner,_ in keys))
    for owner in owners:
        for key in keys:
            if key[0]!=owner:continue
            record=resources[key];due=record.next_at
            if due is None or t<due:continue
            count=record.count(t)
            if not count:record.next_at=None;continue
            manager.notify('feather_tick' if record.spec.legacy else 'source_tick:'+record.spec.name,t,owner)
            if resources.get(key) is record:record.next_at=due+record.spec.interval(count)

def count(manager,caster,name,t):
    record=pool(manager,'periodic_sources').get((caster,name))
    return None if record is None else record.count(t)

class SourceRewrite(ast.NodeTransformer):
    def __init__(self):self.counts={'dispatch':0,'clock':0,'lookup':0}
    def visit_If(self,node):
        if ast.dump(node.test)==ast.dump(ast.parse('stat == "feather_refresh"',mode='eval').body):
            self.counts['dispatch']+=1;return None
        if isinstance(node.test,ast.Name) and node.test.id=='feathers':
            self.counts['clock']+=1;return ast.copy_location(ast.parse('self.tick_periodic_sources(t)').body[0],node)
        if ast.dump(node.test)==ast.dump(ast.parse('ref in feathers',mode='eval').body):
            self.counts['lookup']+=1
            return ast.copy_location(ast.parse('if (source_count := self.periodic_source_count(caster,ref,self._cur_t)) is not None:\n return source_count').body[0],node)
        return self.generic_visit(node)

def install():
    if 'periodic_sources' in CATALOG.handlers:return
    from calculator.buff_manager import BuffManager
    # The tick method already carries HP/lifecycle rewrites; retain those edits.
    for name,expected in (('_dispatch_instant',dict(dispatch=1,clock=0,lookup=0)),('tick',dict(dispatch=0,clock=1,lookup=0)),('ref_count',dict(dispatch=0,clock=0,lookup=1))):
        fn=getattr(BuffManager,name)
        fn=rewrite_reference(fn,SourceRewrite(),expected,compose=getattr(fn,'_nikke_reference_code',None) is fn.__code__)
        setattr(BuffManager,name,fn)
    BuffManager.tick_periodic_sources=tick;BuffManager.periodic_source_count=count
    original_reset=BuffManager.reset
    @wraps(original_reset)
    def reset(self,*args,**kwargs):
        result=original_reset(self,*args,**kwargs);pool(self,'periodic_sources').clear();return result
    BuffManager.reset=reset
    original_register=BuffManager._register_all
    @wraps(original_register)
    def register(self,*args,**kwargs):
        result=original_register(self,*args,**kwargs);descriptors=[(specification(e),owner) for e,owner in self._effects]
        if len({(owner,s.name) for s,owner in descriptors if s})>MAX_SOURCES:raise ValueError('Periodic source capacity exceeded')
        if any(s and s.legacy for s,_ in descriptors):state(self).model_warnings.append(LEGACY_WARNING)
        return result
    BuffManager._register_all=register
    CATALOG.register('periodic_sources',Handler(instant_stat='periodic_source_refresh',instant=refresh))
    CATALOG.register('periodic_source_legacy_adapter',Handler(instant_stat='feather_refresh',instant=refresh))
