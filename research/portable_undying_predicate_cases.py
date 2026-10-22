"""Literal live-stat predicates, independent of the marker's name/value."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(ammo_fixtures()[0]);base.pop('contract');rows=[]
    def add(label,marker=True,value=1,results=(True,True,True),damage=(6000,6600,7200),stack=3,owner=0):
        case=copy.deepcopy(base);case['name']='undying-predicate-'+label
        if owner!=0:
            case['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10)
            case['combat']['weapons'][owner].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
        case['effects']=[field('crit_rate',-100,'self','no-crit')]
        if marker:case['effects'].append(field('undying',value,'self','differently-named-marker'))
        case['effects'].append(field('atk_pct',10,'self','undying-witness',timing='on_attack',duration=10,max_stack=128,condition=['self_undying']))
        case['owners']=[owner]*len(case['effects'])
        case['contract']=dict(owner=owner,results=list(results),queries=[[v] for v in results],damage=list(damage),stack=stack,ammo=7)
        rows.append(case);return case
    add('absent',False,results=(False,)*3,damage=(6000,)*3,stack=0)
    add('present')
    add('zero-value',value=0)
    add('negative-value',value=-1)
    c=add('name-is-not-stat',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][1].update(stat='atk_pct',fixed_value=0,name='undying')
    c=add('other-stat',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][1]['stat']='invincible'
    c=add('expires',results=(True,False,False),damage=(6000,6600,6600),stack=1);c['effects'][1]['duration']=.1
    c=add('arrives',results=(False,True,True),damage=(6000,6000,6600),stack=2);c['effects'][1]['trigger']['timing']=['every:0.1s'];c['effects'][1]['max_trigger']=1
    c=add('finite-witness',damage=(6000,)*3,stack=1);c['effects'][-1]['duration']=.05
    c=add('permanent-witness',results=(True,False,False),damage=(6000,6600,6600),stack=1);c['effects'][1]['duration']=.1;c['effects'][-1]['duration']=-1
    add('last-owner',owner=4)
    c=add('foreign-self',results=(False,)*3,damage=(6000,)*3,stack=0);c['owners'][1]=4
    c=add('ally-applies');c['owners'][1]=4;c['effects'][1]['target']=roster_names(c)[0]
    c=add('all-allies');c['owners'][1]=4;c['effects'][1]['target']='all_allies'
    c=add('different-recipient',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][1]['target']=roster_names(c)[4]
    c=add('stacked-zero-marker',value=0);c['effects'][1].update(max_stack=3);c['effects'][1]['trigger']['timing']=['on_attack']
    c=add('marker-after-witness',results=(False,True,True),damage=(6000,6000,6600),stack=2);c['effects'][1]['trigger']['timing']=['on_attack'];c['effects'][1],c['effects'][2]=c['effects'][2],c['effects'][1]
    c=add('runtime-hp-gate',results=(True,True,False),stack=2);c['effects'][1]['trigger']['condition']=['self_hp_above:75'];c['effects'].append(instant('current_hp_reduce',90,'self','drain','on_attack_count:2'));c['owners'].append(0)
    c=add('finite-gate-snapshot');c['effects'][1].update(duration=1);c['effects'][1]['trigger']['condition']=['self_hp_above:75'];c['effects'].append(instant('current_hp_reduce',90,'self','drain','on_attack_count:2'));c['owners'].append(0)
    c=add('first-condition-false',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].insert(0,'self_hp_below:1');c['contract']['queries']=[[],[],[]]
    c=add('last-condition-false',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].append('self_hp_below:1');c['contract']['queries']=[[True]]*3
    c=add('two-conditions');c['effects'][-1]['trigger']['condition'].append('self_undying');c['contract']['queries']=[[True,True]]*3
    return rows
