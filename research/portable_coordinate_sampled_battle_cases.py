"""Sampled physical native worlds plus callback and exact capacity witnesses."""
import copy
from portable_coordinate_sampling_cases import fixtures as native_cases
from world_enemy_attack_cases import field
def fixtures():
    rows=native_cases()
    def add(label,index=3):
        c=copy.deepcopy(rows[index]);c['name']='coordinate-sampling-common/'+label;rows.append(c);return c
    for label,stat,value,timing in [('critical-snapshot','crit_dmg',100,'crit_hit'),('spread-snapshot','accuracy_pct',100,'pellet_hit_count:1'),('core-snapshot','atk_pct',100,'core_hit')]:
        c=add(label);c['enemy']['core_px']=20;c['effects'].append(field(stat,value,'self',label,timing,max_stack=10));c['owners'].append(0)
    c=add('muzzle-core-average');c['enemy']['core_px']=20;c['effects'].append(field('atk_pct',20,'self','not-core','hit_count:1',condition=['not_core'],max_stack=10));c['owners'].append(0)
    c=add('targets-127',6);c['duration']=.05;c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='p'+str(i),hp=1e8,x=0.,y=0.,r=100.,z=127-i) for i in range(127)])]
    c=add('pellets-1024',5);c['duration']=.05;c['combat']['weapons'][0].update(pellets=64,muzzles=8);c['effects'].append(field('pellet_count_fixed',128,'self','capacity-128'));c['owners'].append(0)
    for probability in (0,50,100):
        c=add('condition-prob-'+str(probability));c['effects'].append(field('atk_pct',10,'self','prob-'+str(probability),'on_attack',condition=['prob:'+str(probability)],max_stack=10));c['owners'].append(0)
    return rows
