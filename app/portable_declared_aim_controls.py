"""Explicit operation overlay, after unchanged original roster verification."""
import copy

def apply(chars,overrides):
    from calculator.timeline import validate_control
    names={c['name'] for c in chars}
    if not isinstance(overrides,dict) or not overrides or set(overrides)-names:raise ValueError('Declared aim controls require existing caster names')
    result=copy.deepcopy(chars)
    for char in result:
        if char['name'] not in overrides:continue
        aim=overrides[char['name']]
        if not isinstance(aim,list) or not 1<=len(aim)<=8:raise ValueError('Declared aim list must be bounded and nonempty')
        control=copy.deepcopy(char.get('control',{}));control['aim']=copy.deepcopy(aim)
        validate_control(control,char['name']);char['control']=control
    return result
