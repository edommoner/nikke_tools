"""Independent healing-share semantics and transparent native observation."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,portable_reference,detail_gpu
from calculator import timeline
from heal_sharing_compat import plan
from portable_heal_share_cases import fixtures
from portable_heal_share_contracts import verify
import world_heal_share_native as observer
from world_projectile_native import observe as plain_observe

spec=importlib.util.spec_from_file_location('heal_share_reference_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class HealShareReferenceTests(unittest.TestCase):
    def test_all_literal_contracts_forbid_packing_and_gpu(self):
        def forbidden(*args,**kwargs):raise AssertionError('Battle/packing/GPU forbidden here')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'build',forbidden):cases=fixtures()
        self.assertEqual(len(cases),20);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):
                    native,_=observer.observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_every_existing_native_field_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain,trace=plain_observe(case)
                native,observed_trace=observer.observe(case)
                self.assertTrue(native.pop('heal_share_events'))
                self.assertEqual(native,plain);self.assertEqual(observed_trace,trace)

    def test_profile_composition_restoration_and_failure(self):
        previous=sys.getprofile();calls=[]
        def prior(frame,event,result):
            if frame.f_code is plan.__code__ and event=='return':calls.append(event)
        try:
            sys.setprofile(prior)
            # This fixture enables the nested periodic/skill profile hooks.
            case=fixtures()[-2];native,_=observer.observe(case)
            self.assertTrue(verify(case,native)['verified'])
            self.assertEqual(calls,['return']);self.assertIs(sys.getprofile(),prior)
            with patch.object(observer,'projectile_native',side_effect=RuntimeError('injected native failure')):
                with self.assertRaisesRegex(RuntimeError,'injected native failure'):observer.observe(case)
            self.assertIs(sys.getprofile(),prior)
        finally:sys.setprofile(previous)

    def test_missing_plan_portion_notice_or_wrong_hp_are_rejected(self):
        case=fixtures()[1];native,_=observer.observe(case)
        for kind in ('plan','portion-call','notify','hp'):
            changed=copy.deepcopy(native)
            if kind=='hp':changed['allies'][1]['hp']+=1
            else:
                index=next(i for i,r in enumerate(changed['heal_share_events']) if r['kind']==kind)
                changed['heal_share_events'].pop(index)
            with self.subTest(kind=kind),self.assertRaises(AssertionError):verify(case,changed)

    def test_adjacent_edges_require_exact_recipients_and_sync_order(self):
        case=fixtures()[-2];native,_=observer.observe(case)
        for edit in ('recipient','ordering','time'):
            changed=copy.deepcopy(native);events=changed['heal_share_events']
            index=next(i for i,r in enumerate(events) if r['kind']=='notify' and r['event']=='event:adjacent_hp_max')
            if edit=='recipient':events[index]['owner']=4
            elif edit=='time':events[index]['time']=.1
            else:events.insert(index-1,events.pop(index))
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)

    def test_nested_mask_amounts_and_return_boundary_are_required(self):
        case=fixtures()[-1];native,_=observer.observe(case)
        for edit in ('mask','amount','notification','return'):
            changed=copy.deepcopy(native);events=changed['heal_share_events']
            if edit=='mask':next(r for r in events if r['kind']=='plan' and r['owner']==2)['weights']=[(0,1)]
            elif edit=='amount':next(r for r in events if r['kind']=='portion-call' and r['amount']==2000)['amount']=5000
            elif edit=='notification':next(r for r in events if r['kind']=='notify' and r['event']=='event:heal_received')['owner']=0
            else:
                index=next(i for i,r in enumerate(events) if r['kind']=='shared-return' and r['owner']==2)
                boundary=events.pop(index);index=next(i for i,r in enumerate(events) if r['kind']=='portion-call' and r['owner']==2 and r['amount']==5000)
                events.insert(index+1,boundary)
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)

    def test_cli_reference_records_sources_without_gpu_support_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'native.json'
            result=portable_reference.run_reference('heal-share',output,write=cli.write,forbid_gpu=cli.forbid_gpu)
            self.assertEqual(result['case_count'],20);self.assertTrue(result['cpu_reference_verified'])
            self.assertFalse(result['gpu_supported']);self.assertFalse(result['calculation_verified'])
            self.assertEqual(result['gpu_calls'],dict(build=0,execute=0));self.assertEqual(result['packing_calls'],0)
            report=json.loads(output.read_text())
            for path in ('app/heal_sharing_compat.py','app/effect_runtime.py','research/world_heal_share_native.py','research/portable_heal_share_cases.py','research/portable_heal_share_contracts.py','research/world_skill_native.py'):
                self.assertIn(path,report['source_sha256'])
            original=output.read_bytes()
            with self.assertRaises(FileExistsError):portable_reference.run_reference('heal-share',output,write=cli.write,forbid_gpu=cli.forbid_gpu)
            self.assertEqual(output.read_bytes(),original)


if __name__=='__main__':unittest.main()
