"""Nonpositive native bases must be clamped after signed count reduction."""
import copy
from portable_nonfull_charge_cases import fixtures as prior
from world_enemy_attack_cases import field


def fixtures():
    rows=[]
    for label,base,reduction,activations,extra in [('zero-negative',0,-1,3,{}),('negative-negative',-1,-1,3,{}),('fractional-negative',0,-1.9,3,{}),('negative-expires',0,-1,3,dict(duration=.4)),('positive-control',1,-1,1,{}),('signed-minimum',-2147483648,-100000000,3,{}),('signed-maximum',2147483647,-1,0,{})]:
        c=copy.deepcopy(prior()[1]);c['name']='partial-reduction-'+label;c['effects'][1]['trigger']['timing']=['non_full_charge_fire_count:'+str(base)]
        c['effects'].append(field('trigger_count_reduce',reduction,'self','signed-reducer',target_effect='nonfull-watch',**extra));c['owners'].append(0)
        c['contract'].update(activations=activations,hp=[5000+100*activations]+[5000]*4);rows.append(c)
    return rows
