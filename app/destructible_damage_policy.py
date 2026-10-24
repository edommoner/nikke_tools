"""Opt-in v1 scalar contract for declared projectile/HP-shield damage.

This is an explicit design extension, not a canonical/gameplay specification.
Keep all seven native factors and rounding; append the target-kind contribution
inside factor5 before its multiplication. No global installation or admission.
"""
import math,types
from impact_specs import ActorKind,enum_value

MODIFIERS=('projectile_dmg_pct','shield_dmg_pct')
KIND_KEY='_declared_destructible_kind_v1'

def _clone(fn,globals,closure=None):
    result=types.FunctionType(fn.__code__,globals,fn.__name__,fn.__defaults__,fn.__closure__ if closure is None else closure)
    result.__kwdefaults__=fn.__kwdefaults__
    return result

def manager_type(base):
    """Local subclass: ordinary carrier lifetime/query math, two extra stats.

    Clone only the dictionary namespace of the two numeric readers. Mutable
    module maps, base class methods and existing managers remain untouched.
    Instantiate this class before any query; do not change a live manager class.
    """
    from calculator.buff_manager import BuffManager
    if not issubclass(base,BuffManager) or base.get_buffs is not BuffManager.get_buffs or base._plan_step is not BuffManager._plan_step:
        raise ValueError('Declared modifier queries require unwrapped native numeric readers')
    def reader(fn):
        wrapped=getattr(fn,'__wrapped__',None)
        if wrapped is not None:
            cells=fn.__closure__ or ()
            if sum(cell.cell_contents is wrapped for cell in cells)!=1:
                raise ValueError('Unreviewed native query wrapper closure')
            child=reader(wrapped)
            # Preserve the installed enemy generation/query-context wrapper;
            # replace only its immutable reference to the numeric reader.
            return _clone(fn,fn.__globals__,tuple(types.CellType(child) if cell.cell_contents is wrapped else cell for cell in cells))
        scope=dict(fn.__globals__)
        if '_STAT_TO_BUFF' not in scope or '_BUFFS_ZERO' not in scope:
            raise ValueError('Unreviewed native numeric reader namespace')
        if any(k in scope['_STAT_TO_BUFF'] or k in scope['_BUFFS_ZERO'] for k in MODIFIERS):
            raise ValueError('Native modifier consumer changed; re-audit v1 contract')
        scope['_STAT_TO_BUFF']=dict(scope['_STAT_TO_BUFF'],**{k:k for k in MODIFIERS})
        scope['_BUFFS_ZERO']=dict(scope['_BUFFS_ZERO'],**{k:0. for k in MODIFIERS})
        return _clone(fn,scope)
    methods={name:reader(getattr(base,name)) for name in ('get_buffs','_plan_step')}
    methods['_declared_destructible_modifier_model']='v1'
    return type('DeclaredDestructibleModifiers',(base,),methods)

def resolve(manager,attacker,*,kind,base_attack,weapon,defense,coefficient,when,full_burst=False,exclude_names=frozenset()):
    from calculator import damage
    kind=enum_value(ActorKind,kind)
    if kind not in (ActorKind.BODY,ActorKind.PROJECTILE,ActorKind.HP_SHIELD):
        raise ValueError('Declared scalar query supports body, projectile or HP shield; hit shields consume credit')
    if getattr(manager,'_declared_destructible_modifier_model',None)!='v1':raise ValueError('Explicit declared modifier manager required')
    if attacker not in manager.squad_names or type(full_burst) is not bool or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (base_attack,defense,coefficient,when)):
        raise ValueError('Finite explicit scalar context required')
    if not isinstance(exclude_names,frozenset) or any(not isinstance(n,str) for n in exclude_names):raise ValueError('Immutable source exclusion names required')
    buffs=manager.get_buffs(attacker,'__enemy__',when,exclude_names)
    for carrier in manager._active:
        if carrier.effect.get('stat') in MODIFIERS and when<carrier.expires_at:
            recipients=carrier.target_chars if carrier.target_chars is not None else manager._resolve_lazy(carrier)
            if any(n not in manager.squad_names for n in recipients):raise ValueError('Declared outgoing modifiers require allied recipients')
    if any(not math.isfinite(buffs[name]) for name in MODIFIERS):raise ValueError('Nonfinite declared modifier sum')
    original=damage._factor5
    def factor5(values,hit):
        value=original(values,hit)
        flag=hit.get(KIND_KEY)
        if flag==int(ActorKind.PROJECTILE):value+=values['projectile_dmg_pct']/100.
        elif flag==int(ActorKind.HP_SHIELD):value+=values['shield_dmg_pct']/100.
        return value
    # A private callable namespace keeps the canonical factor/entry untouched.
    calculator=_clone(damage.calc_damage,dict(damage.calc_damage.__globals__,_factor5=factor5))
    hit=damage.default_hit_type(is_normal_atk=False,is_full_burst=full_burst,coeff=coefficient)
    hit[KIND_KEY]=int(kind)
    result=calculator(base_attack,buffs,weapon,hit,enemy_def=defense,expected=True)
    return dict(result,kind=int(kind),factor5=factor5(buffs,hit),projectile_modifier=buffs['projectile_dmg_pct'],shield_modifier=buffs['shield_dmg_pct'],declared_model='v1',in_game_rules_verified=False)
