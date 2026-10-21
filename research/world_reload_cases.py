"""Literal reload contracts shared by CUDA and Metal."""
import copy
from world_charge_control_cases import fixtures as charge_fixtures
from world_enemy_attack_cases import field

def fixtures():
 rows=[];base=copy.deepcopy(next(c for c in charge_fixtures() if c['name']=='manual-charge-sequence-until-0.8'));base.update(effects=[],owners=[],state_queries=[],duration=1.4)
 for w in base['combat']['weapons']:w.update(reload=.6,capacity=3)
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name='reload-'+name,effects=effects,owners=[0]*len(effects) if owners is None else owners);rows.append(c);return c
 def fixed(value=.2,name='fixed',**kw):return field('reload_time_fixed',value,'self',name,**kw)
 def force(timing='charge_hold:0.1',target='self',name='force',**kw):return dict(name=name,source='스킬1',type='instant',stat='force_reload',target=target,max_trigger=1,trigger=dict(timing=[timing],condition=[])) | kw
 for value in (0,.0004,.2,.9,-.2):add('fixed-'+str(value),[fixed(value),force()])
 c=add('bare-fixed-falls-back',[fixed(),force()]);c['effects'][0].pop('fixed_value')
 c=add('level-fixed',[fixed(),force()]);c['effects'][0].pop('fixed_value');c['effects'][0]['values']={'1':.454,'10':.0004}
 add('max-not-sum-or-base',[fixed(.2),fixed(.4,'second-fixed'),force()])
 add('later-shorter-fixed',[fixed(.4),fixed(.2,'second-fixed'),force()])
 add('expiry-does-not-reschedule',[fixed(.7,duration=.4),force()])
 add('natural-without-force',[fixed(.3)]);rows[-1]['controls']=[{} for _ in range(5)]
 c=add('stacked-fixed',[fixed(.1,max_stack=3,timing='charge_hold:0'),force()]);c['controls']=[{} for _ in range(5)];c['effects'][1]['trigger']['timing']=['on_attack_count:3'];c['duration']=2.4
 add('force-cancels-before-later-raw-alias',[fixed(.3),force(),field('atk_pct',1,'self','must-not-trigger','charge_hold:0.10',condition=['during_charge'])])
 for when in ('battle_start','charge_hold:0'):
  add('force-'+when,[force(when)])
 for value in (0,-.2):add('startup-fixed-'+str(value),[fixed(value),force('battle_start')])
 for target in ('all_allies','all_allies_excl_self','allies_top_atk:2'):
  add('recipient-'+target,[fixed(.3),force(target=target)])
 c=add('already-reloading-not-restarted',[fixed(.6),force('battle_start',name='initial-force'),force('every:0.1s',name='ignored-force',max_trigger=9)]);c['duration']=.45
 c=add('full-reload-callback-restarts',[fixed(.3),force('battle_start',name='initial-force'),force('event:full_reload',name='second-force')]);c['duration']=1.2
 c=add('clip-three-refills',[fixed(.1),force()]);c['weapon_metadata']['clip_count']=3
 for w in c['combat']['weapons']:w['clip_count']=3;w['capacity']=7
 for mode in ('charge','auto','auto_warmup'):
  c=add('infinite-'+mode,[fixed(.3),field('infinite_ammo',1,'self','unlimited'),force('charge_hold:0.1' if mode=='charge' else 'on_attack')]);c['combat']['weapons'][0].update(mode=mode,base_weapon_type='SR' if mode=='charge' else 'MG' if mode=='auto_warmup' else 'AR');c['post_fire_delays'][0]=.215 if mode=='charge' else 0.
 for finite in (-1,.9):
  c=add('fixed-ignores-later-condition-'+str(finite),[fixed(.3,duration=finite,condition=['self_hp_above:99']),force('every:0.5s')]);c['patterns'].append(dict(id='hurt-fixed-owner',kind='attack',delay=.3,spec=dict(atk=100,coeff=100,target='slot:1',hits=1)))
 mode=dict(name='mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=2,fire_rate=10,fire_rate_max=10,charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=.25,core_dmg_mult=200,skill_damage=True,target='self',reload_time=.9,trigger=dict(timing=['battle_start'],condition=[]))
 for timing in ('battle_start','on_attack','every:0.2s'):
  c=add('mode-context-'+timing,[copy.deepcopy(mode),force(timing)]);c['duration']=2
 for kind in ('fixed','force','ordinary-buff','ordinary-ammo'):
  e=fixed(.3,max_trigger=-1) if kind=='fixed' else force(max_trigger=-1) if kind=='force' else field('atk_pct',100,'self','disabled-buff','battle_start',max_trigger=-1) if kind=='ordinary-buff' else dict(force('battle_start',max_trigger=-1),stat='ammo_charge_pct',fixed_value=-100)
  c=add('explicit-negative-budget-'+kind,[e,force(name='enabled-force')])
 add('same-name-fixed-alias',[fixed(.2),fixed(.4),force()])
 c=add('bare-before-valued-alias',[fixed(),fixed(.4),force()]);c['effects'][0].pop('fixed_value')
 c=add('valued-before-bare-alias',[fixed(.4),fixed(),force()]);c['effects'][1].pop('fixed_value')
 add('ordered-recipient-union',[fixed(.3),force(target=['self','all_allies_excl_self','self'])])
 add('shared-team-force-budget',[fixed(.3),force('body_hit_count:1')])
 add('fixed-ignores-speed-buffs',[fixed(.4),field('reload_speed_pct',100,'self','speed'),force()])
 from detail_coverage import body_for
 import engine_worker
 for name in ('\ubc00\ud06c : \ube14\ub8e8\ubc0d \ubc14\ub2c8','\uc9c8'):
  roster=[name,'\ubaa8\ub354\ub2c8\uc544','\ub8e8\uc8fc','\ub3c4\ub77c','\uc580'];prepared=engine_worker.evaluate(dict(body_for(roster,1),_portable_static_inputs=True));assert prepared['cpu_battle_executed'] is False
  effects=[copy.deepcopy(r['effect']) for r in prepared['effects'] if r['owner']==name and r['effect'].get('stat') in ('reload_time_fixed','force_reload')];assert len(effects)==2
  c=add('catalog-'+name,effects);c['names']=roster;c['controls'][0]['sequence'][0]['until']=1.2
  if name=='\uc9c8':
   c['combat']['weapons'][0]['stage']=1;c['effects'].append(dict(name='initial-gauge',source='\uc2a4\ud0ac1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0)
 for stat,value,timing in (('ammo_charge_pct',-100,'every:0.3s'),('ammo_charge_pct',50,'every:0.9s'),('ammo_charge_flat',1,'every:0.9s')):
  add('ordinary-ammo-'+stat+'-'+str(value),[fixed(.3),dict(force(timing),stat=stat,fixed_value=value)])
 return rows
