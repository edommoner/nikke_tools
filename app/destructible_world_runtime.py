"""Declared typed-target lifecycle on the existing BossScript graph clock.

The clock projection owns no damage/geometry. This is a private world adapter;
it does not enable canonical all_projectiles or shield-factor battle admission.
"""
import copy,math
from dataclasses import dataclass
from destructible_target_state import DestructibleTargets,KINDS
from impact_specs import ActorHandle,ActorKind,Impact
from world_actor_runtime import ActorRegistry

@dataclass(frozen=True)
class Binding:
    node:int
    handle:ActorHandle
    capacity:float
    owner:ActorHandle|None=None
    label:str=''

def compile_bindings(nodes,bindings):
    from calculator.boss_pattern import validate
    if not isinstance(nodes,list) or not 1<=len(nodes)<=32 or not isinstance(bindings,list) or not 1<=len(bindings)<=128:raise ValueError('Invalid destructible world capacity')
    names={n['id']:i for i,n in enumerate(nodes)}
    if len(names)!=len(nodes):raise ValueError('Duplicate destructible clock node')
    rows=[];validation=DestructibleTargets(len(bindings))
    for slot,b in enumerate(bindings):
        if set(b)-{'node','kind','identity','capacity','owner','label'} or b.get('node') not in names:raise ValueError('Unknown destructible binding field/node')
        h=ActorHandle(b['kind'],b['identity']);owner=None if b.get('owner') is None else ActorHandle(*b['owner'])
        validation.spawn(slot,h,b['capacity'],owner=owner)
        label=b.get('label','destructible:'+str(int(h.kind))+':'+str(h.identity))
        if not isinstance(label,str) or not label:raise ValueError('Invalid destructible label')
        rows.append(Binding(names[b['node']],h,float(b['capacity']),owner,label))
    if len({r.label for r in rows})!=len(rows):raise ValueError('Duplicate destructible label')
    patterns=[]
    for n in nodes:
        if set(n)-{'id','after','delay','until','repeat'}:raise ValueError('Clock node has unmodelled fields')
        p=copy.deepcopy(n);clear=p.get('until',{}).get('targets_cleared',False)
        p['kind']='parts' if clear else 'idle'
        if clear:
            if not any(r.node==names[n['id']] for r in rows):raise ValueError('Cleared node requires a typed target')
            # One aggregate target expresses the graph's cleared boolean only.
            # Typed target HP/credit/lifecycle remain in DestructibleTargets.
            p['targets']=[dict(name='clock-clear:'+n['id'],hp=1)]
        patterns.append(p)
    parsed=validate(copy.deepcopy(patterns),squad_size=5)
    return patterns,parsed,tuple(rows)

class DestructibleWorld:
    def __init__(self,nodes,bindings,registry=None):
        from calculator.boss_pattern import BossScript
        self.patterns,parsed,self.bindings=compile_bindings(nodes,bindings)
        self.enemy={'def':0,'core_px':0,'patterns':copy.deepcopy(self.patterns)}
        self.clock=BossScript(parsed,self.enemy,lambda *_:False)
        self._setup(self.bindings,registry);self.attached=False
    def _setup(self,bindings,registry):
        self.bindings=bindings
        self.targets=DestructibleTargets(len(self.bindings));self.registry=registry or ActorRegistry()
        self.last=None;self.finished=False
        for slot,b in enumerate(self.bindings):
            def provider(slot=slot,b=b):
                r=self.targets.rows[slot]
                return (0,False,b.owner) if r is None else (r.handle.generation,r.alive,r.owner)
            self.registry.bind(b.handle.kind,b.label,provider,identity=b.handle.identity)
    @classmethod
    def from_clock(cls,clock,bindings,registry=None):
        """Attach quantities to an existing battle clock; create no scheduler."""
        _,_,rows=compile_bindings([dict(id=r.p.id) for r in clock._runs],bindings)
        if any(clock._runs[b.node].p.until_cleared for b in rows):
            raise ValueError('Attached typed bindings require a node without canonical target-cleared semantics')
        self=cls.__new__(cls);self.clock=clock;self.enemy=clock._enemy;self.patterns=None
        self._setup(rows,registry);self.attached=True
        return self
    def synchronize(self,t,*,finished=False):
        if not self.attached or self.finished:raise ValueError('Active attached battle clock required')
        self.targets.advance(t);self.last=float(t);self._sync();self.finished=bool(finished)
    def _sync(self):
        for slot,b in enumerate(self.bindings):
            run=self.clock._runs[b.node];old=self.targets.rows[slot]
            if run.opens==0:continue
            if old is not None and (not run.active or old.handle.generation!=run.opens):self.targets.retire(slot,old.handle)
            if run.active and (old is None or old.handle.generation!=run.opens):
                self.targets.spawn(slot,ActorHandle(b.handle.kind,b.handle.identity,run.opens),b.capacity,owner=b.owner)
    def advance(self,t):
        if self.attached:raise ValueError('The owning battle advances an attached clock')
        if self.finished:raise ValueError('Destructible world already finished')
        self.targets.advance(t)
        if self.last==t:return False
        for run in self.clock._runs:
            rows=[self.targets.rows[i] for i,b in enumerate(self.bindings) if b.node==run.p.idx]
            if run.active and run.p.until_cleared and rows and all(r is not None and r.handle.generation==run.opens and not r.alive for r in rows):
                for target in run.targets:target.destroyed=True
        self.clock.begin_frame(float(t),self.enemy);self.last=float(t);self._sync();return True
    def hit(self,slot,impact):
        if self.last is None or self.finished:raise ValueError('Target landing requires an active world frame')
        result=self.targets.hit(slot,impact);notice=None
        if result['broken']:
            r=self.targets.rows[slot];notice=dict(handle=[int(r.handle.kind),r.handle.identity,r.handle.generation],owner=None if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation],time=self.last)
        return dict(result,notice=notice)
    def finish(self,t):
        if self.attached:raise ValueError('The owning battle finishes an attached clock')
        if self.finished:raise ValueError('Destructible world already finished')
        self.targets.advance(t);self.clock.finish(t);self._sync();self.last=float(t);self.finished=True
