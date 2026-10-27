"""Real native control producers, never a precomputed notification schedule."""
import copy,importlib.util
from pathlib import Path

def fixtures():
    path=Path(__file__).with_name('verify-physical-locks.py')
    spec=importlib.util.spec_from_file_location('lock_cover_physical_factory',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    seed=module.fixtures()[0];rows=[]
    for label,owner,when,duration,blocked in (
        ('charging-owner',0,.3,.25,False),
        ('other-owner',1,.3,.25,False),
        ('blocked-owner',0,.3,.25,True),
        ('empty-owner',0,0.,.25,False),
        ('reload-bound-owner',0,.3,None,False)):
        case=copy.deepcopy(seed);case['name']='physical-lock-cover/'+label
        case['controls']=[{} for _ in range(5)]
        action=dict(t=when,action='cover')
        if duration is not None:action['duration']=duration
        case['controls'][owner]={'sequence':[action]}
        case['cover_contract']=dict(owner=owner,blocked=blocked,empty=when==0.,reload_bound=duration is None)
        if blocked:
            case['effects'].append(dict(name='cover-block',source='스킬1',type='buff',stat='cover_disabled',fixed_value=1,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])))
            case['owners'].append(owner)
        rows.append(case)
    return rows
