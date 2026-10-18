import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail
s=importlib.util.spec_from_file_location('chain_regression',ROOT/'scripts/verify-chains-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class NamedChainCompilerTests(unittest.TestCase):
 def compile(self,effects):return compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in effects])
 def test_marker_and_recipient_audience_are_compiled(self):
  p=self.compile([v.E('carrier','buff','',0,event_scope='recipients'),v.E('listener','buff','atk_pct',1,event='event:carrier')]);q=p['effects'][0]
  self.assertEqual(q[1],4);self.assertEqual(q[201],1);self.assertEqual(q[202],32);self.assertEqual(q[203],p['states']['carrier']);self.assertEqual(q[207],0)
 def test_nonexistent_named_listener_is_safe_and_unknown_scope_rejected(self):
  p=self.compile([v.E('wait','buff','atk_pct',1,event='event:future state')]);self.assertEqual(p['effects'][0][144],1)
  with self.assertRaises(UnsupportedDetail):self.compile([v.E('bad','buff','atk_pct',1,event_scope='nearby')])
 def test_recurrent_partial_instance_is_accepted(self):
  effects=[v.E('state','buff','atk_pct',10,'all_allies',event='on_attack'),v.E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='state',remove_scope='target')]
  self.assertEqual(len(self.compile(effects)['effects']),2)
class NamedChainGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from gpu_selector import Cuda,probe
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_named_order_and_complete_squads_match_cpu(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
 def test_name_callback_precedes_current_hp_gain(self):
  from calculator.buff_manager import BuffManager
  from unittest.mock import patch
  n=v.periodic.NAMES[0];events=[]
  effects={n:[v.E('room','buff','max_hp_only_pct',100),v.E('hp source','buff','max_hp_pct',100,event='burst_cast',duration=2),v.E('before hp witness','buff','atk_dmg_pct',70,event='event:hp source',condition=['self_hp_below:60'],duration=3)]}
  activate=BuffManager._activate
  def track(manager,eff,caster,t,**kw):
   if eff.get('name')=='before hp witness':events.append(('witness-before',manager.state['hp_pct'][caster]))
   result=activate(manager,eff,caster,t,**kw)
   if eff.get('name')=='hp source':events.append(('source-after',manager.state['hp_pct'][caster]))
   return result
  with v.periodic.custom_effects(effects),patch.object(BuffManager,'_activate',track):case=v.periodic.full.compare(self.device,'named-hp-order-gate',v.body_for(v.periodic.NAMES,8,True))
  self.assertTrue(case['passed'],case)
  self.assertEqual([value for label,value in events if label=='witness-before'],[50])
  self.assertTrue(any(label=='source-after' and value>60 for label,value in events),events)
if __name__=='__main__':unittest.main()
