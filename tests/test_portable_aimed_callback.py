"""Counter children must change healing/following shots, preserving sampled packets."""
import copy,random,sys,unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_aimed_callback_cases import fixtures
from portable_aimed_callback_contracts import verify
from world_aimed_area_native import observe
from portable_interrupt_runtime import capture_interrupt_landings
from world_parts_skill_native import observe as baseline
import world_projectile_native as projectile


class AimedCallbackTests(unittest.TestCase):
    def test_all20_preserve_uninstrumented_battle_and_semantic_reads(self):
        for case in fixtures():
            def measure(run):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);return result,[get.call_count,live.call_count,sample.call_count]
            with self.subTest(case=case['name']):
                # Keep canonical landing/counter publication and the private kind6 bridge
                # in both executions; omit only the added packet/focus observers.
                with capture_interrupt_landings(),patch.object(projectile,'capture_projectile_shots',lambda names:nullcontext([])):
                    (plain,trace),reads=measure(baseline)
                (actual,recorded),observed=measure(observe);self.assertTrue(verify(case,actual)['verified'])
                for key in ('physical_packet_sets','interrupt_landings','projectile_shots','focus_aim'):actual.pop(key,None);plain.pop(key,None)
                self.assertEqual(actual,plain);self.assertEqual(recorded,trace);self.assertEqual(observed,reads)

    def test_mutations_cannot_hide_order_or_counter_or_hp_changes(self):
        case=fixtures()[3];native,_=observe(case)
        for kind in ('packet','hp','completion','carrier','extra'):
            bad=copy.deepcopy(native)
            if kind=='packet':bad['physical_packet_sets'][0]['packets'][1]['damage']*=2
            elif kind=='hp':bad['allies'][0]['hp']+=1
            elif kind=='completion':bad['target_counters']['completions'][0]['time']+=.01
            elif kind=='carrier':bad['named_state']['allied_carriers'][-1]['stack']+=1
            else:bad['parts_skill_accounting']['interrupt_damage'][0]+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):verify(case,bad)

    def test_full_cartesian_inputs_are_unique_and_keep_scatter(self):
        rows=fixtures();self.assertEqual(len(rows),20);self.assertEqual(len({x['name'] for x in rows}),20)
        scatter=[x for x in rows if '-scatter-' in x['name']];self.assertEqual(len(scatter),4)
        self.assertTrue(all(x['combat']['weapons'][0]['pellets']==3 and x['combat']['weapons'][0]['muzzles']==2 for x in scatter))


if __name__=='__main__':unittest.main()
