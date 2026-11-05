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
if __name__=='__main__':unittest.main()
