"""Opt-in original-carrier allocation at the existing native landing boundary.

This declared model freezes all live body recipients, then lands their shares
through the original protection/HP executor in squad order. A separate caster
cover share lands last, in the same original cover mutation helper. Excess cover
damage is discarded; callbacks cannot renormalize this already frozen packet.
No default admission, game constants, second clock or parallel HP state.
"""
import ast,copy,math
from contextlib import contextmanager
from unittest.mock import patch
from incoming_weighted_allocation import allocate
from reference_rewrite import rewrite_reference

SPLIT='''group = bm.split_group(name, t)
if group:
    share = dmg / len(group)
    for member in group:
        _land_squad(member, share, hit, t, notify_hit=(member == name))
else:
    _land_squad(name, dmg, hit, t, notify_hit=True)
'''
COVER='''cover = min(state['cover_hp'][name], dmg)
state['cover_hp'][name] -= cover
if state['cover_hp'][name] <= 0.0:
    bm.break_cover(name)
    boss.log_squad(t, hit.pattern, 'cover_break', name)
'''
WEIGHTED='''_weighted = _nikke_weighted_snapshot(bm, name, dmg, t, state['cover_hp'])
if _weighted is not None:
    for _member, _share in _weighted['bodies']:
        _land_squad(_member, _share, hit, t, notify_hit=(_member == name))
    if _weighted['cover'] is not None:
        _owner, _share = _weighted['cover']
        _before = state['cover_hp'][_owner]
        _applied = 0.0
        _delivered = not bm.is_down(_owner) and _before > 0.0
        if _delivered:
            _applied = _apply_weighted_cover(_owner, _share, hit, t)
        _after = state['cover_hp'][_owner]
        if _applied:
            bm.notify('event:cover_hit', t, _owner)
        _nikke_weighted_cover_receipt(_weighted, t, _before, _applied, _after, _delivered)
else:
    pass
'''


def _tree(statements):return ast.dump(ast.Module(body=statements,type_ignores=[]))


class WeightedLanding(ast.NodeTransformer):
    def __init__(self):self.counts=dict(split=0,cover=0,helper=0)
    def visit_FunctionDef(self,node):
        if node.name=='_boss_attack':
            expected=ast.parse(SPLIT).body
            for child in ast.walk(node):
                if not isinstance(child,(ast.For,ast.If)):continue
                for i in range(len(child.body)-1):
                    if _tree(child.body[i:i+2])!=_tree(expected):continue
                    replacement=ast.parse(WEIGHTED).body
                    replacement[-1].orelse=copy.deepcopy(expected)
                    child.body[i:i+2]=replacement;self.counts['split']+=1;break
            return node
        if node.name=='_land_squad':
            expected=ast.parse(COVER).body
            for child in ast.walk(node):
                if isinstance(child,ast.If) and _tree(child.body)==_tree(expected):
                    self.cover_body=copy.deepcopy(child.body)
                    child.body=ast.parse('cover = _apply_weighted_cover(name, dmg, hit, t)').body
                    self.counts['cover']+=1
            return node
        self.generic_visit(node)
        if node.name=='simulate':
            if not hasattr(self,'cover_body'):raise ValueError('Original cover mutation anchor changed')
            helper=ast.parse('def _apply_weighted_cover(name, dmg, hit, t):\n    pass').body[0]
            helper.body=self.cover_body+[ast.Return(value=ast.Name(id='cover',ctx=ast.Load()))]
            node.body.insert(next(i for i,n in enumerate(node.body) if isinstance(n,ast.FunctionDef) and n.name=='_boss_attack'),helper)
            self.counts['helper']+=1
        return node


class WeightedIncoming:
    def __init__(self,spec,names):
        if type(names) not in (list,tuple) or len(names)!=5 or len(set(names))!=5 or any(type(n) is not str or not n for n in names):raise ValueError('Five original distinct body owners required')
        if type(spec) is not dict or set(spec)!={'policy','caster_weight','other_weight','cover_weight'} or spec['policy']!='declared-weighted-incoming-v1':raise ValueError('Explicit weighted incoming policy and three weights required')
        allocate(0.,31,0,spec['caster_weight'],spec['other_weight'],spec['cover_weight'],False)
        self.names=list(names);self.weights=[spec[k] for k in ('caster_weight','other_weight','cover_weight')];self.manager=None
        self.data=dict(policy=spec['policy'],weights=list(self.weights),snapshots=[],cover_receipts=[],in_game_rules_verified=False)

    def snapshot(self,manager,struck,amount,t,cover_hp):
        if manager.squad_names!=self.names or struck not in self.names:raise ValueError('Weighted original roster mismatch')
        if self.manager is None:self.manager=manager
        elif self.manager is not manager:raise ValueError('One original manager per weighted model')
        if type(t) not in (int,float) or not math.isfinite(t):raise ValueError('Finite existing battle time required')
        markers=list(manager._by_stat('received_dmg_split'))
        for ab in markers:
            if ab.effect.get('target') not in ('all_allies','self_cover') or ab.effect.get('trigger',{}).get('condition',[]) or ab.effect.get('duration_bullets',-1)!=-1:
                raise ValueError('Unsupported weighted carrier target/condition/bullet lifetime')
        bodies=[a for a in markers if a.effect['target']=='all_allies' and manager._live(a,struck,t)]
        if not bodies:return None
        if len(bodies)!=1:raise ValueError('Overlapping weighted body carriers need an explicit policy')
        body=bodies[0];caster=body.caster
        if caster not in self.names:raise ValueError('Original weighted caster required')
        if manager.split_group(struck,t):raise ValueError('Even and weighted overlap needs an explicit policy')
        mask=sum(1<<i for i,n in enumerate(self.names) if not manager.is_down(n) and manager._live(body,n,t))
        covers=[a for a in markers if a.effect['target']=='self_cover' and a.caster==caster and t<a.expires_at and a.stack>0]
        if len(covers)>1:raise ValueError('Overlapping cover carriers need an explicit policy')
        cover=bool(covers) and not manager.is_down(caster) and cover_hp[caster]>0.0
        result=allocate(amount,mask,self.names.index(caster),*self.weights,cover)
        if result['status']!=0:raise OverflowError('Weighted incoming denominator overflow')
        plan=dict(index=len(self.data['snapshots']),time=t,struck=struck,caster=caster,body_mask=mask,
            body_source_name=body.effect['name'],body_source_activated_at=body.activated_at,
            cover_source_name=covers[0].effect['name'] if cover else None,amount=amount,**result)
        self.data['snapshots'].append(plan)
        return dict(index=plan['index'],bodies=[(n,result['shares'][i]) for i,n in enumerate(self.names) if mask&(1<<i)],cover=(caster,result['shares'][5]) if cover else None)

    def cover_receipt(self,plan,t,before,applied,after,delivered):
        self.data['cover_receipts'].append(dict(snapshot=plan['index'],time=t,hp_before=before,applied=applied,hp_after=after,delivered=delivered))


@contextmanager
def weighted_incoming(spec,names):
    from calculator import timeline
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Original simulation aliases differ')
    original=timeline.simulate;runtime=WeightedIncoming(spec,names)
    if '_nikke_weighted_snapshot' in original.__globals__:raise ValueError('Weighted model already installed')
    rewritten=rewrite_reference(original,WeightedLanding(),dict(split=1,cover=1,helper=1),compose=True)
    with patch.dict(original.__globals__,{'_nikke_weighted_snapshot':runtime.snapshot,'_nikke_weighted_cover_receipt':runtime.cover_receipt}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):yield runtime.data
