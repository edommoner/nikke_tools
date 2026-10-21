"""Literal physical contracts; same inputs/native oracle for CUDA and Metal."""
import copy,math
from world_fraction_cases import fixtures as fraction_fixtures
from world_enemy_attack_cases import field

def fixtures():
 base=copy.deepcopy(fraction_fixtures()[0]);base.update(duration=.55,effects=[],owners=[],state_queries=[],controls=[{} for _ in range(5)],control_mode='solo')
 for w in base['combat']['weapons']:w.update(enabled=True)
 base['combat']['weapons'][0].update(enabled=True,pellets=3,muzzles=2,capacity=6,interval=.1)
 rows=[]
 def add(name,effects):
  c=copy.deepcopy(base);c.update(name='projectile-'+name,effects=effects,owners=[0]*len(effects));rows.append(c);return c
 def buff(stat,value,name='modifier',timing='battle_start',**kw):return field(stat,value,'self',name,timing,**kw)
 def witness():return buff('atk_pct',1,'pellet-witness','pellet_hit_count:2',max_stack=128)
 for value in (-1e200,-4,-2.5,-1.5,-.5,.5,1.5,2.5,5):
  add('add-'+str(value),[buff('pellet_count',value),witness()])
 for value in (-2,0,.1,.5,1.5,2.5,3.5):
  add('fixed-'+str(value),[buff('pellet_count_fixed',value),buff('pellet_count',4,'add'),witness()])
 c=add('fixed-sum-before-round',[buff('pellet_count_fixed',1.25,'first'),buff('pellet_count_fixed',1.25,'second'),witness()])
 c=add('same-name-stack',[buff('pellet_count',.5,max_stack=3,timing='on_attack'),witness()])
 c=add('finite-expiry',[buff('pellet_count',2,duration=.2),witness()])
 c=add('ammo-callback-before-auto-snapshot',[buff('pellet_count',1,timing='squad_ammo_consume',max_stack=3),witness()])
 c=add('counted-ammo-before-auto-snapshot',[buff('pellet_count',1,timing='squad_ammo_consume:1',max_stack=3),field('infinite_ammo',1,'all_allies_excl_self','other-infinite'),witness()])
 c=add('last-bullet-before-auto-snapshot',[buff('pellet_count_fixed',2,timing='last_bullet_fire'),witness()]);c['combat']['weapons'][0]['capacity']=2
 c=add('child-cannot-resplit-current-shot',[buff('pellet_count',1,timing='pellet_hit_count:1',max_stack=3),witness()])
 for timing in ('full_charge','squad_ammo_consume','on_attack'):
  c=add('charge-snapshot-'+timing,[buff('pellet_count',1,timing=timing,max_stack=3),witness()]);c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SG',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100);c['post_fire_delays'][0]=.2;c['duration']=1
 c=add('counted-ammo-after-charge-snapshot',[buff('pellet_count',1,timing='squad_ammo_consume:1',max_stack=3),field('infinite_ammo',1,'all_allies_excl_self','other-infinite'),witness()]);c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SG',charge=.2,interval=.4,min_cycle=.2,full_charge_mult=300,gauge_mult=100);c['post_fire_delays'][0]=.2;c['duration']=1
 for family in ('pierce','explosion','both'):
  for value in (0,99.9,math.nextafter(100-1e-9,-math.inf),100-1e-9,100):
   e=[buff('explosion_range' if family!='pierce' else 'pierce_range',value),witness()]
   if family!='explosion':e.append(buff('pierce_enabled',1,'pierce'))
   if family=='both':e.append(buff('pierce_range',1000,'pierce-more'))
   c=add('range-'+family+'-'+value.hex() if isinstance(value,float) else 'range-'+family+'-'+str(value),e)
   c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='part'+str(i),hp=1e8,reach=i) for i in range(1,6)])]
   if family!='pierce':
    c['combat']['weapons'][0].update(mode='charge',base_weapon_type='RL',charge=.1,interval=.2,min_cycle=.1,full_charge_mult=100,gauge_mult=100);c['post_fire_delays'][0]=.1
 c=add('range-expiry-next-shot',[buff('pierce_range',100,duration=.2),buff('pierce_enabled',1,'pierce'),witness()]);c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='part2',hp=1e8,reach=2)])]
 c=add('range-pellet-child-frozen',[buff('pierce_range',100,timing='pellet_hit_count:1'),buff('pierce_enabled',1,'pierce'),witness()]);c['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='part2',hp=1e8,reach=2)])]
 return rows
