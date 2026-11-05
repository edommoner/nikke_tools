"""Partial-charge native prerequisites without portable admission or GPU."""
import copy,sys,random,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,detail_gpu
from calculator.buff_manager import BuffManager
from portable_nonfull_charge_cases import fixtures
from portable_nonfull_charge_contracts import verify
from world_nonfull_charge_native import observe
from world_projectile_native import observe as plain


class NonFullChargeReferenceTests(unittest.TestCase):
    def test_literal_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases)
        def forbidden(*a,**k):raise AssertionError('GPU/packing forbidden')
        with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)

    def test_observation_preserves_battle_trace_and_semantic_reads(self):
        for case in fixtures():
            def measured(run):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);return result,[get.call_count,live.call_count,sample.call_count]
            with self.subTest(case=case['name']):
                (actual,trace),reads=measured(observe);(baseline,other),counts=measured(plain)
                actual.pop('nonfull_charge');self.assertEqual(actual,baseline);self.assertEqual(trace,other);self.assertEqual(reads,counts)

    def test_wrong_event_class_owner_order_count_and_health_reject(self):
        case=fixtures()[0];native,_=observe(case)
        for fault in ('full','event','owner','order','count','health','orphan'):
            n=copy.deepcopy(native);events=n['nonfull_charge'];shot=next(e for e in events if e['kind']=='shot' and e['owner']==0)
            if fault=='full':shot['full']=True
            elif fault=='event':next(e for e in events if e.get('event')=='non_full_charge_fire')['event']='full_charge_fire'
            elif fault=='owner':next(e for e in events if e['kind']=='activate')['owner']=4
            elif fault=='order':
                i=next(i for i,e in enumerate(events) if e.get('event')=='non_full_charge_fire');events[i],events[i-1]=events[i-1],events[i]
            elif fault=='count':events.remove(shot)
            elif fault=='orphan':events.append(dict(kind='notify',event='non_full_charge_fire',owner=0,time=.9))
            else:n['allies'][0]['hp']+=100
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,n)

    def test_tap_is_not_synonymous_with_partial_and_muzzles_do_not_multiply_count(self):
        rows={c['name']:c for c in fixtures()}
        self.assertEqual(rows['nonfull-charge-slow-tap-genuine-full']['contract']['partial'],0)
        self.assertEqual(rows['nonfull-charge-periodic-full']['contract']['full'],2)
        c=rows['nonfull-charge-scatter-muzzles'];self.assertEqual(c['combat']['weapons'][0]['muzzles'],2);self.assertEqual(c['contract']['activations'],3)
        for c in (rows['nonfull-charge-slow-tap-genuine-full'],rows['nonfull-charge-periodic-full'],rows['nonfull-charge-scatter-muzzles']):native,_=observe(c);verify(c,native)


if __name__=='__main__':unittest.main()
