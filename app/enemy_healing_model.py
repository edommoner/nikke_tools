"""Declared source-node healing of existing finite ADD health, CPU contract.

The source scheduler, ADD dealt/hit/death state, recipient generations and
heal-received multiplier are existing implementations. No second HP pool or
clock is introduced. This module does not admit any GPU input.
"""
import ast,math
from contextlib import contextmanager
from unittest.mock import patch
from impact_specs import ActorKind
from portable_geometry_specs import number
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for
from world_actor_specs import bindings

def normalize(spec):
    if type(spec) is not list or not 1<=len(spec)<=32:raise ValueError('One to32 explicit healing source nodes required')
    rows=[];nodes=set()
    for row in spec:
        if type(row) is not dict or set(row)!={'node','targets','amount'}:raise ValueError('Literal healing source, targets and amount required')
        node=row['node'];targets=row['targets']
        if type(node) is not str or not node or node in nodes:raise ValueError('Unique healing source node required')
        if type(targets) is not list or not 1<=len(targets)<=127 or any(type(t) is not str or not t for t in targets) or len(set(targets))!=len(targets):raise ValueError('Distinct configured ADD target labels required')
        amount=float(number(row['amount'],nonnegative=True));nodes.add(node)
        rows.append(dict(node=node,targets=list(targets),amount=amount))
    return rows

def multiplier(manager,label,t,fields=None):
    """Existing scalar formula, with existing generation-aware field visibility."""
    original=manager._live;excluded=[]
    def live(carrier,name,when):
        active=original(carrier,name,when)
        if name!=label or not active:return active
        visible=manager.enemy_field_visible(carrier,name)
        key=getattr(carrier,'enemy_recipient_key',None);actor=key.actor_for(name) if key is not None else None
        row=dict(name=carrier.effect['name'],actor=[int(actor.kind),actor.identity,actor.generation] if actor is not None else None,expires_at=carrier.expires_at)
        if fields is not None:fields.append(dict(row,visible=visible))
        if not visible:
            excluded.append(row)
        return visible
    with patch.object(manager,'_live',live):value=manager.heal_received_mult(label,t)
    if not math.isfinite(value) or value<0:raise ValueError('Finite nonnegative enemy healing multiplier required')
    return value,excluded

