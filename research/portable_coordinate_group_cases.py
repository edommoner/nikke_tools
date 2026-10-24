"""Authored expanded-packet group worlds; no target or shot schedule packed."""
import copy
from portable_coordinate_physical_common_cases import fixtures as physical
from world_enemy_attack_cases import field


def fixtures():
    rows=[]
    for source in physical():
        c=copy.deepcopy(source);c['name']='coordinate-group-common/'+c['name'].split('/')[-1]
        c['effects'].append(field('atk_pct',0,'self','group-count-witness',timing='multi_hit:1'));c['owners'].append(0)
        c['effects'].append(field('atk_pct',0,'self','group-two-witness',timing='multi_hit:2'));c['owners'].append(0)
        rows.append(c)
    # Native route: body packets can be routed to a live ADD while PART packets
    # still land on geometry. A one-HP ADD retires before the next pellet.
    for hp in [1.,1e8]:
        c=copy.deepcopy(rows[3]);c['name']='coordinate-group-common/add-'+('retirement' if hp==1 else 'alive')
        c['patterns'].insert(0,dict(id='adds',kind='summon',spec=dict(count=2,hp=hp)))
        rows.append(c)
    def child(case,threshold=1):
        case['effects'].append(dict(name='group-target-child',source='declared',type='damage',stat='bonus_damage',target='target',fixed_value=10.,trigger=dict(timing=[f'multi_hit:{threshold}'],condition=[])));case['owners'].append(0)
    c=copy.deepcopy(rows[0]);c['name']='coordinate-group-common/child-target-body';child(c);rows.append(c)
    c=copy.deepcopy(rows[9]);c['name']='coordinate-group-common/child-retired-adds';child(c,2);rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='coordinate-group-common/zero-damage-body';c['combat']['weapons'][0]['coefficient']=0;c['patterns'][0]['targets'][0]['r']=8.9;rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='coordinate-group-common/two-owners';c['combat']['weapons'][1]=copy.deepcopy(c['combat']['weapons'][0])
    c['effects'].append(field('atk_pct',0,'self','second-owner-witness',timing='multi_hit:1'));c['owners'].append(1)
    c['effects'].append(field('crit_rate',-100,'self','second-owner-no-crit'));c['owners'].append(1);rows.append(c)
    c=copy.deepcopy(rows[5]);c['name']='coordinate-group-common/long-history';c['duration']=1.5;c['combat']['weapons'][0].update(interval=.01,capacity=300);rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='coordinate-group-common/group-buff-next-shot';c['duration']=.15
    c['effects'].append(field('atk_pct',100,'self','group-atk',timing='multi_hit:1',max_stack=128));c['owners'].append(0);rows.append(c)
    return rows
