"""Original incoming scenes must exercise real taunt, healing and decoy loss."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_original_incoming_profiles import profiles
from portable_original_incoming_contracts import verify
from portable_original_catalogue_cases import selected_rows
spec=importlib.util.spec_from_file_location('incoming_catalogue',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueIncoming(unittest.TestCase):
    def test_literal_scenes_list_without_native_preparation(self):
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('Metadata only')):
            rows=profiles();listed=adapter.case_catalog()
        self.assertEqual(len(rows),4);self.assertEqual(len(listed),1084);self.assertTrue(set(rows)<=set(listed))
        red=[r for r in rows.values() if r['character']=='레드 후드']
        self.assertEqual(red[0]['body'],red[1]['body']);self.assertEqual(red[0]['patterns'],red[1]['patterns'])
        self.assertIn('declared_burst_sequence',red[0]);self.assertNotIn('declared_burst_sequence',red[1])

    def test_full_original_definitions_and_literal_incoming_reach_common_compiler(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static only')):rows,_=adapter.prepare_selected(list(profiles()))
        self.assertEqual([len(r[2][0]['effects']) for r in rows],[81,81,74,74])
        for name,words,(case,meta,bindings,desc) in rows:
            original=case['original_run']['prepared']
            self.assertEqual(len(words),115680);self.assertEqual(case['duration'],30)
            self.assertEqual(case['patterns'],case['original_run']['body']['enemy']['patterns'])
            self.assertEqual(case['effects'],[e['effect'] for e in original['effects']]);self.assertFalse(case['declared_owner_counter'])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(case['effects']))))
            self.assertTrue(any(p['kind']=='attack' for p in case['patterns']))

    def test_b2_witness_rejects_uninjured_unhealed_or_unredirected_passes(self):
        case=dict(catalogue_profile=dict(scene_witness=dict(family='Red-Hood',scenario='B2')))
        hits=[dict(time=t,owner=o,hp=100,hp_after=900,down=False) for t,o in zip((1.,4.,14.),(2,0,2))]
        native=dict(battle=dict(hits=hits),sampled_health_returns=[dict(kind='_apply_lifesteal',time=4.1,hp=[1000]*5)])
        verify(case,native)
        for mutate in [lambda n:n['battle']['hits'][1].update(owner=2),lambda n:n['battle']['hits'][1].update(hp=0),lambda n:n.update(sampled_health_returns=[]),lambda n:n['battle']['hits'][1].update(down=True)]:
            bad=copy.deepcopy(native);mutate(bad)
            with self.assertRaises(AssertionError):verify(case,bad)

    def test_decoy_witness_rejects_missing_absorption_and_missing_hp_delivery(self):
        case=dict(catalogue_profile=dict(scene_witness=dict(family='Cinderella',scenario='broken')))
        native=dict(battle=dict(hits=[dict(owner=0,damage=110,decoy=100,hp=0,down=False),dict(owner=0,damage=10,decoy=0,hp=10,down=False),dict(owner=0,damage=10,decoy=10,hp=0,down=False)]))
        verify(case,native)
        for field,value in [('decoy',0),('hp',1),('damage',100)]:
            bad=copy.deepcopy(native);bad['battle']['hits'][0][field]=value
            with self.assertRaises(AssertionError):verify(case,bad)
        bad=copy.deepcopy(native);bad['battle']['hits'][1]['decoy']=10
        with self.assertRaises(AssertionError):verify(case,bad)
        bad=copy.deepcopy(native);bad['battle']['hits'][1]['hp']=0
        with self.assertRaises(AssertionError):verify(case,bad)
        bad=copy.deepcopy(native);bad['battle']['hits'][2].update(hp=10,decoy=0)
        with self.assertRaises(AssertionError):verify(case,bad)

if __name__=='__main__':unittest.main()
