"""Full original Rei skill reaches its real100-shot trigger under logical aims."""
import copy
from portable_coordinate_typed_aim_cases import fixtures as aim_cases

def fixtures():
    rows=[];base=aim_cases()[-1]
    for label,duration in (('control',1),('body',12),('adds',12),('manual-typed-with-adds',12)):
        c=copy.deepcopy(base);c.pop('expect_reference_gap');c['name']='coordinate-typed-actor/'+label
        c['body']['duration']=duration;c['patterns'][0]['until']['time']=duration+1
        if label in ('adds','manual-typed-with-adds'):
            c['patterns'].append(dict(id='logical-adds',kind='summon',spec=dict(count=2,hp=1e30)))
        c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'][:1])
        c['typed_actor_policy']=dict(mode='canonical-current-damage-v1')
        if label=='manual-typed-with-adds':
            c['declared_aim_controls']={c['body']['squad'][0]:[dict(at='typed-back',priority=90)]}
        rows.append(c)
    return rows
