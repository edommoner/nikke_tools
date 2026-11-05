"""Authored ally-burst stimuli; no portable packing or generated expectations."""
import copy
from portable_burst_recipient_cases import fixtures as burst_fixtures,instant
from world_enemy_attack_cases import field

def fixtures():
    base=copy.deepcopy(burst_fixtures()[0]);base['name']='ally-burst-none'
    base['effects'].append(instant('current_hp_reduce',50,'all_allies','drain'));base['owners'].append(0)
    for ally in base['environment']['allies']:ally['base_hp']=10000
    rows=[]
    def add(label,owners=(),target='self',before=(),before_owners=(),**kw):
        c=copy.deepcopy(base);c['name']='ally-burst-'+label
        c['effects'].extend(copy.deepcopy(before));c['owners'].extend(before_owners)
        for owner in owners:
            eff=instant('heal_hp_pct',1,target,'listener-'+str(owner),'event:ally_burst_cast');eff.update(copy.deepcopy(kw))
            c['effects'].append(eff);c['owners'].append(owner)
        c['contract']=dict(casts=3,hp=[5000]*5,listener_activations=[])
        rows.append(c);return c
    add('none')
    c=add('self-each',range(5));c['contract'].update(hp=[5300]*5,listener_activations=list(range(5))*3)
    for label,owner in [('caster',0),('noncaster',4)]:
        c=add(label,[owner]);c['contract']['hp'][owner]=5300;c['contract']['listener_activations']=[owner]*3
    c=add('all-allies',[4],target='all_allies');c['contract'].update(hp=[5300]*5,listener_activations=[4]*3)
    c=add('budget',[4],max_trigger=1);c['contract']['hp'][4]=5100;c['contract']['listener_activations']=[4]
    c=add('not-casted',[0,4]);c['contract']['hp'][4]=5300;c['contract']['listener_activations']=[4]*3
    for e in c['effects'][-2:]:e['trigger']['condition']=['burst_not_casted']
    for label,timing in [('after-own-cast','burst_cast'),('squad-order','event:ally_burst_cast')]:
        c=add(label,[4],before=[field('atk_pct',1,'all_allies','witness',timing)],before_owners=[0]);c['effects'][-1]['trigger']['condition']=['self_state:witness']
        c['contract']['hp'][4]=5300;c['contract']['listener_activations']=[4]*3
    c=add('reentry',range(5),before=[instant('burst_reentry',1,'self','reopen','burst_cast')],before_owners=[0])
    c['contract'].update(casts=4,hp=[5400]*5,listener_activations=list(range(5))*4)
    c=add('no-cast',range(5));c['effects']=c['effects'][1:];c['owners']=c['owners'][1:]
    for weapon in c['combat']['weapons']:weapon['gauge']=0
    c['contract'].update(casts=0,hp=[5000]*5,listener_activations=[])
    c=add('down-listener',[4]);c['patterns']=[dict(id='down',kind='attack',delay=.01,spec=dict(atk=1e8,coeff=100,target='slot:5',pierce=True,hits=1))]
    c['contract'].update(hp=[5000,5000,5000,5000,0],listener_activations=[4])
    c=add('reentry-via-broadcast',range(5),before=[instant('burst_reentry',1,'self','reopen','event:ally_burst_cast')],before_owners=[0])
    c['contract'].update(casts=4,hp=[5400]*5,listener_activations=list(range(5))*4)
    c=add('condition-false',[4]);c['effects'][-1]['trigger']['condition']=['burst_casted']
    c=add('duplicate-descriptor',[4]);c['effects'][-1]['trigger']['timing']*=2;c['contract']['hp'][4]=5600;c['contract']['listener_activations']=[4]*6
    return rows