class HealingFrame(ast.NodeTransformer):
    def __init__(self):self.counts=dict(frame=0,result=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and ast.unparse(node.func)=='boss.begin_frame':
            if len(node.args)!=2 or node.keywords:raise ValueError('World source frame boundary changed')
            result=ast.parse('_nikke_enemy_healing_frame(bm,boss,None,None)',mode='eval').body
            result.args[2:]=node.args;self.counts['frame']+=1;return ast.copy_location(result,node)
        return node
    def visit_Return(self,node):
        if isinstance(node.value,ast.Name) and node.value.id=='result':
            self.counts['result']+=1
            return ast.copy_location(ast.Return(ast.Call(func=ast.Name(id='_nikke_enemy_healing_result',ctx=ast.Load()),args=[node.value],keywords=[])),node)
        return self.generic_visit(node)

class EnemyHealing:
    def __init__(self,spec):
        self.spec=normalize(spec);self.boss=None;self.manager=None;self.seen={};self.bound={};self.data=dict(receipts=[],sources=[])

    def bind(self,manager,boss):
        configured={b.label:b for b in bindings([run.p for run in boss._runs])}
        if len(boss._runs)>32 or len(configured)>128:raise ValueError('Common world node/actor capacity exceeded')
        nodes={run.p.id:run for run in boss._runs}
        for row in self.spec:
            if row['node'] not in nodes or nodes[row['node']].p.kind!='idle':raise ValueError('Healing source must name an existing idle world node')
            for label in row['targets']:
                b=configured.get(label)
                if b is None or b.kind!=ActorKind.ADD:raise ValueError('Healing requires an actual configured ADD, never BODY/PART')
                spec=boss._runs[b.run].p.summon
                if spec.hp is None or not math.isfinite(spec.hp) or spec.hp<=0 or spec.hit_hp or spec.hit_hp_after:raise ValueError('Healing requires finite damage-owned ADD health')
                self.bound[label]=b
        self.boss=boss;self.manager=manager

    def result(self,result):
        self.data['public_summary']=dict(add_char_total=dict(result.add_char_total),add_total=result.add_total,add_overkill=result.add_overkill)
        return result

    def frame(self,manager,boss,t,enemy):
        if self.boss is None:self.bind(manager,boss)
        if self.boss is not boss or self.manager is not manager:raise ValueError('One source world per enemy healing scope')
        events=boss.begin_frame(t,enemy);registry=registry_for(manager,boss)
        for rule in self.spec:
            source=boss._run_by_id[rule['node']];previous=self.seen.get(rule['node'],0)
            if source.opens==previous:continue
            if not source.active or source.opens!=previous+1:raise ValueError('Unobserved healing source generation')
            self.seen[rule['node']]=source.opens
            self.data['sources'].append(dict(node=rule['node'],generation=source.opens,time=t))
            for label in rule['targets']:
                binding=self.bound[label];run=boss._runs[binding.run]
                record=dict(node=rule['node'],source_generation=source.opens,time=t,target=label,base_amount=rule['amount'],actor=None,status='not-spawned')
                if len(self.data['receipts'])>=1024:raise ValueError('Enemy healing receipt capacity exceeded; no history truncation')
                self.data['receipts'].append(record)
                if run.opens==0:continue
                snapshot=registry.view(ActorKind.ADD,label);record['actor']=[5,snapshot.handle.identity,snapshot.handle.generation]
                if not snapshot.alive:record['status']='dead-or-inactive';continue
                add=run.adds[binding.slot];before=add.dealt;hits=add.hits;score=dict(boss.add_dealt)
                fields=[];value,excluded=multiplier(manager,label,t,fields);requested=rule['amount']*value
                if not math.isfinite(requested):raise ValueError('Enemy healing amount overflow')
                applied=min(requested,before);add.dealt=before-applied
                record.update(status='healed',max_hp=add.spec.hp,multiplier=value,requested=requested,
                    dealt_before=before,dealt_after=add.dealt,applied=applied,effective_gain=before-add.dealt,
                    hits_before=hits,hits_after=add.hits,scored_before=score,scored_after=dict(boss.add_dealt),
                    hp_before=add.spec.hp-before,hp_after=add.spec.hp-add.dealt,excluded_stale_fields=excluded,quantity_fields=fields)
        return events

@contextmanager
def enemy_healing(spec):
    from calculator import timeline
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    original=timeline.simulate;runtime=EnemyHealing(spec)
    rewritten=rewrite_reference(original,HealingFrame(),dict(frame=2,result=1),compose=True)
    with patch.dict(original.__globals__,{'_nikke_enemy_healing_frame':runtime.frame,'_nikke_enemy_healing_result':runtime.result}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):
        try:yield runtime.data
        finally:
            if runtime.boss is not None:
                runtime.data['final_scored_damage']=dict(runtime.boss.add_dealt)
                runtime.data['final_overkill']=runtime.boss.add_overkill
                runtime.data['final_adds']=[]
                for binding in bindings([run.p for run in runtime.boss._runs]):
                    if binding.kind!=ActorKind.ADD:continue
                    run=runtime.boss._runs[binding.run]
                    if run.opens==0:
                        runtime.data['final_adds'].append(dict(label=binding.label,generation=0));continue
                    add=run.adds[binding.slot]
                    runtime.data['final_adds'].append(dict(label=binding.label,generation=run.opens,
                        alive=bool(run.active and add.alive),gone=add.gone,dealt=add.dealt,
                        hits=add.hits,born=add.spawn_t,order=add.order))
