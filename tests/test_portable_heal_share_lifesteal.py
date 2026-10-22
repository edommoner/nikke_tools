"""Native packet/source/portion contracts before any GPU admission."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from portable_heal_share_lifesteal_cases import fixtures
from portable_heal_share_contracts import verify
from world_heal_share_native import observe
from world_projectile_native import observe as plain_observe
spec=importlib.util.spec_from_file_location('heal_lifesteal_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class HealShareLifestealTests(unittest.TestCase):
    def test_literal_packets_forbid_packing_and_gpu(self):
        def forbidden(*a,**kw):raise AssertionError('GPU/packing forbidden')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),9);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_optional_observation_preserves_full_state_and_trace(self):
        for case in fixtures():
            native,trace=observe(case);plain,plain_trace=plain_observe(case);native.pop('heal_share_events')
            with self.subTest(case=case['name']):self.assertEqual(native,plain);self.assertEqual(trace,plain_trace)

    def test_packet_amount_source_or_extra_recursive_notice_is_rejected(self):
        case=fixtures()[5];native,_=observe(case)
        for edit in ('packet','source','recursive'):
            changed=copy.deepcopy(native);events=changed['heal_share_events']
            if edit=='packet':next(e for e in events if e['kind']=='lifesteal-call')['damage']=1
            elif edit=='source':next(e for e in events if e['kind']=='notify' and e['event']=='event:heal_received')['heal_source']=1
            else:events.append(copy.deepcopy(next(e for e in events if e['kind']=='notify' and e['event']=='event:heal_received')))
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)


if __name__=='__main__':unittest.main()
