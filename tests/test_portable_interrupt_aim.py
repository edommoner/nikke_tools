"""Admission and exact shared-source deltas for private interrupt landings."""
import array,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_interrupt_aim_source_contract import ledger,project_sources
from portable_interrupt_aim_trace import BASE,COUNT,MAGIC,gpu_records
from portable_scratch_layout import verify
from portable_specs import LIMITS


class InterruptAimGpuTests(unittest.TestCase):
    def test_all_native_contracts_pack_without_canonical_kind_aliases(self):
        spec=importlib.util.spec_from_file_location('interrupt_pack_test',ROOT/'research/verify-world-interrupt-aim-short.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        entries,_=m.prepare();self.assertEqual(len(entries),24)
        for name,words,domain in entries:
            self.assertIsNotNone(domain)
            self.assertTrue(all(int(b.kind) in (0,1,5,6) for b in domain[2]))

    def test_exact_delta_rejects_accounting_credit_lifecycle_and_admission_faults(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    project_sources(ROOT,{name:text.replace(change['current'],change['baseline'],1)})
        for name,old,new in [('gpu/world_interrupt_runtime.slang','f64Add(actorNumber(at),amount)','f64Add(actorNumber(at),ONE)'),
                             ('gpu/world_actor_pools.slang','kind==1 || kind==6','kind==1 || kind==2'),
                             ('gpu/counter_landing_runtime.slang','if(commands[actorBinding(s,slot)]==6) return;','if(false) return;')]:
            text=(ROOT/name).read_text();self.assertEqual(text.count(old),1)
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(old,new,1)})

    def test_diagnostic_bank_and_reserved_fields_fail_closed(self):
        report=verify(LIMITS,mode='interrupt-aim-diagnostic');self.assertTrue(report['verified'])
        words=array.array('I',[0])*LIMITS['WORLD_RELOAD_OUTPUT_WORDS'];words[BASE]=MAGIC
        self.assertEqual(gpu_records(words,list('abcde')),[])
        for at,value in ((BASE+1,COUNT+1),(BASE+2,1),(BASE+16,1),(BASE+16+COUNT*32-1,1)):
            changed=array.array('I',words);changed[at]=value
            with self.subTest(at=at),self.assertRaises(AssertionError):gpu_records(changed,list('abcde'))


if __name__=='__main__':unittest.main()
