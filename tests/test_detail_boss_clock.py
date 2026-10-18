"""Independent boss lifecycle, bytecode rejection and context recovery."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('boss_clock_tests',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_boss import validate_world,validate_patterns,WP,WB
from gpu_service import resolve_verification

class BossClockInputTests(unittest.TestCase):
 def test_all_worlds_compile_without_running_cpu_combat(self):
  with patch.object(v.a.sim,'execute',side_effect=AssertionError('CPU combat invoked')):
   for name,body,extra in v.fixtures():
    saved=copy.deepcopy(body)
    with v.t.raw.injected_effects(extra):c=v.a.evaluate({**body,'_compile_gpu_detail':True})
    validate_world(c['program']['world']);self.assertEqual(body,saved,name)
 def test_malformed_patterns_and_packets_are_rejected_before_cuda(self):
  for patterns in [None,[{'id':'x','kind':'core','core_px':-1}], [{'id':'x','kind':'move','distance':1,'after':['missing']}]]:
   with self.assertRaises(ValueError):validate_patterns(patterns)
  name,body,extra=next(v.fixtures())
  with v.t.raw.injected_effects(extra):c=v.a.evaluate({**body,'_compile_gpu_detail':True})
  for index,value in [(0,33),(1,float('nan')),(WB+4,9),(WB+12,33),(WB+7,3)]:
   p=copy.deepcopy(c['program']);p['world'][index]=value
   with self.assertRaises(ValueError):v.g.run(None,[p],[],[c['enemy']],[c['base_stats']])
  with self.assertRaises(v.g.UnsupportedDetail):v.g.run(None,[c['program']],[[0,4,0,0,0,-1,0,0]],[c['enemy']],[c['base_stats']])
 def test_matching_totals_do_not_hide_a_wrong_boss_timeline(self):
  cpu=dict(total_damage=1,members=[],base_stats={},burst_timeline=[],boss_patterns=[],boss_timeline=[{'event':'end'}])
  gpu={**copy.deepcopy(cpu),'boss_timeline':[{'event':'start'}],'compute':{'backend':'cuda_detail'}}
  result=resolve_verification(gpu,cpu)
  self.assertEqual(result['compute']['backend'],'cpu');self.assertFalse(result['compute']['cpu_verification']['boss_timeline_equal'])

class BossClockGPUTests(unittest.TestCase):
 def test_complete_squads_match_cpu_with_live_worlds(self):
  d=v.Cuda()
  from calculator.timeline import CharState
  original=CharState._tick_weapon_change;mode_ticks=[]
  def observed(self,*args,**kwargs):
   mode_ticks.append(self.name);return original(self,*args,**kwargs)
  try:
   rows=[v.compare(d,n,b,e,'native') for n,b,e in list(v.fixtures(quick=True))[:2]]
   n,b,e=list(v.fixtures())[13]
   with patch.object(CharState,'_tick_weapon_change',observed):rows.append(v.compare(d,n,b,e,'native'))
  finally:d.close()
  self.assertTrue(all(r['passed'] for r in rows));self.assertTrue(mode_ticks,'Weapon-mode positive control did not fire')
 def test_distinct_worlds_are_isolated_in_one_concurrent_launch(self):
  fixtures=list(v.fixtures())[:6];compiled=[];cpu=[]
  for n,b,e in fixtures:
   with v.t.raw.injected_effects(e):
    compiled.append(v.a.evaluate({**b,'_compile_gpu_detail':True}));cpu.append(v.a.evaluate(b))
  script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[0,0,5,i,0,-1,0,0] for i in range(5)]
  at=0.
  while at<=12:script.append([at,4,0,0,0,-1,0,0]);at+=1/60
  script.extend([[12,5,0,0,0,-1,0,0],[12,2,101,0,0,0,0,0]]);d=v.Cuda()
  try:result=v.g.run(d,[c['program'] for c in compiled],script,[c['enemy'] for c in compiled],[c['base_stats'] for c in compiled],module_backend='native',seeds=[12345]*len(compiled))
  finally:d.close()
  for i,c in enumerate(cpu):self.assertEqual(round(sum(result['totals'][i])),c['total_damage'],fixtures[i][0])
 def test_history_overflow_rejects_result_and_context_recovers(self):
  b=v.body_for(v.NAMES,20,True);b['enemy']['patterns']=[v.pattern('fast','idle',0,.001,after=['start','fast'],repeat=0)]
  c=v.a.evaluate({**b,'_compile_gpu_detail':True});d=v.Cuda()
  try:
   with self.assertRaisesRegex(RuntimeError,r'\[8\]'):v.g.evaluate_full(d,c,module_backend='native')
   n,b,e=next(v.fixtures());self.assertTrue(v.compare(d,n,b,e,'native')['passed'])
  finally:d.close()
if __name__=='__main__':unittest.main()
