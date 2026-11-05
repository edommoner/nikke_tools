"""Named enemy filtering stimuli; construction never runs a battle or compiler."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

MARK='named:enemy:印'
BOSS='__enemy__'
ADDS=['__enemy__:wave#'+str(i) for i in (1,2,3)]

def fixtures():
    seed=copy.deepcopy(ammo()[0]);seed.pop('contract');rows=[]
    def add(label,kind='buff',mark_target=None,mark_name=MARK):
        c=copy.deepcopy(seed);c.update(name='named-enemy-'+label,effects=[],owners=[])
        c['patterns']=[dict(id='idle',kind='idle'),dict(id='wave',kind='summon',spec=dict(count=3,hp=1e15))]
        if mark_target is not None:c['effects'].append(field('received_dmg_pct',0,mark_target,mark_name));c['owners'].append(0)
        target='enemies_with_buff:'+mark_name
        if kind=='buff':listener=field('received_dmg_pct',5,target,'named-recipient-witness','on_attack',duration=.05)
        elif kind=='damage':listener=dict(name='named-packet-witness',source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,target=target,trigger=dict(timing=['on_attack'],condition=[]))
        else:
            c['effects'].append(field('def_pct',0,'all_enemies','extended-payload',duration=.1));c['owners'].append(0)
            listener=dict(instant('named_buff_duration_extend',.1,target,'named-duration-witness','on_attack'),target_effect='extended-payload')
        c['effects'].append(listener);c['owners'].append(0)
        picked=[BOSS] if mark_target in (None,'boss') else ADDS[:1] if mark_target=='target' else [BOSS]+ADDS
        present=[] if mark_target is None else [BOSS] if mark_target=='boss' else ADDS[:1] if mark_target=='target' else [BOSS]+ADDS
        c['contract']=dict(kind=kind,mark_name=mark_name,picked=[picked]*3,present=[present]*3,rank_steps=[0,1,2],rank_calls=3,recipient_calls=0 if kind=='damage' else 3,pools=[[BOSS]+ADDS]*3)
        rows.append(c);return c
    for kind in ('buff','damage','instant'):
        for label,target in [('missing',None),('boss','boss'),('add','target'),('all','all_enemies')]:add(kind+'-'+label,kind,target)
    add('opaque-colon-and-spaces',mark_target='target',mark_name=' a:b: 印 ')
    add('empty-name',mark_target='target',mark_name='')
    c=add('mark-expires-between-shots',mark_target='target');c['effects'][0]['duration']=.05;c['contract'].update(picked=[ADDS[:1],[BOSS],[BOSS]],present=[ADDS[:1],[],[]])
    c=add('late-wave-not-retargeted',mark_target='all_enemies');c['patterns'][1]['delay']=.05;c['contract'].update(picked=[[BOSS]]*3,present=[[BOSS]]*3,rank_steps=[1,2],rank_calls=2,pools=[[BOSS]+ADDS]*2)
    c=add('retired-wave',mark_target='all_enemies');c['patterns'][1]['until']=dict(time=.15);c['contract'].update(picked=[[BOSS]+ADDS,[BOSS]+ADDS,[BOSS]],rank_steps=[0,1],rank_calls=2,pools=[[BOSS]+ADDS]*2)
    c=add('reopened-same-id-drops-mark',mark_target='target');c['patterns'][1].update(after=['start','wave'],until=dict(time=.1),repeat=0);c['contract'].update(picked=[ADDS[:1],[BOSS],[BOSS]],present=[ADDS[:1],[],[]])
    c=add('other-owner-marker-is-visible',mark_target='target');c['owners'][0]=4
    c=add('same-name-union-across-casters',mark_target='boss');c['effects'].insert(1,field('received_dmg_pct',0,'target',MARK));c['owners'].insert(1,4);c['contract'].update(picked=[[BOSS]+ADDS[:1]]*3,present=[[BOSS]+ADDS[:1]]*3)
    c=add('explicit-removal-before-witness',mark_target='target');e=dict(instant('remove_named_buff',0,'all_enemies','remove-mark','on_attack'),target_effect=MARK,remove_scope='target');c['effects'].insert(1,e);c['owners'].insert(1,0);c['contract'].update(picked=[[BOSS]]*3,present=[[]]*3)
    c=add('no-adds-skips-filter');c['patterns'].pop();c['contract'].update(rank_calls=0,rank_steps=[],pools=[])
    c=add('all128-enemy-identities',mark_target='all_enemies');c['patterns'][1]['spec']['count']=127;pool=[BOSS]+['__enemy__:wave#'+str(i) for i in range(1,128)];c['contract'].update(picked=[pool]*3,present=[pool]*3,pools=[pool]*3)
    return rows
