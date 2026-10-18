import copy,hashlib,importlib.util,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from gpu_selector import Cuda,probe
from detail_gpu import compile_effects,UnsupportedDetail,run
spec=importlib.util.spec_from_file_location('detail_oracle',ROOT/'scripts/verify-detail.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)

class DetailedGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_real_effects_and_180_second_autonomous_shooting_match_pinned_cpu(self):
  report=oracle.verify(self.device)
  self.assertTrue(report['passed'],json.dumps([c for c in report['cases'] if not c['matched']],ensure_ascii=True))
  self.assertTrue(all(c['total_damage_equal'] and c['individual_hit_damage_exact'] for c in report['cases']))
  autonomous=[c for c in report['cases'] if c['per_frame_checked']]
  self.assertEqual(len(autonomous),2);self.assertTrue(all(c['queries']==21600 and c['shot_counts_exact'] for c in autonomous))
 def test_parallel_scenarios_keep_growth_and_state_isolated(self):
  fixtures=oracle.cases()[:3];programs=[v[1] for v in fixtures];script=fixtures[0][2]
  stats=[{c['name']:{'atk':100000+i*1234+batch*10000,'def':1000,'hp':1000000} for i,c in enumerate(p['chars'])} for batch,p in enumerate(programs)]
  actual=run(self.device,programs,script,[[31784,50]]*3,stats)
  for i,p in enumerate(programs):
   expected,totals=oracle.oracle(p,script,[31784,50],stats[i])
   self.assertEqual(actual['totals'][i],totals)
   for cpu,gpu in zip(expected,actual['queries'][i]):
    self.assertEqual(cpu[36],gpu[36]);self.assertEqual(cpu[37],gpu[37]);self.assertAlmostEqual(cpu[1],gpu[1],places=8)
  self.assertNotEqual(actual['queries'][0][2][36],actual['queries'][2][2][36])
 def test_workspace_isolated_across_warps_and_reinitialized_on_reuse(self):
  program,script=oracle.cases()[0][1:3]
  count=33
  stats=[{c['name']:{'atk':100000+batch*1777+i*1234,'def':1000,'hp':1000000+batch*100} for i,c in enumerate(program['chars'])} for batch in range(count)]
  expected=[oracle.oracle(program,script,[31784,50],bs) for bs in stats]
  for backend in ('native','ptx'):
   with self.subTest(backend=backend):
    before=len(self.device.buffers)
    actual=run(self.device,[program]*count,script,[[31784,50]]*count,stats,module_backend=backend)
    self.assertEqual(len(self.device.buffers),before)
    self.assertGreater(actual['workspace_bytes'],count*1024)
    for i,(cpu,totals) in enumerate(expected):
     self.assertEqual(actual['totals'][i],totals)
     for x,y in zip(cpu,actual['queries'][i]):
      for key in (36,37):self.assertEqual(x[key],y[key],(backend,i,key))
    again=run(self.device,[program],script,[[31784,50]],[stats[-1]],module_backend=backend)
    self.assertEqual(again['queries'][0],actual['queries'][-1])
    self.assertEqual(again['workspace_bytes']*count,actual['workspace_bytes'])
    self.assertEqual(len(self.device.buffers),before)

 def test_nested_stack_reach_damage_precedes_remove(self):
  chars=oracle.characters(['모더니아','마스트 : 로망틱 메이드','리타','크라운','앨리스']);owner=chars[0]['name']
  base={'source':'스킬1','trigger':{'timing':['hit_count:1'],'condition':[]},'target':'self','polarity':'beneficial'}
  a={**base,'name':'test charge','type':'buff','stat':'atk_pct','fixed_value':10,'max_stack':3,'duration':-1}
  b={**base,'name':'test release','type':'damage','stat':'bonus_damage','fixed_value':100,'target':'target','trigger':{'timing':['stack_reach:test charge:3'],'condition':[]}}
  remove={**b,'name':'test remove','type':'instant','stat':'remove_named_buff','target':'self','target_effect':'test charge'}
  # Remove the inherited damage value: an instant removal has no coefficient.
  remove.pop('fixed_value')
  p=oracle.program(chars,[(a,owner),(b,owner),(remove,owner)]);script=[]
  for i in range(10):script.extend([[i,0,8,0,0,-1,0,0],[i,2,0,0,p['states']['test charge'],i,0,0]])
  stats={c['name']:{'atk':100000,'def':1000,'hp':1000000} for c in chars}
  cpu,total=oracle.oracle(p,script,[31784,0],stats);gpu=run(self.device,[p],script,[[31784,0]],[stats])
  self.assertGreater(total[0],0);self.assertEqual(total,gpu['totals'][0])
  self.assertEqual([q[37] for q in gpu['queries'][0]],[1,2,0,1,2,0,1,2,0,1])
  self.assertEqual([q[36] for q in cpu],[q[36] for q in gpu['queries'][0]])
 def test_unsupported_semantics_and_invalid_programs_are_rejected(self):
  chars=oracle.characters(['모더니아','마스트 : 로망틱 메이드','리타','크라운','앨리스']);owner=chars[0]['name']
  e={'name':'unsupported','type':'buff','stat':'atk_pct','fixed_value':30,'target':'self','trigger':{'timing':['battle_start'],'condition':['new unknown condition']}}
  with self.assertRaises(UnsupportedDetail) as caught:compile_effects(chars,[(e,owner)])
  self.assertEqual(caught.exception.issues[0]['effect'],'unsupported')
  e['trigger']={'timing':['hit_count:not-a-count'],'condition':[]}
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(e,owner)])
  e['trigger']={'timing':['passive'],'condition':['self_state:other']};e['duration']=5
  # Time-based finite passives are now supported; bullet-bound passives still fail closed.
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[({**e,'duration_bullets':2},owner)])
  e['duration_values']={'10':5};e['scaling']='stack_count';e['scaling_ref']='other';e['duration_scaling']='unknown-duration'
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(e,owner)])
  p=compile_effects(chars,[]);stats={c['name']:{'atk':100000} for c in chars}
  with self.assertRaises(ValueError):run(self.device,[p],[[float('nan'),2,0,0,-1,0,0,0]],[[0,0]],[stats])
 def test_detail_source_and_ptx_are_consistent(self):
  manifest=json.loads((ROOT/'app/detail_effects-build.json').read_text())
  for file,key in [('detail_effects.cu','source_sha256'),('detail_effects.ptx','ptx_sha256')]:self.assertEqual(hashlib.sha256((ROOT/'app'/file).read_bytes()).hexdigest(),manifest[key])

if __name__=='__main__':unittest.main()
