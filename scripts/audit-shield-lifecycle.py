"""CPU shield subsystem references from authored effects/absorption operations.
Amounts returned by CPU are oracle outputs, never inputs to a future GPU run.
"""
import copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('shield_cpu',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.E;NAMES=v.NAMES

def scenarios():
 def shield(name,stat,target='all_allies',**kw):return E(name,'buff',stat,25,target,duration=60,**kw)
 for first,second in [('shield_from_max_hp_pct','shield_from_max_hp_pct'),('shared_shield_from_max_hp_pct','shared_shield_from_max_hp_pct'),('shield_from_max_hp_pct','shared_shield_from_max_hp_pct'),('shared_shield_from_max_hp_pct','shield_from_max_hp_pct')]:
  effects={NAMES[0]:[shield('old shield',first)],NAMES[1]:[shield('new shield',second,event='every:0.5s',max_trigger=1)]}
  for pierce in (False,True):
   yield first+'-'+second+('-pierce' if pierce else '-ordinary'),effects,[('absorb',0,100000,pierce),('absorb',1,100000,pierce),('absorb',0,1e9,pierce),('heal',0,200000,False)]
 for end in (False,True):
  effects={NAMES[0]:[shield('shared carrier','shared_shield_from_max_hp_pct',end_on_shield_consumed=end),E('ended probe','buff','atk_pct',1,event='event:state_end:shared carrier',max_stack=10)]}
  yield 'carrier-'+('end-after-all-recipients' if end else 'retained-after-zero'),effects,[('absorb',i,1e9,False) for i in range(5)]+[('heal',0,1e9,False)]
 for owner in (0,1):
  effects={NAMES[0]:[shield('protected shield','shield_from_max_hp_pct')],NAMES[owner]:[E('shield protection','buff','shield_invincible',1)]}
  # Keep the shield when marker owner and shield owner are the same.
  if owner==0:effects[NAMES[0]].insert(0,shield('protected shield','shield_from_max_hp_pct'))
  yield 'invincibility-owner-'+str(owner),effects,[('absorb',0,1e9,False),('absorb',1,1e9,False)]
 effects={NAMES[0]:[E('next shield amp','buff','next_shield_hp_pct',50,'all_allies'),shield('first consumes amp','shared_shield_from_max_hp_pct'),shield('second unamplified','shield_from_max_hp_pct')]}
 yield 'next-amplifier-consumed-per-recipient',effects,[('absorb',0,100000,True),('heal',0,1e9,False)]
 effects={NAMES[0]:[E('lazy next shield amp','buff','next_shield_hp_pct',50,'allies_random:1'),shield('random amp consumer','shared_shield_from_max_hp_pct')]}
 yield 'lazy-random-amplifier-resolves-on-first-shield',effects,[('absorb',0,100000,False)]
 effects={NAMES[0]:[shield('refreshed shield','shared_shield_from_max_hp_pct'),E('conditional amp','buff','next_shield_hp_pct',50,'all_allies',event='every:0.5s',max_trigger=1,condition=['during_shield']),shield('refreshed shield','shared_shield_from_max_hp_pct',event='every:1s',max_trigger=1)]}
 yield 'refresh-amplifier-sees-old-positive-shield',effects,[('tick',0,1.1,False)]
 effects={NAMES[0]:[shield('externally protected shield','shared_shield_from_max_hp_pct')],NAMES[2]:[E('protection from another caster','buff','shield_invincible',1,NAMES[0])]}
 yield 'maker-protected-by-another-caster',effects,[('absorb',0,1e9,True),('absorb',1,1e9,False)]
 effects={NAMES[0]:[shield('stack shield','shared_shield_from_max_hp_pct',max_stack=5)]}
 yield 'stack-add-does-not-rebuild-capacity',effects,[('addstack',0,2,False),('absorb',0,100000,False),('heal',0,1e9,False)]
 effects={NAMES[0]:[E('expires shield','buff','shared_shield_from_max_hp_pct',25,'all_allies',duration=1.5)]}
 yield 'expiration-removes-shield-maps-with-carrier',effects,[('tick',0,2,False),('absorb',0,100000,False)]
 effects={NAMES[0]:[shield('refreshable','shared_shield_from_max_hp_pct',event='battle_start'),E('on break refresh','buff','shared_shield_from_max_hp_pct',50,'all_allies',event='event:shield_consumed',duration=60)]}
 yield 'synchronous-consumed-callback-creates-shield',effects,[('absorb',0,1e9,False),('absorb',1,100000,False)]
 for scope in ('target','global'):
  effects={NAMES[0]:[shield('strip shield','shared_shield_from_max_hp_pct')]}
  yield 'named-removal-'+scope,effects,[('remove',0,scope,False),('absorb',0,100000,False),('absorb',1,100000,False)]

def snapshot(bm):
 return dict(entries=[dict(uid=ab.uid,name=ab.effect.get('name'),caster=ab.caster,targets=copy.deepcopy(ab.target_chars),stack=ab.stack,shield=copy.deepcopy(ab.shield_per_target),capacity=copy.deepcopy(ab.shield_max_per_target)) for ab in bm._active if ab.effect.get('stat') in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct','next_shield_hp_pct')],
             amount={n:bm.shield_amount(n) for n in NAMES},capacity={n:bm.shield_capacity(n) for n in NAMES},has_shield={n:bm.has_shield(n) for n in NAMES},ended_probe=[ab.stack for ab in bm._active if ab.effect.get('name')=='ended probe'])
