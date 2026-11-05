"""Independent native weapon sessions: logical identity versus physical entry.

A refresh keeps its session; an ended/replaced mode starts a fresh one. Old
shot callbacks still finish their packet but cannot consume or schedule the new
gun. No observations from this layer are supplied to GPU input preparation.
"""
import ast
from reference_rewrite import rewrite_reference

def token(manager,name):
    return manager.state.get('weapon_change',{}).get(name,{}).get('_nikke_session',0)

def parent_valid(actor,manager):
    return getattr(actor,'_nikke_mode_token',0)==token(manager,actor.name)

def base_capacity(actor):
    if not getattr(actor,'_nikke_mode_physical',False):
        return getattr(actor,'_nikke_base_weapon',actor.weapon)['max_ammo']
    return actor.weapon['max_ammo']

def prepare_frame(actor,manager,t):
    manager.__dict__.setdefault('_nikke_weapon_actors',{})[actor.name]=actor
    actor._nikke_base_weapon=actor.weapon
    if manager.get_weapon_change(actor.name) is None:
        actor._nikke_mode_token=0
        actor._nikke_mode_physical=False

def begin_session(actor,manager,t):
    actor._in_weapon_change=True
    actor._wc_shots=0
    actor._wc_new_session=True
    actor._wc_ammo_full=None
    actor._wc_ammo_restored=False
    actor._nikke_mode_token=token(manager,actor.name)
    actor._nikke_mode_physical=True
    actor._charge_phase='ready';actor._charge_full_t=-1.0
    actor._post_delay_end_t=-1.0;actor._post_reload_end_t=-1.0
    actor._wc_entry_reload_until=-1.0;actor._pending_auto_reload=False
    actor.next_fire_time=t;actor.reloading_until=-1.0
    manager.state.setdefault('charging',{})[actor.name]=False

def record(manager,caster,effect,t,expires):
    prior=manager.state.get('weapon_change',{}).get(caster)
    if prior is not None and prior['effect'] is effect:
        generation=prior['_nikke_session']
    else:
        generation=getattr(manager,'_nikke_weapon_next_session',0)+1
        manager._nikke_weapon_next_session=generation
        actor=getattr(manager,'_nikke_weapon_actors',{}).get(caster)
        if actor is not None:actor._wc_shots=0;actor._wc_ammo_full=None
    return dict(effect=effect,activated_at=t,expires_at=expires,_nikke_session=generation)

def end_session(manager,caster,t):
    actor=getattr(manager,'_nikke_weapon_actors',{}).get(caster)
    if actor is None or not getattr(actor,'_nikke_mode_physical',False):return
    when=manager._cur_t if t is None else t
    # The native round-limit path has already restored this magazine; an end
    # callback may mutate it, so restore exactly once before the notification.
    if not actor._wc_ammo_restored:
        base=getattr(actor,'_nikke_base_weapon',actor.weapon)['max_ammo']
        actor.ammo=actor._buffed_ammo(manager,when,base)
    actor._nikke_mode_physical=False
    actor._wc_shots=0;actor._wc_ammo_full=None;actor._wc_ammo_restored=True
    actor.next_fire_time=when;actor.reloading_until=-1.0
    actor._charge_phase='ready';actor._charge_full_t=-1.0
    actor._post_delay_end_t=-1.0;actor._post_reload_end_t=-1.0
    actor._pending_auto_reload=False
    manager.state.setdefault('charging',{})[caster]=False

class ModeSessionEntry(ast.NodeTransformer):
    def __init__(self):self.counts=dict(regular=0,reload=0,prepare=0)
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        node.body.insert(0,ast.copy_location(ast.parse('self.prepare_weapon_frame(bm,t)').body[0],node.body[0]))
        self.counts['prepare']+=1
        return node
    def visit_If(self,node):
        if ast.dump(node.test)==ast.dump(ast.parse('not self._in_weapon_change',mode='eval').body):
            expected=ast.parse('self._in_weapon_change=True\nself._wc_shots=0\nself._wc_new_session=True\nself._wc_ammo_full=None\nself._wc_ammo_restored=False').body
            if [ast.dump(s) for s in node.body]!=[ast.dump(s) for s in expected]:raise AssertionError('Unexpected regular mode entry')
            self.counts['regular']+=1
            node.test=ast.copy_location(ast.parse('not self._in_weapon_change or not self.weapon_parent_session_valid(bm)',mode='eval').body,node.test)
            node.body=[ast.copy_location(ast.parse('self.begin_weapon_session(bm,t)').body[0],node.body[0])]
        return self.generic_visit(node)
    def visit_Assign(self,node):
        if ast.dump(node)==ast.dump(ast.parse('self._in_weapon_change=True').body[0]):
            self.counts['reload']+=1;return ast.copy_location(ast.parse('self.begin_weapon_session(bm,t)').body[0],node)
        return node

class ModeRecord(ast.NodeTransformer):
    def __init__(self):self.counts=dict(record=0)
    def visit_Assign(self,node):
        if len(node.targets)==1 and ast.dump(node.targets[0])==ast.dump(ast.parse('wc[caster]=None').body[0].targets[0]):
            expected=ast.parse('{"effect":eff,"activated_at":t,"expires_at":expires}',mode='eval').body
            assert ast.dump(node.value)==ast.dump(expected)
            node.value=ast.parse('self.weapon_session_record(caster,eff,t,expires)',mode='eval').body
            self.counts['record']+=1
        return self.generic_visit(node)

