"""Exact area semantics, mixed pools, full diagnostic capacity and source faults."""
import array,copy,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_aimed_area_cases import fixtures
from portable_aimed_area_contracts import verify
from world_aimed_area_native import observe
from world_aimed_packet_native import observe as packet_observe
from world_parts_skill_native import observe as uninstrumented_native
from portable_aimed_area_source_contract import ledger,project_sources
from portable_interrupt_aim_trace import BASE,COUNT,MAGIC,gpu_records
from portable_scratch_layout import verify as layout
from portable_specs import LIMITS


class AimedAreaTests(unittest.TestCase):
    def test_all12_contracts_preserve_native_trace_and_semantic_reads(self):
        for case in fixtures():
            counts=[[],[]]
            def measure(run,counts):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get, \
                     patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live, \
                     patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);counts.extend([get.call_count,live.call_count,sample.call_count]);return result
            with self.subTest(case=case['name']):
                # The original homogeneous-shot observer cannot describe area
                # returns. Disable only that observer and optional typed impact
                # publication in the baseline, keeping actual native executors.
                from contextlib import nullcontext
                import world_projectile_native as projectile
                with patch.object(projectile,'capture_projectile_shots',lambda names:nullcontext([])),patch.object(BuffManager,'publish_landing',lambda *args:None):plain,trace=measure(uninstrumented_native,counts[0])
                actual,recorded=measure(observe,counts[1]);self.assertTrue(verify(case,actual)['verified'])
                for key in ('physical_packet_sets','interrupt_landings','projectile_shots','focus_aim'):actual.pop(key,None);plain.pop(key,None)
                self.assertEqual(actual,plain);self.assertEqual(recorded,trace);self.assertEqual(*counts)

    def test_original8_packet_contracts_and_all_native_fields_are_preserved(self):
        for case in fixtures()[:8]:
            prior,trace=packet_observe(case);actual,recorded=observe(case)
            actual.pop('parts_skill_accounting');actual.pop('parts_skill_events')
            self.assertEqual(actual,prior);self.assertEqual(recorded,trace)

    def test_packet_and_extra_accounting_faults_are_detected(self):
        case=fixtures()[8];native,_=observe(case)
        for fault in ('order','extra','total','damage','hp'):
            bad=copy.deepcopy(native)
            if fault=='order':bad['physical_packet_sets'][0]['packets'].reverse()
            elif fault=='extra':bad['parts_skill_accounting']['extra'][1]['extra_hits']+=1
            elif fault=='total':bad['parts_skill_accounting']['interrupt_damage'][0]+=1
            elif fault=='damage':bad['damage'][0]+=1
            else:bad['allies'][0]['hp']+=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)

    def test_exact_delta_rejects_landing_order_exclusion_and_resampling_faults(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(change['current'],change['baseline'],1)})
        name='gpu/counter_landing_runtime.slang';text=(ROOT/name).read_text()
        for old,new in [('slot==excluded||commands[input]!=1','false||commands[input]!=1'),('targetAmount=actorNumber(shot+6)','targetAmount=ONE'),('landAimedAreaPacket(s,who,0,amount','landAimedAreaPacket(s,who,target,amount')]:
            self.assertIn(old,text)
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(old,new,1)})

    def test_full128_diagnostic_records_fit_exclusive_bank_without_omission(self):
        self.assertEqual((BASE,COUNT),(770976,128));layout(LIMITS,mode='interrupt-aim-diagnostic')
        data=array.array('I',[0])*LIMITS['WORLD_RELOAD_OUTPUT_WORDS'];data[BASE]=MAGIC;data[BASE+1]=COUNT
        for i in range(COUNT):
            at=BASE+16+i*32;data[at+2]=1;data[at+3]=data[at+4]=1
        self.assertEqual(len(gpu_records(data,list('abcde'))),128)
        data[BASE+1]+=1
        with self.assertRaises(AssertionError):gpu_records(data,list('abcde'))


if __name__=='__main__':unittest.main()
