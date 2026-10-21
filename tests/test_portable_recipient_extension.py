"""New host admission uses existing static-mask and cast-mask GPU selectors."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_recipient_specs import admitted
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
from portable_recipient_extension_cases import fixtures
from world_projectile_native import observe

class RecipientExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('recipient_test_suite',ROOT/'research/verify-world-recipients-short.py')
        cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)

    def test_catalog_names_and_b3_cast_selector_fail_closed_for_unknowns(self):
        self.assertTrue(admitted('N102'));self.assertTrue(admitted('프리카'))
        self.assertTrue(admitted('allies_burst_casted_burst3'))
        self.assertFalse(admitted('not-a-real-nikke'));self.assertFalse(admitted(None))
        with self.assertRaises(UnsupportedPortable):validate_effect(fixtures()[-1]['effects'][1])

    def test_present_absent_and_ordered_name_compiler_masks_are_canonical(self):
        cases=fixtures();before=copy.deepcopy(cases)
        a,_,_=self.adapter.suite.compile_case(cases[0]);b,_,_=self.adapter.suite.compile_case(cases[1])
        self.assertEqual(a[L['RECIPIENT_BASE']:L['RECIPIENT_BASE']+3],[8,0,16])
        self.assertEqual(b[L['RECIPIENT_BASE']:L['RECIPIENT_BASE']+3],[8,0,0])
        c,_,_=self.adapter.suite.compile_case(cases[2]);self.assertEqual(c[L['RECIPIENT_BASE']],17)
        self.assertEqual(cases,before)

    def test_b3_uses_existing_intersection_selector(self):
        words,_,_=self.adapter.suite.compile_case(fixtures()[-1]);at=L['RECIPIENT_BASE']+8
        self.assertEqual(words[at],11);self.assertTrue(words[at+2]&4);self.assertFalse(words[at+2]&3)

    def test_native_named_absence_and_cast_state_change_damage_only_where_selected(self):
        cases=fixtures();present=observe(cases[0])[0];absent=observe(cases[1])[0]
        self.assertGreater(present['damage'][4],absent['damage'][4])
        before=observe(cases[-2])[0];after=observe(cases[-1])[0]
        self.assertGreater(after['damage'][2],before['damage'][2])
        self.assertEqual(after['damage'][:2],before['damage'][:2]);self.assertEqual(after['damage'][3:],before['damage'][3:])

if __name__=='__main__':unittest.main()
