"""Complete source/ammo profiles retain native models and no CPU schedules."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu
s=importlib.util.spec_from_file_location('original_owned_test',ROOT/'research/verify-coordinate-original-owned-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalOwnedTests(unittest.TestCase):
    def test_complete_original_definitions_and_public_policies_without_simulation(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native firing schedule in packing')):rows,_=a.prepare()
        self.assertEqual(len(rows),5)
        for i,(_,words,domain) in enumerate(rows):
            c,m,_,_=domain;count=74 if i<3 else 88
            self.assertEqual(len(c['effects']),count);self.assertEqual(set(m['binding_source_indices']),set(range(count)))
            self.assertEqual(c['effects'],[e['effect'] for e in c['original_run']['prepared']['effects']]);self.assertEqual(c['sequence'],[])
            self.assertEqual(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'],[]);self.assertIs(provider(a,domain)[2],a.native_reference)
            if i<3:
                self.assertEqual(c['effects'][0]['feather_slots'],[-1,38.,32.,26.]);self.assertEqual(c['effects'][4]['feather_slots'],[-1,38.,32.,26.,10.,10.])
            else:self.assertTrue(c['original_run']['body']['weapon_mode_swap'])
    def test_actual_population_generations_and_equivalent_ammo_reject_corruption(self):
        import array,copy,hashlib,json
        records=json.loads((ROOT/'tests/fixtures/portable-original-owned-observations.json').read_text())['rows'];rows,_=a.prepare()
        for r,(name,words,domain) in zip(records,rows,strict=True):
            self.assertEqual(r['name'],name);self.assertEqual(r['input_sha256'],hashlib.sha256(array.array('I',words).tobytes()).hexdigest())
            self.assertTrue(a.verify_witness(domain[0],r['native']))
            kinds=('epoch','expiry') if domain[0]['owned_witness']=='Ein' else ('count',)
            if domain[0]['owned_witness']=='Ein' and domain[0]['duration']>1:kinds+=('tick',)
            if domain[0]['owned_witness']!='Ein' and domain[0]['duration']>3:kinds+=('quantity','notice')
            for kind in kinds:
                bad=copy.deepcopy(r['native'])
                if kind=='epoch':bad['original_owned_sources']['final'][0]['epoch']+=1
                elif kind=='expiry':bad['original_owned_sources']['final'][0]['expiry'][1]=0.
                elif kind=='tick':bad['original_owned_sources']['ticks'].pop()
                elif kind=='count':bad['ammo_equivalent']['squad_count']+=1
                elif kind=='quantity':bad['ammo_equivalent']['calls'][0]['value']=39.
                else:
                    notices=bad['ammo_equivalent']['notices'];notices.pop(next(i for i,r in enumerate(notices) if r['origin']!='physical'));bad['ammo_equivalent']['squad_count']-=1
                with self.subTest(name=name,kind=kind),self.assertRaises(AssertionError):a.verify_witness(domain[0],bad)
    def test_saved_metal_state_rejects_clock_population_and_counter_corruption(self):
        import copy,json,math
        states=json.loads((ROOT/'tests/fixtures/portable-original-owned-gpu-state.json').read_text())['rows'];native=json.loads((ROOT/'tests/fixtures/portable-original-owned-observations.json').read_text())['rows'];rows,_=a.prepare()
        for saved,n,(name,_,domain) in zip(states,native,rows,strict=True):
            self.assertEqual(saved['name'],name);self.assertEqual(saved['input_sha256'],n['input_sha256'])
            a.compare_owned_state(saved['actual'],domain,n['native'])
            fields=('epoch','count','next_at') if saved['actual']['periodic_sources'] else ('activations','counter')
            for field in fields:
                bad=copy.deepcopy(saved['actual'])
                if field in ('epoch','count'):bad['periodic_sources'][0][field]+=1
                elif field=='next_at':bad['periodic_sources'][0][field]=math.nextafter(bad['periodic_sources'][0][field],math.inf)
                elif field=='activations':bad['timers'][domain[1]['binding_source_indices'].index(5)]['activations']+=1
                else:bad['timers'][domain[1]['binding_source_indices'].index(10)]['trigger_counts'][0]+=1
                with self.subTest(name=name,field=field),self.assertRaises(AssertionError):a.compare_owned_state(bad,domain,n['native'])
if __name__=='__main__':unittest.main()
