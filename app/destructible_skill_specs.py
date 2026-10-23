"""Private lowering of a plain all_projectiles skill into an ordinary row.

Only target routing changes. Scalar flags and values use the existing compiler;
this does not enable public battle admission or specialized projectile factors.
"""
import copy,math

MAGIC=0x44534b31
FIELDS=frozenset(('source','type','name','trigger','target','stat','values','fixed_value','max_trigger'))

def coefficient(effect,character):
    from calculator.buff_manager import _get_skill_lv
    if not isinstance(effect,dict) or set(effect)-FIELDS or effect.get('type')!='damage' or effect.get('stat')!='damage' or effect.get('target')!='all_projectiles':
        raise ValueError('Plain all_projectiles damage definition required')
    trigger=effect.get('trigger',{})
    budget=effect.get('max_trigger',-1)
    if type(budget) is not int or not -1<=budget<2**31:raise ValueError('Invalid projectile activation budget')
    if not isinstance(trigger,dict) or set(trigger)-{'timing','condition'} or trigger.get('condition',[]) or not isinstance(trigger.get('timing'),list):raise ValueError('Unsupported projectile skill trigger')
    if ('values' in effect)==('fixed_value' in effect):raise ValueError('Exactly one projectile coefficient source required')
    vals=effect.get('values')
    if vals is not None:
        if not isinstance(vals,dict):raise ValueError('Invalid projectile coefficient table')
        raw=vals.get(_get_skill_lv(character,effect),vals.get('10',0.))
    else:raw=effect['fixed_value']
    if type(raw) not in (int,float) or not math.isfinite(raw) or raw<0 or raw>1e30:raise ValueError('Invalid projectile coefficient')
    return float(raw)

def compiler_effect(effect,character):
    value=coefficient(effect,character);result=copy.deepcopy(effect)
    result.pop('values',None);result.update(target='boss',fixed_value=value)
    return result
