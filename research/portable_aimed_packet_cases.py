"""Literal no-core, target-factor and aimed body/target packet stimuli."""
import copy
from portable_interrupt_aim_cases import fixtures as original
from world_enemy_attack_cases import field


def fixtures():
    base=original();rows=[]
    def add(label,seed=0,*,intercept=0,part=0,critical=False,wide=None,scatter=False,dead=False):
        c=copy.deepcopy(base[seed]);c['name']='aimed-packet-'+label
        c['enemy']['core_px']=1e8
        if critical:c['effects'][0]['fixed_value']=100
        for stat,value in [('intercept_dmg_pct',intercept),('part_dmg_pct',part)]:
            if value:
                c['effects'].append(field(stat,value,'all_allies',stat));c['owners'].append(0)
        if wide=='pierce':
            c['effects'].append(field('pierce_enabled',1,'all_allies','pierce'));c['owners'].append(0)
        if wide=='explosion':
            c['weapon_metadata']['fire_stance_hold']=0
            for w in c['combat']['weapons'][:2]:w.update(mode='charge',charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100,base_weapon_type='RL')
        if scatter:
            for w in c['combat']['weapons'][:2]:w.update(pellets=3,muzzles=2)
        if dead:c['patterns'][0]['targets'][0]['hp']=1
        rows.append(c);return c
    add('core-suppressed')
    add('intercept',intercept=50)
    add('part-factor-is-distinct',part=200)
    add('critical-intercept',critical=True,intercept=50)
    add('charge-intercept',seed=21,intercept=50)
    add('heal-intercept',seed=18,intercept=100)
    add('part-core',seed=17,part=50)
    add('part-critical',seed=17,part=50,critical=True)
    add('pierce',intercept=50,wide='pierce')
    add('pierce-scatter',intercept=50,wide='pierce',scatter=True)
    add('pierce-dead',wide='pierce',dead=True)
    add('explosion',intercept=50,wide='explosion')
    add('explosion-heal',seed=18,intercept=50,wide='explosion')
    add('explosion-dead',wide='explosion',dead=True)
    add('part-pierce',seed=17,part=50,wide='pierce')
    add('part-explosion',seed=17,part=50,wide='explosion')
    return rows


def direct_fixtures():return fixtures()[:8]
