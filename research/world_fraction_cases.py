"""Literal critical/core fractional notification programs and session changes."""
import copy
from world_spawn_cases import fixtures as spawn_fixtures
from world_enemy_attack_cases import field

def fixtures():
 base=copy.deepcopy(spawn_fixtures()[0]);base.update(observe_fractional_hits=True,duration=1.5);base['patterns']=[dict(id='idle',kind='idle',until=dict(time=1.5))];rows=[]
 def effect(timing,stat='atk_pct',value=1,name='fraction',**kw):return field(stat,value,'self',name,timing,duration=-1,max_stack=128,**kw)
 def add(name,effects):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=[0]*len(effects));c['state_queries']=[(0,0,0,1,effects[0]['name'])];rows.append(c);return c
 for timing in ('crit_hit','crit_hit_count:1','crit_hit_count:2','core_hit','core_hit:2','core_hit_count:2'):
  c=add('fraction-'+timing,[effect(timing)])
  if 'core' in timing:c['enemy']['core_px']=10
 for rate in (-100,0,35,85,200):
  add('critical-clamp-'+str(rate),[effect('crit_hit_count:1'),field('crit_rate',rate,'self','rate','battle_start')])
 c=add('pellets3-muzzles2-frozen-critical',[effect('crit_hit'),field('crit_rate',35,'self','rate','battle_start')]);c['combat']['weapons'][0].update(base_weapon_type='SG',pellets=3,muzzles=2);c['duration']=.7
 c=add('critical-callback-does-not-resample-same-shot',[effect('crit_hit',stat='crit_rate',value=20)]);c['combat']['weapons'][0].update(base_weapon_type='SG',pellets=10);c['duration']=.7
 c=add('critical-then-core-order',[effect('crit_hit',stat='atk_pct',name='critical'),effect('core_hit',stat='crit_dmg',name='core')]);c['enemy']['core_px']=10
 for mode in ('normal','skill'):
  for counter in ('crit_hit','core_hit'):
   c=add('charge-'+mode+'-'+counter,[effect(counter)]);c['enemy']['core_px']=10;c['duration']=1.7
   for w in c['combat']['weapons']:w.update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100)
   if mode=='skill':
    c['effects'].insert(0,dict(name='mode',source='스킬1',type='weapon_change',weapon_type='SR',damage_coeff=100,max_ammo=-1,fire_rate=5,fire_rate_max=5,charge=True,charge_time=.2,full_charge_mult=300,pellets=3,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,skill_damage=True,target='self',duration=2,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].insert(0,0)
 c=add('core-kept-on-add-route',[effect('core_hit')]);c['enemy']['core_px']=10;c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=1,hp=10000000)))
 c=add('core-changes-next-world-frame',[effect('core_hit')]);c['patterns'].append(dict(id='core',kind='core',delay=.4,until=dict(time=.4),core_px=10))
 c=add('critical-retains-remainder-at-unit-rate',[effect('crit_hit'),field('crit_rate',85,'self','later-rate','every:0.2s')])
 c=add('core-unit-probability',[effect('core_hit')]);c['enemy']['core_px']=100
 c=copy.deepcopy(next(c for c in rows if c['name']=='charge-skill-crit_hit'));c['name']='skill-mode-excludes-normal-critical';c['effects'].append(field('normal_atk_crit_rate',85,'self','normal-rate','battle_start'));c['owners'].append(0);rows.append(c)
 c=add('bullet-critical-buff-expiry-order',[effect('crit_hit'),dict(field('crit_rate',85,'self','bullet-rate','battle_start'),duration_bullets=1)]);c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100);c['duration']=1.4
 for c in rows:
  c['post_fire_delays']=[.215 if w.get('mode')=='charge' else 0 for w in c['combat']['weapons']]
  for w in c['combat']['weapons']:
   if w.get('mode')=='charge':w['min_cycle']=.4
 return rows
