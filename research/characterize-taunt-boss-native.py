"""Original simulate/boss target selector;authored effects,untouched targeting and damage."""
import copy,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator import timeline,buff_manager
from timer_registry_cases import NAMES

def main():
 rows=[]
 for owner in range(5):
  for effect_target in ('self','all_allies','boss'):
   taunter=0 if effect_target=='all_allies' else owner
   for rule in ('all','slot:2','top_atk:1','random:1'):
    for ignore in ((False,) if rule=='all' else (False,True)):
     for stealth in ('none','taunter','others','all'):
      effects=[(dict(name='taunt-study',source='스킬1',type='buff',stat='taunt',fixed_value=0,target=effect_target,duration=-1,trigger=dict(timing=['battle_start'],condition=[])),NAMES[owner])]
      hidden=[] if stealth=='none' else [taunter] if stealth=='taunter' else [i for i in range(5) if i!=taunter] if stealth=='others' else list(range(5))
      for i in hidden:
       effects.append((dict(name=f'stealth-{i}',source='스킬2',type='buff',stat='stealth',fixed_value=0,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])),NAMES[i]))
      observed_bm=[]
      def register(bm):bm._effects=copy.deepcopy(effects);bm._build_notify_index();observed_bm.append(bm)
      metadata={n:dict(timeline._NIKKE[n],weapon_type='AR',is_charge=False,input_type='DOWN',burst_stage='0',fire_rate=1,fire_rate_max=1,damage_coeff=100,max_ammo=100) for n in NAMES}
      spec=dict(target=rule,coeff=100,atk=1000,pierce=True)
      if ignore:spec['ignore_taunt']=True
      enemy=dict(core_px=0,code=None,**{'def':0},patterns=[dict(id='observe',kind='attack',after=['start'],spec=spec)])
      with patch.dict(timeline._NIKKE,metadata),patch.dict(buff_manager._NIKKE,metadata),patch.object(buff_manager.BuffManager,'_register_all',register):
       result=timeline.simulate([dict(name=n,skill_levels={'1':10,'2':10,'3':10}) for n in NAMES],config=dict(duration=.05,rng_mode='expected',burst_gauge_mode='accumulate'),enemy=enemy,seed=19)
      hits=[vars(h) for h in result.squad_hits];selected=[NAMES.index(h['target']) for h in hits]
      if rule=='all':expected=list(range(5));assert selected==expected,(owner,effect_target,rule,ignore,selected,expected)
      elif not ignore:expected=[taunter];assert selected==expected,(owner,effect_target,rule,ignore,selected,expected)
      elif rule=='slot:2':expected=[1];assert selected==expected,(owner,effect_target,rule,ignore,selected,expected)
      elif rule=='top_atk:1':
       base=observed_bm[0].state['base_stats'];pool=[i for i in range(5) if i not in hidden] or list(range(5));expected=[max(pool,key=lambda i:base[NAMES[i]]['atk'])];assert selected==expected,(owner,effect_target,rule,selected,expected)
      else:
       assert timeline._EXPECTED_BOSS_SEED==0
       pool=[i for i in range(5) if i not in hidden] or list(range(5));expected=[pool[0] if len(pool)==1 else pool[3]];assert selected==expected,(owner,effect_target,rule,selected,expected)
      assert all(h['hp']>=0 and h['damage']>=1 for h in hits)
      rows.append(dict(owner=owner,stealth=stealth,effect_target=effect_target,rule=rule,ignore_taunt=ignore,expected_targets=expected,actual_targets=selected,hits=hits))
 paths=['research/characterize-taunt-boss-native.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']
 report=dict(passed=True,cpu_only=True,gpu_admission_enabled=False,gpu_execution_performed=False,cases=rows,requested_seed=19,effective_boss_seed=timeline._EXPECTED_BOSS_SEED,
  scope='420 original simulate/boss-attack cases,5 owners,3 effect targets,all/slot/top-attack/random with ignore_taunt. Stealth covers none/taunter/others/all-hidden fallback. Ignored top-attack uses base attack ranking;ignored random asserts fixed-seed0 first choice for each pool. No shared RNG implementation or multi-draw certification.',
  source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
 (ROOT/'research/portable-taunt-boss-native-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(rows),'original boss-attack target cases passed;GPU admission unchanged')
if __name__=='__main__':main()
