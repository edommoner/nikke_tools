import json,random,sys,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import engine_worker as adapter
from gpu_combat import Combat,CS,ES,ME,prefilter,STAT
from gpu_selector import Cuda,probe
from calculator.damage import calc_damage,default_hit_type
from calculator.timeline import _core_hit_prob,_ACC_SLOPE_RATIO

class CombatTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda();cls.combat=Combat(cls.device)
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def basic(self,duration=1):
  return {'chars':([100,100,10,1,1,1,1,0,0,100,1,1,200,0,0,0,0,20,2,0]+[0]*24)*5,'effects':[],'enemy':[duration,0,0,0,0],'names':[str(i) for i in range(5)]}
 def test_damage_matches_pinned_formula_with_random_growth_buffs_and_enemy(self):
  rng=random.Random(90);models=[];expected=[]
  for n in range(120):
   m=self.basic(1/60);buff={}
   for i,name in enumerate(STAT):
    value=rng.uniform(0,40)
    if name=='enemy_def_down_pct':value=-value
    m['effects'].append([0,31,i,0,0,0,value,-1,1,0,0,1]);buff[name]=value
   a=m['chars'];a[0]=rng.uniform(1000,100000);a[1]=rng.uniform(.5,300);a[14]=n%2;a[15]=n%3==0
   a[13]=rng.uniform(10,100);m['enemy'][2]=rng.uniform(0,60)
   charged=n%2==0
   if charged:a[7]=.001;a[9]=rng.uniform(100,500);m['enemy'][0]=2/60
   for i in range(1,5):a[i*CS:(i+1)*CS]=a[:CS]
   m['enemy'][1]=rng.uniform(0,30000)
   weapon={'damage_coeff':a[1],'core_dmg_mult':200,'full_charge_mult':a[9]}
   buff['crit_rate']=.15+(buff['crit_rate']+buff['normal_atk_crit_rate'])/100
   buff['crit_dmg']+=buff['normal_atk_crit_dmg'];buff['element_bonus_pct']=buff['element_bonus'];buff['received_dmg']=buff['received_dmg_pct'];buff['is_element_match']=bool(a[15])
   result=calc_damage(a[0],buff,weapon,default_hit_type(coeff=None,is_normal_atk=True,is_optimal_range=bool(a[14]),is_full_charge=charged,core_prob=_core_hit_prob(a[13]*(1-_ACC_SLOPE_RATIO*buff['accuracy_pct']),m['enemy'][2])),enemy_def=m['enemy'][1],expected=True)
   expected.append(result['damage']*5);models.append(m)
  actual=self.combat.run(models)
  self.assertEqual([s['damage'] for s in actual['scores']],expected)
 def test_timeline_reload_periodic_damage_stacks_and_expiry(self):
  m=self.basic(5)
  # 2-round magazine, 2 shots/sec; reload adds 1 sec: 0,.5,2,2.5,4,4.5.
  for i in range(5):m['chars'][i*CS+2]=2;m['chars'][i*CS+4]=2;m['chars'][i*CS+5]=2
  s=self.combat.run([m])['scores'][0]
  self.assertEqual(s['shots'],30);self.assertEqual(s['damage'],30*108)
  m=self.basic(5);m['effects']=[[0,31,0,0,4,1,100,1.5,2,0,0,1],[0,31,0,1,4,1,100,0,1,0,0,1]]
  s=self.combat.run([m])['scores'][0]
  # Owner deals a periodic hit each second; buff stacks refresh duration.
  self.assertEqual(s['members'],[2470,1289,1289,1289,1289])
 def test_burst_owner_cooldown_and_mast_third_cycle(self):
  m=self.basic(55)
  for i,stage in enumerate([1,2,3,2,3]):m['chars'][i*CS+16]=stage;m['chars'][i*CS+17]=20
  # Distinct owners' burst damage proves events aren't restricted to position 1.
  m['effects']=[[i,31,0,1,3,0,100,0,1,0,1,1] for i in range(5)]
  s=self.combat.run([m])['scores'][0];self.assertEqual(s['cycles'],3)
  self.assertGreater(s['members'][1],s['members'][3])
  m['enemy'][4]=2 # Position 2 allowed only every third cycle, position 4 replaces it.
  s=self.combat.run([m])['scores'][0]
  self.assertGreater(s['members'][3],s['members'][1])
 def test_preparation_never_executes_cpu_combat_and_reports_omissions(self):
  profile=adapter.demo()['profile'];squad=list(profile['chars'])[:5]
  with patch.object(adapter.sim,'execute',side_effect=AssertionError('CPU combat must not run')):
   result=prefilter({'evaluation':{'profile':profile,'duration':1,'level':400},'squads':[squad]},self.device,self.combat)
  self.assertTrue(result['approximate']);self.assertEqual(len(result['scores']),1);self.assertTrue(result['issues'])
  self.assertTrue(any('weapon' in i['reason'] or '未対応' in i['reason'] for i in result['issues']))
 def test_growth_equipment_and_cube_buffs_are_compiled(self):
  profile=adapter.demo()['profile'];squad=list(profile['chars'])[:5]
  m=adapter.evaluate({'profile':profile,'squad':squad,'duration':1,'_compile_gpu':True})
  for stat in ('atk_pct','element_bonus','max_ammo_pct','reload_speed_pct','normal_atk_dmg_pct'):
   self.assertTrue(any(r[2]==STAT[stat] and r[6]>0 for r in m['effects']) or any(m['chars'][i*CS+20+STAT[stat]]>0 for i in range(5)),stat)
  self.assertTrue(all(r[7] is not None for r in m['effects']))
  # Ally received-damage reduction must never multiply outgoing damage.
  self.assertTrue(all(r[2]!=STAT['received_dmg_pct'] or r[1]==31 for r in m['effects']))
 def test_checked_in_kernel_matches_build_manifest(self):
  directory=Path(__file__).resolve().parents[1]/'app'
  manifest=json.loads((directory/'combat-build.json').read_text())
  for file,key in [('combat.cu','source_sha256'),('combat.ptx','ptx_sha256')]:
   self.assertEqual(hashlib.sha256((directory/file).read_bytes()).hexdigest(),manifest[key])
 def test_invalid_layout_is_rejected_before_launch(self):
  m=self.basic();m['effects']=[[0,31,0,0,5,0,1,-1,1,0,0,1]]
  with self.assertRaises(ValueError):self.combat.run([m])

if __name__=='__main__':unittest.main()
