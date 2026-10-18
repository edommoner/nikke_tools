"""Independent CPU-oracle checks for pellet/muzzle/clip and trigger budgets."""
import sys,copy,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run,evaluate_full
from gpu_selector import Cuda,probe
from detail_coverage import a,body_for
spec=importlib.util.spec_from_file_location('weapon_oracle',ROOT/'scripts/verify-detail.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
class DetailedWeaponTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=probe()
  if not p['available']:raise unittest.SkipTest(p['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def shooting(self,owner,effects,seconds=40,core=17):
  names=[owner]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=owner][:4]
  chars=oracle.characters(names);p=oracle.program(chars,[(e,owner) for e in effects]);bs={n:{'atk':100000+i*1234,'def':1000,'hp':1000000} for i,n in enumerate(names)}
  script=[[0,0,0,0,0,-1,0,0]]
  for frame in range(seconds*60):
   t=frame/60;script.extend([[t,3,0,0,0,-1,0,0],[t,2,0,0,-1,frame,0,0]])
  cpu,totals=oracle.oracle(p,script,[31784,core],bs,startup_full=True);gpu=run(self.device,[p],script,[[31784,core]],[bs])
  for index,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
   for k in (38,44,45,46,47):self.assertEqual(x[k],y[k],(owner,index,k,x[k],y[k]))
  self.assertEqual(totals,gpu['totals'][0])
  return gpu
 def effect(self,name,stat,value,event='battle_start',**kw):
  return {'source':'스킬1','name':name,'type':'buff','stat':stat,'target':'self','fixed_value':value,'trigger':{'timing':[event],'condition':[]},**kw}
 def test_ten_pellets_and_four_rounded_clips_match_every_frame(self):
  effects=[self.effect('31 rounds','max_ammo_flat',22),self.effect('changed ratio','reload_ratio_pct',-25)]
  self.shooting('드레이크',effects)
 def test_dual_muzzles_hit_count_is_twice_the_attack_count(self):
  effects=[self.effect('attack buff','atk_pct',7,'on_attack_count:10',max_stack=3,duration=2),self.effect('hit buff','atk_dmg_pct',11,'hit_count:10',max_stack=2,duration=1)]
  self.shooting('크로우',effects)
 def test_pellet_callbacks_use_original_shot_snapshot(self):
  effects=[self.effect('pellet buff','atk_pct',25,'pellet_hit_count:3',duration=1),self.effect('crit buff','atk_dmg_pct',13,'crit_hit_count:3',duration=2),self.effect('core buff','normal_atk_dmg_pct',17,'core_hit_count:3',duration=2),self.effect('one shot threshold','crit_dmg',50,'pellet_hit_in_shot:10',duration=1)]
  self.shooting('메어리',effects)
 def test_last_fire_precedes_damage_and_pellet_modifiers_match_cpu(self):
  effects=[self.effect('last shot','atk_dmg_pct',99,'last_bullet_fire',duration=1),self.effect('extra pellets','pellet_count',3),self.effect('limited effect','atk_pct',7,'on_attack_count:1',max_stack=20,max_trigger=3,duration=-1)]
  self.shooting('프로덕트 23',effects)
 def test_max_trigger_budget_is_shared_by_burst_target_instances(self):
  from calculator import buff_manager,timeline
  Original=buff_manager.BuffManager
  class Limited(Original):
   def char_effects(self,n):
    effects=super().char_effects(n)
    return [{**e,'max_trigger':1} if n=='크라운' and e.get('name')=='원 포 올' else e for e in effects]
  buff_manager.BuffManager=timeline.BuffManager=Limited
  try:
   b=body_for(['리타','크라운','앨리스','모더니아','N102'],60,True)
   gpu=evaluate_full(self.device,a.evaluate({**b,'_compile_gpu_detail':True}));cpu=a.evaluate(b)
   for key in ('total_damage','members','base_stats','burst_timeline'):self.assertEqual(gpu[key],cpu[key],key)
  finally:buff_manager.BuffManager=timeline.BuffManager=Original
if __name__=='__main__':unittest.main()
