"""Entry-reload packing and shared-native cases; GPU proof belongs to captures."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('entry_reload_gpu_suite',ROOT/'research/verify-world-entry-reload-short.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
from portable_specs import LIMITS as L
from portable_entry_reload_cases import fixtures


class EntryReloadGpuTests(unittest.TestCase):
    def test_explicit_policy_preserves_measured_zero_and_dynamic_base_reload(self):
        for case in fixtures():
            if 'cover-' in case['name']:continue
            words,_,_=suite.compile_case(case);index=len(case['effects'])-1;at=L['MODE_BASE']+index*L['MODE_WORDS']
            measured=case.get('entry_delays');mode=case['effects'][-1]
            policy=1 if measured else 2 if mode.get('entry_reload') else 0
            self.assertEqual(words[at+30],policy,case['name'])
            value=struct.unpack('<d',struct.pack('<II',*words[at+28:at+30]))[0]
            self.assertEqual(value,measured[0]['value'] if measured else 0)
            self.assertEqual(words[at+31],0)

    def test_dependency_on_cover_control_stays_explicit_and_bad_boolean_rejected(self):
        covered=[c for c in fixtures() if 'cover-' in c['name']];self.assertEqual(len(covered),4)
        for case in covered:
            with self.subTest(case['name']),self.assertRaisesRegex(ValueError,'Non-hold sequence'):suite.compile_case(case)
        for value in (1,'true',None):
            case=copy.deepcopy(fixtures()[0]);case['effects'][-1]['entry_reload']=value
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'boolean'):suite.compile_case(case)

    def test_shared_suite_has_all_currently_admissible_contracts_and_six_negatives(self):
        entries,data=suite.prepare();self.assertEqual(len(entries),37)
        self.assertEqual(sum(domain is not None for _,_,domain in entries),31)
        self.assertEqual(len(data),4+37*suite.suite.INPUT*4)
        case,_,_=entries[0][2];reference=suite.native_reference(entries[0][2])
        self.assertEqual(reference['entry_duration_queries'][0],dict(owner=0,time=0.,duration=.6))
        self.assertGreater(len(reference['entry_duration_queries']),50)
        self.assertEqual(reference['mode_entry_wait_until'],[-1.]*5)


if __name__=='__main__':unittest.main()
