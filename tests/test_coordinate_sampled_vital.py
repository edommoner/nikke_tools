"""Sampled mode arithmetic and health callbacks retain native semantics."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampled_vital_cases import fixtures
from world_coordinate_sampled_vital_native import observe
from portable_coordinate_sampled_vital_contracts import verify
spec=importlib.util.spec_from_file_location('vital_test_adapter',ROOT/'research/verify-coordinate-sampled-vital-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class VitalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers={c['name'].rsplit('/',1)[1]:observe(c)[0] for c in cls.cases}
    def test_real_contracts_and_immutable_inputs(self):
        self.assertEqual(len(self.cases),29);self.assertEqual(self.cases,self.before)
        for c in self.cases:self.assertTrue(verify(c,self.answers[c['name'].rsplit('/',1)[1]])['verified'])
    def test_first_coefficient_and_exhaustion_are_actual_live_modes(self):
        modes=[s for s in self.answers['mode-first-coefficient']['sampled_live_shots'] if s['mode']];self.assertEqual([s['coefficient'] for s in modes],[277,123,123,123,123])
        self.assertEqual(sum(s['mode'] for s in self.answers['mode-bullet-exhaustion']['sampled_live_shots']),2)
        self.assertFalse(any(s['mode'] for s in self.answers['mode-expired-before-entry']['sampled_live_shots']))
    def test_live_muzzles_are_used_for_parent_quantity(self):
        n=self.answers['mode-charge-parent'];notices=n['full_charge_quantities'];self.assertTrue(notices);self.assertTrue(any(r['muzzles']==2 for r in notices))
        self.assertTrue(any(p['skill_name']=='parent' for p in n['landed_packets']))
    def test_heal_bounds_and_recipient_bonus(self):
        for name,value in [('heal-self',8000),('heal-overflow',10000),('heal-negative',0)]:self.assertEqual(self.answers[name]['battle']['allies'][0]['hp'],value)
        self.assertEqual([a['hp'] for a in self.answers['heal-received-bonus']['battle']['allies']],[10000]*4+[20000])
    def test_cover_repair_and_broken_cover_are_distinct(self):
        self.assertGreater(self.answers['cover-repair']['battle']['covers'][0]['hp'],500)
        self.assertEqual(self.answers['cover-broken-no-revive']['battle']['covers'][0]['hp'],0)
    def test_heal_notification_and_lifesteal_affect_actual_battle(self):
        witness=self.answers['heal-notification-child']['battle'];baseline=self.answers['heal-self']['battle'];self.assertGreater(witness['damage'][0],baseline['damage'][0])
        self.assertGreater(self.answers['lifesteal-packets']['battle']['allies'][0]['hp'],2000)
    def test_old89_inputs_and_full_wire_are_unchanged(self):
        rows,_=a.prepare();old,_=a.parent.prepare();self.assertEqual(rows[:89],old);self.assertEqual((len(rows),sum(x[2] is not None for x in rows)),(120,112))
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        for source,i,o in [(a.SOURCE,a.INPUT_WORDS,1507328),(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS),('gpu/world_coordinate_sampling_skill_entry.slang',a.INPUT_WORDS,a.OUTPUT_WORDS)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,i,o)
    def test_strict_inverse_rejects_unknown_source_or_transport(self):
        from portable_coordinate_sampled_vital_source_contract import project_sources,project_backend_source
        from portable_coordinate_manual_source_contract import project_sources as manual_sources,project_backend_source as manual_backend
        project_sources(ROOT,manual_sources(ROOT));project_backend_source(ROOT,manual_backend(ROOT))
        for name in ('gpu/coordinate_sampling_runtime.slang','gpu/world_coordinate_sampling_vital_entry.slang'):
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// changed\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n')
if __name__=='__main__':unittest.main()
