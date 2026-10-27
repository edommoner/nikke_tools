"""Explicit literal operations applied after original roster identity verification."""
import copy,math

def apply(chars,overrides):
    from calculator.timeline import validate_control
    names={c['name'] for c in chars}
    if not isinstance(overrides,dict) or not overrides or set(overrides)-names:raise ValueError('Declared manual sequences require existing caster names')
    result=copy.deepcopy(chars)
    for char in result:
        if char['name'] not in overrides:continue
        rows=overrides[char['name']]
        if not isinstance(rows,list) or not 1<=len(rows)<=8:raise ValueError('Declared manual sequence must be bounded and nonempty')
        previous=-1
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'action','t','duration'} or row['action']!='cover':raise ValueError('Only explicit cover sequence literals supported')
            at,duration=row['t'],row['duration']
            if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=180 for v in (at,duration)) or at<previous:raise ValueError('Manual times must be ordered finite nonnegative literals')
            previous=at
        control=copy.deepcopy(char.get('control',{}))
        if control.get('sequence'):raise ValueError('Original manual sequence cannot be overwritten')
        control['sequence']=copy.deepcopy(rows)
        validate_control(control,char['name']);char['control']=control
    return result
