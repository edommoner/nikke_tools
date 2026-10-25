"""Author both pending queues; no landing values, schedule or random table."""
import copy
from portable_coordinate_pending_cases import fixtures as pending
from portable_coordinate_sampled_battle_cases import fixtures as physical
from world_enemy_attack_cases import field

def fixtures():
    base=copy.deepcopy(pending()[0]);base.pop('contract');base.update(sampled_burst=True,sampled_skill=True,coordinate_packet_trace=False)
    pairs=[(e,o) for e,o in zip(base['effects'],base['owners']) if e['name']!='no-crit'];base['effects']=[e for e,o in pairs];base['owners']=[o for e,o in pairs]
    base['effects'].insert(0,field('crit_rate',35,'self','sampled-rate'));base['owners'].insert(0,0)
    base['combat']['weapons'][0]=dict(copy.deepcopy(physical()[5]['combat']['weapons'][0]),stage=3,cooldown=40)
    rows=[]
    def add(label,optin=False,**changes):
        c=copy.deepcopy(base);c.update(name='coordinate-sampled-burst/'+label,seed=73+len(rows));e=c['effects'][-1];e.update(changes)
        if optin:e.update(stat=changes.get('stat','damage'),land_in_full_burst=True,hits_parts=changes.get('hits_parts',True))
        rows.append(c);return c
    def append(c,e):c['effects'].append(e);c['owners'].append(0)
    add('legacy-single')
    c=add('legacy-three',target='same_target:reference-attack');e=copy.deepcopy(c['effects'][-1]);e.update(name='reference-attack',stat='sequential_damage:3',target='boss');e['trigger']['timing']=['every:20s'];append(c,e)
    c=add('legacy-duplicate');c['effects'][-1]['trigger']['timing']*=2
    add('legacy-zero',fixed_value=0)
    c=add('legacy-earlier-buff');c['effects'].insert(-1,field('atk_pct',100,'self','earlier','burst_cast'));c['owners'].insert(-1,0)
    c=add('legacy-later-buff');append(c,field('atk_pct',100,'self','later','burst_cast'))
    c=add('legacy-entry-buff');append(c,field('atk_pct',100,'self','entry','full_burst_start'))
    c=add('legacy-ordinary-prefix');e=copy.deepcopy(c['effects'][-1]);e.update(name='ordinary-prefix',stat='burst_damage');e['trigger']['timing']=['full_burst_start'];append(c,e)
    c=add('legacy-two-amounts');e=copy.deepcopy(c['effects'][-1]);e.update(name='other-legacy',fixed_value=50);append(c,e)
    for label,value in [('zero-rate',-100),('unit-rate',200)]:c=add('legacy-'+label);c['effects'][0]['fixed_value']=value
    add('legacy-missing-reference',scaling='stack_count',scaling_ref='missing')
    add('optin-all-parts',True)
    add('optin-three',True,stat='sequential_damage:3')
    add('optin-zero-hits',True,stat='sequential_damage:0')
    c=add('optin-latched-reference',True,stat='sequential_damage:cast-count');e=field('',0,'self','cast-count',max_stack=9);e['trigger']['timing']=['battle_start','full_burst_start'];append(c,e)
    c=add('optin-later-buff',True);append(c,field('atk_pct',100,'self','later','burst_cast'))
    c=add('optin-entry-buff',True);append(c,field('atk_pct',100,'self','entry','full_burst_start'))
    c=add('optin-parts-born',True);c['patterns'][0]['delay']=.55
    c=add('optin-parts-expired',True);c['patterns'][0]['until']=dict(time=.3)
    add('optin-pierce',True,stat='pierce_damage:3',hits_parts=False)
    c=add('optin-explosion',True,stat='projectile_explosion_damage:3',hits_parts=False);append(c,field('explosion_range',200,'self','wide'))
    c=add('mixed-queues',True,stat='sequential_damage:3');e=copy.deepcopy(base['effects'][-1]);e['name']='legacy-after-optin';append(c,e)
    c=add('optin-named-child',True,stat='sequential_damage:3');e=copy.deepcopy(base['effects'][-1]);e.update(name='ordinary-child',stat='bonus_damage:2');e['trigger']=dict(timing=['hit_count:parts-source:1'],condition=['trigger_hit_crit']);append(c,e)
    return rows
