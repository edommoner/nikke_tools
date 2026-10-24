"""Literal parent-quantity worlds; probability and damage remain outputs."""
import copy
from portable_coordinate_physical_gpu_cases import fixtures as physical


def fixtures():
    base=physical()[7];rows=[]
    def add(name,**changes):
        case=copy.deepcopy(base);case['name']='coordinate-quantity/'+name
        case['effects'].append(dict(name='expanded-charge-parent',source='스킬2',type='damage',stat='dealt_fixed_damage',fixed_value=25,target='target_body',trigger=dict(timing=['full_charge_hit'],condition=[])))
        case['owners'].append(0);case['observe_coordinate_landings']=True
        case['combat']['weapons'][0].update(**changes);rows.append(case);return case
    add('pierce-parent')
    add('two-muzzles-seven-pellets',pellets=7,muzzles=2)
    case=add('large-parent',pellets=7,muzzles=2);case['base_atk'][0]=10**15
    case=add('including-interrupt');case['patterns'].insert(0,dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=3,z=3)]))
    case=add('zero-child');case['effects'][-1]['fixed_value']=0
    case=add('fraction-to-zero');case['effects'][-1]['fixed_value']=.001
    case=add('last-owner')
    case['combat']['weapons'][4]=copy.deepcopy(case['combat']['weapons'][0])
    case['combat']['weapons'][0].update(charge=10,interval=10,min_cycle=10)
    case['owners']=[4]*len(case['owners'])
    case=add('two-shooters');case['combat']['weapons'][3]=copy.deepcopy(case['combat']['weapons'][0])
    return rows
