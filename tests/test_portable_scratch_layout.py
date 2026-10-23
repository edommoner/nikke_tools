"""Maximum-capacity ownership and relocation guards, including literal banks."""
import copy, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L
from portable_scratch_layout import verify, audit_sources
from portable_scratch_layout_source_contract import ledger,project_sources


class ScratchLayoutTests(unittest.TestCase):
    def test_all_concurrent_banks_are_disjoint_without_capacity_or_stride_loss(self):
        report=audit_sources(ROOT,L)
        self.assertTrue(report['verified'])
        self.assertEqual((L['WORLD_RELOAD_OUTPUT_WORDS'],L['NATIVE_QUERY_COUNT'],L['FOCUS_CACHE_COUNT'],L['LANDINGS']),(786432,64,256,2048))
        self.assertEqual(L['NATIVE_QUERY_WORDS'],8736)
        for r in report['modes']:
            self.assertTrue(all(a['end']<=b['base'] for a,b in zip(r['banks'],r['banks'][1:])))

    def test_previous_allocations_reproduce_the_actual_overlaps(self):
        previous=dict(L,FOCUS_STATE_BASE=770976,NATIVE_QUERY_BASE=773056,
                      NATIVE_QUERY_BANK0_BASE=773088,NATIVE_QUERY_BANK1_BASE=777440,
                      ORDERED_HISTORY_BASE=781792,NATIVE_DIAG_BASE=781856)
        for mode in ('normal','native-query-diagnostic','heal-share-diagnostic'):
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'overlap'):
                verify(previous,mode=mode)

    def test_one_word_boundary_overrun_and_missing_mode_guard_are_rejected(self):
        for field,value in (('NATIVE_QUERY_BANK0_BASE',249601),('NATIVE_QUERY_BANK1_BASE',519937),
                            ('FOCUS_STATE_BASE',260049),('NATIVE_QUERY_BASE',786385),
                            ('NATIVE_QUERY_CELL_WORDS',135),('FOCUS_STATE_WORDS',2079),
                            ('NATIVE_QUERY_COUNT',32),('LANDINGS',2047)):
            changed=dict(L);changed[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):verify(changed)
        for name,old,new in [('gpu/skill_part_receipt.slang','781328','781320'),
                             ('gpu/world_interrupt_runtime.slang','785424','785416'),
                             ('gpu/native_query_diagnostic.slang','&& defined(PORTABLE_HEAL_SHARE_DIAGNOSTIC)','&& 0')]:
            text=(ROOT/name).read_text();self.assertIn(old,text)
            with self.assertRaises(ValueError):audit_sources(ROOT,L,sources={name:text.replace(old,new,1)})

    def test_whole_output_oracle_detects_late_cells_and_unallocated_writes(self):
        import importlib.util, array
        spec=importlib.util.spec_from_file_location('scratch_probe_test',ROOT/'research/verify-scratch-layout-short.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        entries,data=m.prepare();self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(8,6))
        for case in m.CASES[:6]:
            block=m.expected(case);self.assertFalse(m.compare(block,case)['battle_certified'])
        case=m.CASES[0];block=m.expected(case)
        for at in (0,258576+2079,248600+4351,518336+4351,781328+4095,785424+9,785440+31,785472+63,253951):
            changed=array.array('I',block);changed[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):m.compare(changed,case)

    def test_all_relocation_deltas_are_exact_and_faults_rejected(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for c in row['changes']:
                self.assertEqual(text.count(c['current']),1)
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    project_sources(ROOT,{name:text.replace(c['current'],c['baseline'],1)})


if __name__=='__main__':unittest.main()
