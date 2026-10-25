"""Original complete inputs and common accumulator proof integration."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu
s=importlib.util.spec_from_file_location('original_accum_test',ROOT/'research/verify-coordinate-original-accum-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalAccumTests(unittest.TestCase):
    def test_complete_original_definitions_without_simulation(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in packing')):rows,_=a.prepare()
        self.assertEqual(len(rows),4)
        for i,(_,words,domain) in enumerate(rows):
            c,m,_,_=domain;count=73 if i<2 else 74
            self.assertEqual(len(c['effects']),count)
            self.assertEqual(set(m['binding_source_indices']),set(range(count)))
            self.assertEqual(c['effects'],[e['effect'] for e in c['original_run']['prepared']['effects']])
            self.assertEqual(c['sequence'],[]);self.assertNotIn('python_observers_only',c)
            self.assertEqual(c['coordinate_packet_history'],'ordered-sha256-v1')
            self.assertEqual(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'],[])
            self.assertIs(provider(a,domain)[2],a.native_reference)
    def test_control_witness_rejects_even_empty_discharge(self):
        c=dict(accum_witness='control');n=dict(damage_accumulation=dict(events=[]))
        self.assertTrue(a.verify_witness(c,n))
        n['damage_accumulation']['events']=[dict(kind='take',value=0.)]
        with self.assertRaises(AssertionError):a.verify_witness(c,n)
if __name__=='__main__':unittest.main()

class AccumCreationTests(unittest.TestCase):
    def test_real_creation_boundary_and_strict_missing_receipt(self):
        from types import SimpleNamespace
        from world_coordinate_sampled_skill_native import creation_indices
        case=dict(effects=[dict(name='release',type='damage',stat='accum_split_damage')])
        _dot_events=[];eff=case['effects'][0]
        def _handle_damage_eff(eff,caster,t):
            _dot_events.append(SimpleNamespace(hit_tag='accum_split_damage',skill_name=eff['name'],t=t,caster=caster,damage=31))
        def _land(ev,t):pass
        with creation_indices(case) as observed:
            _handle_damage_eff(eff,'owner',2.)
            _land(_dot_events[0],2.)
        self.assertEqual(observed,[dict(row=0,created=2.,landed=2.,amount=31,hit=1,hits=1)])
        with self.assertRaisesRegex(AssertionError,'Missing native creation'):
            with creation_indices(case):_land(_dot_events[0],2.)

class AccumWitnessTests(unittest.TestCase):
    def test_actual_expiry_and_full_release_lifetimes_and_corruption(self):
        import array,copy,hashlib,json
        records=json.loads((ROOT/'tests/fixtures/portable-original-accum-observations.json').read_text())['rows'];rows,_=a.prepare()
        for r,(name,words,domain) in zip(records,rows,strict=True):
            self.assertEqual(r['name'],name);self.assertEqual(r['input_sha256'],hashlib.sha256(array.array('I',words).tobytes()).hexdigest())
            n=dict(damage_accumulation=r['observed']);self.assertTrue(a.verify_witness(domain[0],n))
            if domain[0]['accum_witness']=='control':continue
            for corrupt in ('notice','quantity','consumed','time'):
                bad=copy.deepcopy(n);events=bad['damage_accumulation']['events'];take=next(e for e in events if e['kind']=='take')
                if corrupt=='notice':events[:]=[e for e in events if e['kind']!='full-notice']
                elif corrupt=='quantity':take['value']+=1.
                elif corrupt=='consumed':take['after']['archive'][take['name']]=1.
                else:take['time']-=.1
                with self.subTest(name=name,corrupt=corrupt),self.assertRaises(AssertionError):a.verify_witness(domain[0],bad)
