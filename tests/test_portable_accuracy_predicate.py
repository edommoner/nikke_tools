"""Shared predicate wire, raw fault coverage and exact GPU admission delta."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L


def adapter():
    spec=importlib.util.spec_from_file_location('accuracy_gpu_test',ROOT/'research/verify-world-accuracy-predicate-short.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class AccuracyPredicateTests(unittest.TestCase):
    def test_all_contracts_and_six_raw_faults_use_shared_wire(self):
        module=adapter();entries,data=module.prepare();self.assertEqual(len(entries),32)
        self.assertEqual(sum(row[2] is not None for row in entries),26)
        at=L['CONDITION_BASE']+2*L['CONDITION_WORDS']
        self.assertEqual(entries[1][1][at:at+2],[8,21])
        for name,words,domain in entries[-6:]:
            self.assertIsNone(domain);module.validate_rejection([64],name)
            with self.assertRaises(AssertionError):module.validate_rejection([0],name)
        self.assertEqual(len(data),4+sum(len(row[1])*4 for row in entries))

    def test_compiled_nonfinite_threshold_and_unknown_stat_are_rejected(self):
        module=adapter();case=module.fixtures()[1]
        for descriptor in ['self_stat_above:accuracy_pct:'+('9'*400),'self_stat_above:accuracy_pct:nan','self_stat_above:unknown:0']:
            import copy
            changed=copy.deepcopy(case);changed['effects'][-1]['trigger']['condition']=[descriptor]
            with self.subTest(descriptor=descriptor[:50]),self.assertRaises(ValueError):module.suite.compile_case(changed)


if __name__=='__main__':unittest.main()
