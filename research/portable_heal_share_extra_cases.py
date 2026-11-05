"""Additional independent CPU prerequisites; original twenty remain immutable."""
import copy
from portable_heal_share_cases import fixtures as original
from world_frame_native import roster_names


def fixtures():
    cases={r['name']:r for r in original()};result=[]
    def clone(label,source='presence-1'):
        case=copy.deepcopy(cases['heal-share-'+source]);case['name']='heal-share-extra-'+label;result.append(case);return case
    c=clone('lazy-lowest-snapshot');c['effects'][1]['target']='allies_lowest_hp:2'
    c['contract'].update(hp=[7500,7500,5000,5000,5000],weights=[(0,1),(1,1)])
    c=clone('lazy-excluding-caster');names=roster_names(c)
    c['effects'][1]['target']='allies_lowest_hp_excl:2';c['effects'][-1]['target']=names[1]
    c['contract'].update(hp=[5000,7500,7500,5000,5000],weights=[(1,1),(2,1)])
    for owner in (0,1):
        c=clone('runtime-condition-crosses-'+str(owner));c['effects'][1]['trigger']=dict(timing=['passive'],condition=['self_hp_below:60']);c['owners'][1]=owner
        if owner==1:
            c['name']='heal-share-extra-other-owner-passive-not-live'
            c['contract'].update(hp=[10000,5000,5000,5000,5000],weights=[(0,1)])
    c=clone('runtime-condition-false');c['effects'][1]['trigger']=dict(timing=['passive'],condition=['self_hp_below:10'])
    c['contract'].update(hp=[10000,5000,5000,5000,5000],weights=[(0,1)])
    c=clone('multiple-caster-carriers','same-owner-two-carriers');c['owners'][1:3]=[1,2];c['effects'][-1]['trigger']['timing']=['every:0.2s']
    c=clone('multiply-before-divide','overlap-ranked');c['effects'][-1]['fixed_value']=.001
    c['contract'].update(hp=[5000.04,5000.04,5000.02,5000,5000],portion_sequence=[(0,.04),(1,.04),(2,.02)],notice_order=[0],original_amounts=[.1])
    c=clone('single-recipient-no-division','self-two-carriers');c['effects'][-1]['fixed_value']=.001
    third=copy.deepcopy(c['effects'][1]);third['name']='third';c['effects'].insert(-1,third);c['owners'].insert(-1,0)
    c['contract'].update(hp=[5000.1,5000,5000,5000,5000],weights=[(0,3)],portion_sequence=[(0,.1)],notice_order=[0],original_amounts=[.1])
    return result
