"""Independent native workloads cover common cache storage and query semantics."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_lazy_bank_cases import fixtures
from world_projectile_native import observe


class LazyBankTests(unittest.TestCase):
    def test_bank_entry_inherits_the_validated_output_stride(self):
        from portable_lazy_bank_specs import validate_output_stride,PROJECTILE_OUTPUT_WORDS,DIAGNOSTIC_WORDS
        from portable_specs import LIMITS as L
        # The only entry defining the bank must continue to inherit reload's
        # output stride; otherwise a valid bank could cross a program boundary.
        entry=ROOT/'gpu/world_projectile_entry.slang'
        self.assertIn('#define PORTABLE_WORLD_PROJECTILE\n',entry.read_text())
        self.assertIn('#include "world_roster_entry.slang"',entry.read_text())
        self.assertIn('#include "world_reload_entry.slang"',(ROOT/'gpu/world_roster_entry.slang').read_text())
        self.assertIn('#define PORTABLE_WORLD_RELOAD\n',(ROOT/'gpu/world_reload_entry.slang').read_text())
        owners=[p.name for p in (ROOT/'gpu').glob('*.slang')
                if '#define PORTABLE_WORLD_PROJECTILE\n' in p.read_text()]
        self.assertEqual(owners,['world_projectile_entry.slang'])
        validate_output_stride(L['WORLD_RELOAD_OUTPUT_WORDS'])
        self.assertLessEqual(L['LAZY_BANK_BASE']+L['LAZY_BANK_WORDS'],PROJECTILE_OUTPUT_WORDS-DIAGNOSTIC_WORDS)
        for stride in (655360,PROJECTILE_OUTPUT_WORDS-1,PROJECTILE_OUTPUT_WORDS+1):
            with self.assertRaisesRegex(ValueError,'output stride'):validate_output_stride(stride)

    def test_temporary_banks_are_disjoint_aligned_and_bounded_before_diagnostics(self):
        from portable_lazy_bank_specs import FIELDS,allocate
        from portable_specs import LIMITS as L
        occupied=set()
        for _,key,width in FIELDS:
            base=L['LAZY_BANK_'+key+'_BASE'];region=set(range(base,base+L['LAZY_CACHE']*width))
            self.assertFalse(occupied&region);occupied|=region
            if width==2:self.assertEqual(base%2,0)
        self.assertEqual(len(occupied)*4,24576)
        self.assertGreaterEqual(min(occupied),L['SKILL_CRITICAL_STATE_BASE']+L['SKILL_CRITICAL_STATE_WORDS'])
        self.assertLess(max(occupied),786416)
        enlarged=dict(L,LAZY_CACHE=L['LAZY_CACHE']*5)
        with self.assertRaisesRegex(ValueError,'overlaps'):allocate(enlarged)

    def test_native_stress_finishes_and_retains_all_physical_packets(self):
        for case in fixtures()[4:]:
            before=copy.deepcopy(case);battle,trace=observe(case)
            self.assertEqual(case,before);self.assertEqual(trace,[])
            self.assertGreater(battle['shots'][0],120)
            self.assertLessEqual(len(battle['projectile_shots']),2048)
            self.assertTrue(all(not a['down'] for a in battle['allies']))

    def test_literal_inputs_do_not_execute_cpu_battle_or_gpu(self):
        import portable_backend
        from calculator import timeline
        spec=importlib.util.spec_from_file_location('bank_adapter',ROOT/'research/verify-world-lazy-bank-short.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        def forbidden(*args,**kwargs):raise AssertionError('Execution forbidden during input packing')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,raw=module.prepare()
        self.assertEqual(len(entries),8);self.assertEqual(int.from_bytes(raw[:4],'little'),8)
        self.assertEqual(sum(r[2] is not None for r in entries),7)


if __name__=='__main__':unittest.main()
