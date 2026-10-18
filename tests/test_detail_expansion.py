import copy,importlib.util,json,sys,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'));sys.path.insert(0,str(ROOT/'scripts'))
from gpu_selector import Cuda,probe
from detail_gpu import compile_effects,run,evaluate_full
from detail_coverage import body_for,a,coverage
spec=importlib.util.spec_from_file_location('expanded_verifier',ROOT/'scripts/verify-extended-detail.py');expanded=importlib.util.module_from_spec(spec);spec.loader.exec_module(expanded)
spec=importlib.util.spec_from_file_location('expanded_effect_oracle',ROOT/'scripts/verify-detail.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
class ExpandedDetailedGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_new_complete_real_squads_and_health_transitions_match_cpu(self):
  report=expanded.verify(self.device,include_coverage=False)
  self.assertTrue(report['passed'],json.dumps([c for c in report['cases'] if not c['passed']],ensure_ascii=True))
  health=next(c for c in report['cases'] if c['name'].startswith('hp-threshold'))
  self.assertTrue(all(health['observed_cpu_conditions'].values()),health['observed_cpu_conditions'])
  crown=[c for c in report['cases'] if c['name'].startswith('crown-')];self.assertEqual(len(crown),4);self.assertTrue(all(c['crown_conditions_exercised'] for c in crown));self.assertTrue(next(c for c in crown if c['name'].startswith('crown-charge'))['automatic_reload_exercised'])
  self.assertGreaterEqual(report['compile_coverage_after'],24);self.assertGreater(report['compile_coverage_after'],report['compile_coverage_before'])
 def test_lazy_rank_refresh_holds_recipients_until_expiry(self):
  cs=oracle.characters(['모더니아','마스트 : 로망틱 메이드','리타','크라운','앨리스']);owner=cs[0]['name']
  effect={'source':'스킬1','type':'buff','name':'ranked bonus','stat':'atk_dmg_pct','target':'allies_top_atk:1','fixed_value':25,'duration':5,'trigger':{'timing':['hit_count:1'],'condition':[]}}
  late={'source':'스킬3','type':'buff','name':'ranking changes','stat':'atk_pct','target':'self','fixed_value':200,'duration':20,'trigger':{'timing':['burst_cast'],'condition':[]}}
  p=oracle.program(cs,[(effect,owner),(late,owner)]);stats={c['name']:{'atk':100000+i*10000,'def':1000,'hp':1000000} for i,c in enumerate(cs)}
  script=[[0,0,8,0,0,-1,0,0],[0,2,0,4,-1,0,0,0],[1,0,3,0,0,-1,0,0],[2,0,8,0,0,-1,0,0],[2,2,0,4,-1,1,0,0],[2,2,0,0,-1,2,0,0],[8,1,0,0,0,-1,0,0],[8,0,8,0,0,-1,0,0],[8,2,0,0,-1,3,0,0]]
  expected,totals=oracle.oracle(p,script,[31784,50],stats);actual=run(self.device,[p],script,[[31784,50]],[stats])
  self.assertEqual([r[10] for r in expected],[25,25,0,25]);self.assertEqual([r[10] for r in expected],[r[10] for r in actual['queries'][0]])
  self.assertEqual([r[36] for r in expected],[r[36] for r in actual['queries'][0]])
 def test_b3_landing_excludes_later_cast_buffs_and_zero_coeff_is_no_hit(self):
  import calculator.buff_manager as buff_module
  from calculator import timeline
  Original=buff_module.BuffManager
  body=body_for(['모더니아','루주','마스트 : 로망틱 메이드','도라','앨리스'],8)
  totals=[]
  for coeff in (100,0):
   extra=[{'source':'스킬3','type':'damage','name':'deferred test hit','stat':'bonus_damage','target':'target','fixed_value':coeff,'trigger':{'timing':['burst_cast'],'condition':[]}}, {'source':'스킬3','type':'buff','name':'after deferred test hit','stat':'atk_pct','target':'self','fixed_value':200,'duration':10,'trigger':{'timing':['burst_cast'],'condition':[]}}]
   class Custom(Original):
    def char_effects(self,name):return super().char_effects(name)+(extra if name=='모더니아' else [])
   buff_module.BuffManager=timeline.BuffManager=Custom
   try:
    compiled=a.evaluate({**body,'_compile_gpu_detail':True});deferred=[r for r in compiled['program']['effects'] if r[51]]
    self.assertTrue(deferred);self.assertTrue(any(any(r[52:56]) for r in deferred))
    gpu=evaluate_full(self.device,compiled);cpu=a.evaluate(body)
    for k in ('total_damage','members','burst_timeline','base_stats'):self.assertEqual(gpu[k],cpu[k],k)
    totals.append(gpu['total_damage'])
   finally:buff_module.BuffManager=timeline.BuffManager=Original
  self.assertGreater(totals[0],totals[1])
 def test_normal_worker_runs_new_liter_alice_squad_on_gpu(self):
  body=body_for(['리타','마스트 : 로망틱 메이드','앨리스','모더니아','N102'],8,True);body.update(action='evaluate_detail',verify_detail=True)
  process=subprocess.Popen([sys.executable,str(ROOT/'app/gpu_service.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',cwd=ROOT)
  try:
   process.stdin.write(json.dumps({'id':'new-squad','body':body})+'\n');process.stdin.flush();reply=json.loads(process.stdout.readline())
   self.assertNotIn('error',reply,reply);self.assertEqual(reply['result']['compute']['backend'],'cuda_detail');self.assertTrue(reply['result']['compute']['cpu_verification']['matched']);self.assertEqual(len(reply['result']['compute']['final_hp']),5)
  finally:
   process.stdin.close();process.wait(timeout=30);process.stdout.close();process.stderr.close()
 def test_ordered_healing_notifies_before_next_recipient(self):
  import calculator.buff_manager as buff_module
  from calculator import timeline
  Original=buff_module.BuffManager
  body=body_for(['리타','크라운','모더니아','마스트 : 로망틱 메이드','앨리스'],12)
  def effect(name,kind,stat,target,value,event,**extra):
   return {'source':'스킬3','name':name,'type':kind,'stat':stat,'target':target,'fixed_value':value,'trigger':{'timing':[event],'condition':[]},**extra}
  extra=[effect('missing hp','buff','max_hp_only_pct','all_allies',100,'battle_start'),
         effect('ordered heal','instant','heal_hp_pct','allies_adjacent:2',5,'burst_cast',scaling='max_hp'),
         effect('heal changes next base','buff','max_hp_only_pct','self',100,'event:heal_received')]
  class Custom(Original):
   def char_effects(self,name):return super().char_effects(name)+(extra if name=='모더니아' else [])
  buff_module.BuffManager=timeline.BuffManager=Custom
  try:
   result=expanded.compare(self.device,'ordered-healing',body)
   self.assertTrue(result['passed'],result)
   health=result['gpu_health'];self.assertGreater(health['마스트 : 로망틱 메이드']['hp_pct'],50)
  finally:buff_module.BuffManager=timeline.BuffManager=Original

 def test_pinned_enemy_debuff_routing_matches_cpu(self):
  cs=oracle.characters(['모더니아','마스트 : 로망틱 메이드','리타','크라운','앨리스']);owner=cs[0]['name']
  e={'source':'스킬1','type':'buff','name':'enemy atk down compatibility','stat':'atk_pct','target':'target','fixed_value':-30,'duration':-1,'trigger':{'timing':['battle_start'],'condition':[]}}
  p=oracle.program(cs,[(e,owner)]);stats={c['name']:{'atk':100000,'def':1000,'hp':1000000} for c in cs};script=[[0,0,0,0,0,-1,0,0],[0,2,0,1,-1,0,0,0]]
  cpu,_=oracle.oracle(p,script,[31784,50],stats);gpu=run(self.device,[p],script,[[31784,50]],[stats])
  self.assertEqual(cpu[0][0],-30);self.assertEqual(cpu[0][0],gpu['queries'][0][0][0]);self.assertEqual(cpu[0][36],gpu['queries'][0][0][36])
if __name__=='__main__':unittest.main()
