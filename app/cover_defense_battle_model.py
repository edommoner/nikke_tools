"""Opt-in cover quantity at the existing native landing boundary.

Body/shield/decoy damage and all callbacks stay in the original executor. The
original attack/received scalar snapshot is passed as locals, including through
equal sharing; cover DEF is read after shield callbacks at the actual cover phase.
This is a declared model, not a game level curve or default admission.
"""
import ast,math
from contextlib import contextmanager
from unittest.mock import patch
from cover_defense_model import incoming_damage,live_defense
from reference_rewrite import rewrite_reference

LAND_PREFIX="""spec = hit.spec
if bm.is_down(name):
    return
cs = char_states[name]
covered = cs.in_cover(t) and state['cover_hp'][name] > 0.0 and not cs.cover_blocked(t, bm)
shield = bm.absorb_shield(name, dmg, t, pierce=spec.pierce)
cover = 0.0
if spec.pierce or shield <= 0.0:
    if covered:
        cover = min(state['cover_hp'][name], dmg)
        state['cover_hp'][name] -= cover
        if state['cover_hp'][name] <= 0.0:
            bm.break_cover(name)
            boss.log_squad(t, hit.pattern, 'cover_break', name)
"""

def normalize(spec,names):
    if type(names) not in (list,tuple) or len(names)!=5 or any(type(n) is not str or not n for n in names) or len(set(names))!=5:raise ValueError('Five distinct original cover owners required')
    if type(spec) is not list or len(spec)!=5:raise ValueError('Five explicit independent cover base quantities required')
    result={}
    for row in spec:
        if type(row) is not dict or set(row)!={'name','base_defense'}:raise ValueError('Explicit cover owner and base_defense required')
        name=row['name'];base=row['base_defense']
        if type(name) is not str or name not in names or name in result or type(base) not in (int,float) or not math.isfinite(base) or not 0<=base<=1e30:raise ValueError('Unique original cover owner and finite bounded base required')
        result[name]=float(base)
    if set(result)!=set(names):raise ValueError('Cover declaration must retain the actual original roster')
    return result

class CoverLanding(ast.NodeTransformer):
    def __init__(self):self.function=None;self.counts=dict(bind=0,percent=0,land=0,signature=0,cover=0)
    def visit_FunctionDef(self,node):
        previous=self.function;self.function=node.name
        if node.name=='_boss_attack':
            offset=1 if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str) else 0
            node.body.insert(offset,ast.parse('_nikke_cover_bind(bm)').body[0]);self.counts['bind']+=1
        if node.name=='_land_squad':
            if [a.arg for a in node.args.args]!=['name','dmg','hit','t'] or [a.arg for a in node.args.kwonlyargs]!=['notify_hit'] or node.args.kw_defaults!=[None]:raise ValueError('Native layered landing signature changed')
            expected=ast.parse(LAND_PREFIX).body
            actual=node.body[1:1+len(expected)]
            if ast.dump(ast.Module(body=actual,type_ignores=[]))!=ast.dump(ast.Module(body=expected,type_ignores=[])):raise ValueError('Native shield/cover phase or mutation anchor changed')
            for name in ('cover_attack','cover_coefficient','cover_received','cover_divisor'):
                node.args.kwonlyargs.append(ast.arg(arg=name));node.args.kw_defaults.append(None)
            self.counts['signature']+=1
        result=self.generic_visit(node);self.function=previous;return result
    def visit_Call(self,node):
        self.generic_visit(node)
        if self.function=='_boss_attack' and ast.unparse(node.func)=='bm.incoming_dmg_pct':
            if [ast.unparse(a) for a in node.args]!=['name','t'] or node.keywords:raise ValueError('Original received quantity query changed')
            self.counts['percent']+=1
            return ast.copy_location(ast.NamedExpr(target=ast.Name(id='_nikke_cover_received',ctx=ast.Store()),value=node),node)
        if self.function=='_boss_attack' and isinstance(node.func,ast.Name) and node.func.id=='_land_squad':
            actual=[ast.unparse(a) for a in node.args]
            if actual not in (['name','dmg','hit','t'],['member','share','hit','t']) or len(node.keywords)!=1 or node.keywords[0].arg!='notify_hit':raise ValueError('Native damage-sharing landing changed')
            divisor=ast.parse('len(group)' if actual[0]=='member' else '1',mode='eval').body
            node.keywords.extend([ast.keyword(arg='cover_attack',value=ast.Name(id='atk',ctx=ast.Load())),ast.keyword(arg='cover_coefficient',value=ast.parse('spec.coeff',mode='eval').body),ast.keyword(arg='cover_received',value=ast.Name(id='_nikke_cover_received',ctx=ast.Load())),ast.keyword(arg='cover_divisor',value=divisor)])
            self.counts['land']+=1;return node
        if self.function=='_land_squad' and isinstance(node.func,ast.Name) and node.func.id=='min' and [ast.unparse(a) for a in node.args]==["state['cover_hp'][name]",'dmg'] and not node.keywords:
            self.counts['cover']+=1
            return ast.copy_location(ast.parse("_nikke_cover_layer(bm,name,t,cover_attack,cover_coefficient,cover_received,cover_divisor,state['cover_hp'][name])",mode='eval').body,node)
        return node

class CoverDefense:
    def __init__(self,spec,names):
        self.names=list(names);self.bases=normalize(spec,names);self.manager=None
        self.data=dict(policy='declared-independent-cover-defense-v1',base_defenses=[self.bases[n] for n in names],receipts=[])
    def bind(self,manager):
        if manager.squad_names!=self.names:raise ValueError('Cover model original roster mismatch')
        if self.manager is None:self.manager=manager
        elif self.manager is not manager:raise ValueError('One original battle manager per cover model')
    def layer(self,manager,name,t,attack,coefficient,received,divisor,hp):
        self.bind(manager)
        if name not in self.bases or type(divisor) is not int or not 1<=divisor<=5:raise ValueError('Existing live owner and sharing divisor required')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (t,attack,coefficient,received,hp)) or min(t,attack,coefficient)<0 or hp<=0:raise ValueError('Finite snapshot and positive live cover HP required')
        base=self.bases[name];defense=live_defense(manager,name,t,base)
        quantity=incoming_damage(attack,coefficient,defense,received);shared=quantity/divisor
        if not math.isfinite(shared):raise ValueError('Nonfinite declared cover damage')
        applied=min(hp,shared)
        self.data['receipts'].append(dict(name=name,time=t,attack=attack,coefficient=coefficient,received_snapshot=received,divisor=divisor,base_defense=base,effective_defense=defense,quantity=quantity,shared_quantity=shared,hp_before=hp,applied=applied,hp_after=hp-applied))
        return applied

@contextmanager
def cover_defense(spec,names):
    from calculator import timeline
    from runner import sim
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    original=timeline.simulate;runtime=CoverDefense(spec,names)
    if '_nikke_cover_layer' in original.__globals__:raise ValueError('Cover model already installed')
    rewritten=rewrite_reference(original,CoverLanding(),dict(bind=1,percent=1,land=2,signature=1,cover=1),compose=True)
    with patch.dict(original.__globals__,{'_nikke_cover_bind':runtime.bind,'_nikke_cover_layer':runtime.layer}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):yield runtime.data
