"""Real role parties and canonical explicit burst controls; no injected effects."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_declared_burst_sequence import apply
from portable_original_role_profiles import profiles
from portable_original_catalogue_cases import selected_rows
spec=importlib.util.spec_from_file_location('role_catalogue_tests',ROOT/'research/verify-original-catalogue.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogueRoles(unittest.TestCase):
    def test_literal_config_is_validated_bounded_and_copied(self):
        chars=[dict(name=n,_weapon=dict(burst_stage=s)) for n,s in zip('ABCDE',('A','1','2','3','3'))]
        sequence=[{'1':['A'],'2':['A'],'3':['D']}];cfg={'duration':30,'burst_sequence':None}
        before=copy.deepcopy((cfg,chars,sequence));result=apply(cfg,chars,sequence)
        self.assertEqual((cfg,chars,sequence),before);self.assertEqual(result['burst_sequence'],sequence)
        sequence[0]['1'].clear();self.assertEqual(result['burst_sequence'][0]['1'],['A'])
        for invalid in (None,[],[{}]*17,[{'4':[]}],[{'1':['missing']}],[{'1':['A','A']}],[{'1':['D']}],[{'2':['B']}],[{'1':'A'}]):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):apply(cfg,chars,invalid)
        with self.assertRaisesRegex(ValueError,'overwritten'):apply({'burst_sequence':[]},chars,[{}])

    def test_role_listing_never_runs_preparation_or_battle(self):
        from calculator import timeline
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('No preparation while listing')),patch.object(timeline,'simulate',side_effect=AssertionError('No battle')):
            rows=profiles();names=adapter.case_catalog()
        self.assertEqual(len(rows),4);self.assertTrue(set(rows)<=set(names));self.assertEqual(len(names),1084)
        self.assertFalse(any('declared_burst_sequence' in r for n,r in rows.items() if 'Rapi-' in n))

    def test_only_real_parties_and_all_original_definitions_reach_compiler(self):
        from calculator import timeline
        names=list(profiles())
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static preparation only')):
            entries,_=adapter.prepare_selected(names)
        for name,words,(case,meta,bindings,descriptor) in entries:
            with self.subTest(name=name):
                original=case['original_run']['prepared']
                self.assertEqual(case['duration'],30);self.assertEqual(len(words),115680)
                self.assertEqual(case['effects'],[r['effect'] for r in original['effects']])
                self.assertEqual(case['owners'],[case['names'].index(r['owner']) for r in original['effects']])
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(case['effects']))))
                self.assertFalse(case['declared_owner_counter'])
                if case.get('declared_burst_sequence'):
                    self.assertIsNone(original['policies']['config'].get('burst_sequence'))
                    self.assertFalse(meta['coordinate_original_input']['original_controls_preserved'])
                    self.assertTrue(meta['coordinate_original_input']['declared_burst_sequence_applied_after_identity_check'])
                    self.assertEqual(words[109792+3],1)
                else:self.assertTrue(meta['coordinate_original_input']['original_controls_preserved'])

    def test_party_stage_condition_has_a_real_b1_control(self):
        rows=profiles();off=rows['original-catalogue/role/Rapi-no-B1/30s']['body'];on=rows['original-catalogue/role/Rapi-with-B1/30s']['body']
        self.assertEqual(off['squad'][:4],on['squad'][:4]);self.assertEqual(off['squad'][-1],'센티');self.assertEqual(on['squad'][-1],'미란다')
        self.assertFalse(any(str(engine_worker.META[n]['burst_stage'])=='1' for n in off['squad'][1:]))
        self.assertTrue(any(str(engine_worker.META[n]['burst_stage'])=='1' for n in on['squad'][1:]))

    def test_role_data_and_selected_bodies_are_independent(self):
        rows=selected_rows(list(profiles()));before=copy.deepcopy(rows[1]);rows[0]['body']['profile']['chars']['도라']['skill_levels']['1']=1
        self.assertEqual(rows[1],before)

    def test_missing_or_wrong_actual_casts_do_not_certify_a_role(self):
        from portable_original_catalogue_cases import verify_role_casts
        expected={'Rapi-no-B1':[(1,0)],'Rapi-with-B1':[(3,0)],'Red-Hood-123':[(1,0),(2,0),(3,0)],'Red-Hood-12':[(1,0),(2,0),(3,3)]}
        for variant,casts in expected.items():
            case={'catalogue_profile':{'variant':variant}}
            trace=[dict(event=e,owner=o) for e,o in casts]
            verify_role_casts(case,trace)
            with self.assertRaises(AssertionError):verify_role_casts(case,[])
            with self.assertRaises(AssertionError):verify_role_casts(case,[dict(r,owner=4) for r in trace])

if __name__=='__main__':unittest.main()