class ModeEnd(ast.NodeTransformer):
    def __init__(self):self.counts=dict(end=0)
    def visit_If(self,node):
        if ast.dump(node.test)==ast.dump(ast.parse('info is None',mode='eval').body):
            self.counts['end']+=1
            return [node,ast.copy_location(ast.parse('self.end_weapon_session(caster,t)').body[0],node)]
        return self.generic_visit(node)

class RegisterActors(ast.NodeTransformer):
    def __init__(self):self.counts=dict(register=0)
    def visit_FunctionDef(self,node):
        if node.name=='_register_instant_handlers':
            node.body.insert(0,ast.copy_location(ast.parse('bm._nikke_weapon_actors=char_states').body[0],node.body[0]))
            self.counts['register']+=1
        return node

class BaseCapacity(ast.NodeTransformer):
    def __init__(self):self.counts=dict(base=0)
    def visit_Assign(self,node):
        if ast.dump(node)==ast.dump(ast.parse('base=self.weapon["max_ammo"]').body[0]):
            self.counts['base']+=1
            return ast.copy_location(ast.parse('base=self.weapon_base_capacity()').body[0],node)
        return self.generic_visit(node)

class ParentShot(ast.NodeTransformer):
    def __init__(self,routine):
        self.routine=routine
        self.counts=dict(ammo=0,shots=0,full=0,tail=0,cadence=0,warm=0,start=0,limit=0)
    def visit_AugAssign(self,node):
        if self.routine=='_tick_auto' and ast.dump(node)==ast.dump(ast.parse('self.next_fire_time += inter').body[0]):
            self.counts['cadence']+=1
            guard=ast.parse('if self.weapon_parent_session_valid(bm):\n pass').body[0];guard.body=[node]
            return ast.copy_location(guard,node)
        if isinstance(node.target,ast.Attribute) and node.target.attr in ('ammo','_wc_shots'):
            field=node.target.attr
            assert ast.dump(node.op)==ast.dump(ast.Sub() if field=='ammo' else ast.Add()) and isinstance(node.value,ast.Constant) and node.value.value==1
            self.counts['ammo' if field=='ammo' else 'shots']+=1
            guard=ast.parse('if self.weapon_parent_session_valid(bm):\n pass').body[0];guard.body=[node]
            return ast.copy_location(guard,node)
        return node
    def visit_Expr(self,node):
        text=ast.unparse(node)
        if text=="bm.notify('full_charge', t, self.name)" or self.routine=='_tick_charge' and text=="bm.notify('last_bullet_fire', t, self.name)":
            key='full' if 'full_charge' in text else 'start';self.counts[key]+=1
            return [node,ast.copy_location(ast.parse('if not self.weapon_parent_session_valid(bm):\n return events').body[0],node)]
        return node
    def visit_If(self,node):
        self.generic_visit(node)
        if self.routine=='_tick_auto' and [ast.dump(s) for s in node.body]==[ast.dump(s) for s in ast.parse('self.last_fire_t=t\nself._last_inter=inter').body]:
            assert ast.unparse(node.test)=="self.fire_mode == 'auto_warmup'"
            self.counts['warm']+=1
            return [node,ast.copy_location(ast.parse('if not self.weapon_parent_session_valid(bm):\n break').body[0],node)]
        if self.routine=='_charge_fire' and ast.dump(node.test)==ast.dump(ast.parse('self._tap_this_shot',mode='eval').body):
            self.counts['tail']+=1
            return [ast.copy_location(ast.parse('if not self.weapon_parent_session_valid(bm):\n return events').body[0],node),node]
        if ast.unparse(node.test)=='duration_bullets is not None and self._wc_shots >= duration_bullets':
            node.test=ast.BoolOp(op=ast.And(),values=[node.test,ast.parse('self.weapon_parent_session_valid(bm)',mode='eval').body]);self.counts['limit']+=1
        return node

def install():
    from calculator import timeline
    from calculator.buff_manager import BuffManager
    CharState=timeline.CharState
    if getattr(CharState,'_nikke_mode_session_entry',False):return
    CharState.begin_weapon_session=begin_session
    CharState.prepare_weapon_frame=prepare_frame;CharState.weapon_parent_session_valid=parent_valid
    CharState.weapon_base_capacity=base_capacity
    BuffManager.weapon_session_record=record;BuffManager.end_weapon_session=end_session
    BuffManager._activate=rewrite_reference(BuffManager._activate,ModeRecord(),dict(record=1),compose=True)
    BuffManager.end_weapon_change=rewrite_reference(BuffManager.end_weapon_change,ModeEnd(),dict(end=1))
    timeline._register_instant_handlers=rewrite_reference(timeline._register_instant_handlers,RegisterActors(),dict(register=1),compose=True)
    CharState.tick=rewrite_reference(CharState.tick,ModeSessionEntry(),dict(regular=1,reload=1,prepare=1))
    CharState._buffed_ammo=rewrite_reference(CharState._buffed_ammo,BaseCapacity(),dict(base=1))
    zero=dict(ammo=0,shots=0,full=0,tail=0,cadence=0,warm=0,start=0,limit=0)
    for name,expected in [('_fire',dict(ammo=1,shots=1)),('_charge_fire',dict(ammo=1,shots=1,full=1,tail=1)),('_tick_auto',dict(cadence=1,warm=1)),('_tick_charge',dict(start=1)),('_tick_weapon_change',dict(limit=1))]:
        transform=ParentShot(name)
        setattr(CharState,name,rewrite_reference(getattr(CharState,name),transform,{**zero,**expected}))
    CharState._nikke_mode_session_entry=True
