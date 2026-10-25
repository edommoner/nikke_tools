"""Native lifecycle witnesses and exact shared-source boundary checks."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('healing_test_adapter',ROOT/'research/verify-coordinate-healing-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class HealingTests(unittest.TestCase):
    def native(self,label):
        c=next(x for x in a.fixtures() if x['name'].endswith('/'+label));w,m,b,d=a.compile_case(c)
        before=sys.getprofile();n=a.native_reference((c,m,b,d));self.assertIs(sys.getprofile(),before);return c,n
    def test_input_is_literal_and_never_runs_battle(self):
        from calculator import timeline
        cases=a.fixtures();before=copy.deepcopy(cases)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule')):
            for c in cases:self.assertEqual(len(a.compile_case(c)[0]),a.INPUT_WORDS)
        self.assertEqual(cases,before)
    def test_real_pool_is_capped_then_released_once_in_lifecycle_order(self):
        _,n=self.native('pool-discharge');events=n['healing_charge']['events']
        take=[e for e in events if e['kind']=='take'];self.assertEqual(len(take),1);self.assertEqual(take[0]['value'],3000.)
        self.assertTrue(any(e['kind']=='latch_end' for e in events));self.assertEqual(n['healing_charge']['final'],[])
        self.assertEqual(a.charge.expected_trace(events)[-1][0],3)
    def test_active_pool_and_cover_repair_are_independently_observed(self):
        _,n=self.native('pool-still-active');p=n['healing_charge']['final'];self.assertEqual(len(p),1)
        self.assertTrue(p[0]['active']);self.assertEqual(p[0]['current'],3000.)
        _,n=self.native('cover-repair-no-deposit');self.assertTrue(all(e['amount']==0 for e in n['healing_charge']['events'] if e['kind']=='collect'))
        self.assertEqual([e['value'] for e in n['healing_charge']['events'] if e['kind']=='take'],[0.])
    def test_storage_and_actor_delivery_observation_is_not_a_cpu_packet_input(self):
        _,n=self.native('mixed-actors-store');self.assertGreater(len(n['landed_packets']),10)
        adds=[p for p in n['landed_packets'] if p['target'].startswith('__enemy__:healing-adds#')]
        self.assertEqual({p['target'] for p in adds},{'__enemy__:healing-adds#1','__enemy__:healing-adds#2'},'Actual implicit ADD recipients must not become BODY')
        self.assertEqual(sum(p['damage'] for p in n['landed_packets'] if not p['target'] or p['target']=='front'),n['battle']['damage'][0])
        self.assertIn('healing_storage',n['battle']);self.assertTrue(n['healing_charge']['events'])
    def test_exact_source_inverse_and_registered_wire_reject_tampering(self):
        from portable_coordinate_healing_source_contract import project_sources
        from portable_backend import validate_composed_stride
        golden=json.loads((ROOT/'research/portable-coordinate-auto-reload-short-expected.json').read_text())
        for name,text in project_sources(ROOT).items():self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),golden['source_sha256'][name])
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
        path='gpu/coordinate_sampling_runtime.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{path:(ROOT/path).read_text()+'\n'})

if __name__=='__main__':unittest.main()
