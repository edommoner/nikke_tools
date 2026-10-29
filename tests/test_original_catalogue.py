"""Selection precedes compilation and cannot drop failed original profiles."""
import array,copy,importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,nikke_gpu as cli
from portable_original_catalogue_cases import catalog,selected_rows
spec=importlib.util.spec_from_file_location('catalogue_test_adapter',ROOT/'research/verify-original-catalogue.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogue(unittest.TestCase):
    def fake(self):
        a=SimpleNamespace(SELECTED_PREPARATION=True,MAX_SELECTED_CASES=4,suite=SimpleNamespace(INPUT=2),case_catalog=lambda:['good','later'],prepare=Mock(side_effect=AssertionError('Full preparation forbidden')))
        a.prepare_selected=Mock(side_effect=lambda names:([(n,[1,2],dict(name=n)) for n in names],None));return a
    def manifest(self,**kwargs):return dict(suite='catalogue-fixture',purpose='development',selected_cases=['good'],**kwargs)

    def test_metadata_listing_never_prepares_or_compiles_any_profile(self):
        from calculator import timeline
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('Listing must be metadata only')),patch.object(timeline,'simulate',side_effect=AssertionError('No battle')):
            rows=catalog();listed=cli.case_names('original-catalogue',match='모더니아')
        self.assertEqual(len(rows),1064);self.assertEqual(len(listed['cases']),4);self.assertEqual(listed['total_cases'],1084)
        self.assertFalse(listed['gpu_calls']);self.assertEqual({r['favorite_stage'] for r in rows.values()},{0,1,2,3})

    def test_only_explicit_selected_names_are_prepared_and_input_is_canonical(self):
        a=self.fake()
        with patch.dict(cli.SUITES,{'catalogue-fixture':{}}):rows,raw=cli.prepare_entries(a,self.manifest())
        a.prepare.assert_not_called();a.prepare_selected.assert_called_once_with(['good'])
        self.assertEqual([r[0] for r in rows],['good']);self.assertEqual(raw,array.array('I',[1,1,2]).tobytes())

    def test_unknown_duplicate_empty_and_oversized_selection_fail_before_preparation(self):
        for selected in [[],['missing'],['good','good'],['good']*5,[False],None]:
            a=self.fake()
            with self.subTest(selected=selected),patch.dict(cli.SUITES,{'catalogue-fixture':{}}),self.assertRaises(ValueError):cli.prepare_entries(a,dict(suite='catalogue-fixture',purpose='development',selected_cases=selected))
            a.prepare_selected.assert_not_called();a.prepare.assert_not_called()

    def test_frozen_cohort_cannot_be_overridden_and_keeps_canonical_order(self):
        a=self.fake();config={'frozen_cases':['later','good']}
        with patch.dict(cli.SUITES,{'catalogue-fixture':config}):
            rows,raw=cli.prepare_entries(a,dict(suite='catalogue-fixture',purpose='sealed',selected_cases=[]))
            self.assertEqual([r[0] for r in rows],['good','later'])
            with self.assertRaisesRegex(ValueError,'cannot be overridden'):cli.prepare_entries(a,self.manifest())
        a.prepare_selected.assert_called_once_with(['good','later'])

    def test_unfrozen_catalogue_cannot_bypass_development_restriction(self):
        a=self.fake()
        with patch.dict(cli.SUITES,{'catalogue-fixture':{}}),self.assertRaisesRegex(ValueError,'development package'):cli.prepare_entries(a,dict(suite='catalogue-fixture',purpose='sealed',selected_cases=['good']))
        a.prepare_selected.assert_not_called()

    def test_dropped_extra_rejected_wrong_order_and_truncated_outputs_fail(self):
        examples=[([],None),([('good',[1,2],None)],None),([('good',[1],{})],None),([('later',[1,2],{}),('good',[1,2],{})],None),([('later',[1,2],{})],None),([('good',[1,2],{})],b'wrong')]
        for result in examples:
            a=self.fake();a.prepare_selected=Mock(return_value=result)
            with self.subTest(result=result),patch.dict(cli.SUITES,{'catalogue-fixture':{}}),self.assertRaises(ValueError):cli.prepare_entries(a,self.manifest())

    def test_compiler_failure_is_propagated_without_rejection_conversion(self):
        a=self.fake();a.prepare_selected=Mock(side_effect=ValueError('Selected original unsupported effect'))
        with patch.dict(cli.SUITES,{'catalogue-fixture':{}}),self.assertRaisesRegex(ValueError,'Selected original unsupported'):cli.prepare_entries(a,self.manifest())

    def test_malformed_catalogue_protocol_and_limit_are_rejected(self):
        for change in [dict(SELECTED_PREPARATION=1),dict(case_catalog=lambda:['good','good']),dict(case_catalog=lambda:[]),dict(prepare_selected=None),dict(MAX_SELECTED_CASES=True),dict(MAX_SELECTED_CASES=9),dict(development_entries=lambda:[])]:
            a=self.fake();a.__dict__.update(change)
            with self.subTest(change=change),patch.dict(cli.SUITES,{'catalogue-fixture':{}}),self.assertRaises(ValueError):cli.prepare_entries(a,self.manifest())

    def test_invalid_frozen_selection_fails_before_any_compilation(self):
        for names in ([],['missing'],['good','good']):
            a=self.fake()
            with patch.dict(cli.SUITES,{'catalogue-fixture':{'frozen_cases':names}}),self.assertRaises(ValueError):cli.prepare_entries(a,dict(suite='catalogue-fixture',purpose='sealed',selected_cases=[]))
            a.prepare_selected.assert_not_called()

    def test_real_selected_profile_preserves_all_original_effects_and_favorite_stage(self):
        name='original-catalogue/projectile/라플라스/favorite-3/3s'
        from calculator import timeline
        original=engine_worker.evaluate;calls=[]
        def evaluate(body):calls.append(body);return original(body)
        with patch.object(engine_worker,'evaluate',evaluate),patch.object(timeline,'simulate',side_effect=AssertionError('No battle during packing')):
            rows,raw=cli.prepare_entries(adapter,dict(suite='original-catalogue',purpose='development',selected_cases=[name]))
        self.assertEqual(len(calls),1);self.assertTrue(calls[0]['_portable_static_inputs'])
        c,m,b,d=rows[0][2];source=c['original_run']['prepared'];self.assertEqual(c['effects'],[e['effect'] for e in source['effects']])
        self.assertEqual(set(m['binding_source_indices']),set(range(len(source['effects']))));self.assertEqual(c['catalogue_profile']['favorite_stage'],3)
        self.assertEqual(c['original_run']['body']['profile']['chars']['라플라스']['collection_stage'],'SR15')
        self.assertEqual(len(rows[0][1]),115680);self.assertFalse(c['declared_owner_counter'])

    def test_real_unsupported_profile_fails_instead_of_disappearing(self):
        name='original-catalogue/projectile/일레그/favorite-0/3s'
        with self.assertRaisesRegex(ValueError,'selector'):cli.prepare_entries(adapter,dict(suite='original-catalogue',purpose='development',selected_cases=[name]))

    def test_registered_initial_cohort_has_four_known_cases_and_same_source(self):
        config=cli.SUITES['original-catalogue-initial'];names=config['frozen_cases']
        self.assertEqual(len(names),4);self.assertTrue(set(names)<=set(adapter.case_catalog()))
        self.assertEqual(config['source'],adapter.SOURCE);self.assertEqual((config['input_words'],config['output_words']),(115680,2032000))
        self.assertTrue(config['parent_oracle_reuse'])

    def test_prepared_bodies_remain_immutable_when_selecting_variants(self):
        names=['original-catalogue/hp-shield/모더니아/favorite-0/3s','original-catalogue/projectile/모더니아/favorite-0/30s']
        rows=selected_rows(names);before=copy.deepcopy(rows[1]);rows[0]['body']['profile']['chars']['모더니아']['favorite_stage']=99
        self.assertEqual(rows[1],before)

    def test_modernia_witness_requires_original_mode_entry_and_restoration(self):
        from portable_original_catalogue_cases import prepare,verify_original_weapon_change
        case,_=prepare(selected_rows(['original-catalogue/hp-shield/모더니아/favorite-0/30s'])[0])
        def shot(coefficient,skill=False):return dict(owner=0,coefficient=coefficient,weapon_mode_skill=skill)
        normal=case['original_run']['prepared']['chars'][0]['_weapon']['damage_coeff']
        change=next(r['effect'] for r in case['original_run']['prepared']['effects'] if r['owner']=='모더니아' and r['effect']['type']=='weapon_change')
        mode=change['damage_coeff']['10']
        valid=[shot(normal),shot(mode),shot(mode),shot(normal)]
        verify_original_weapon_change(case,valid)
        for rows in ([shot(normal)],valid[1:],valid[:-1],[shot(normal),shot(mode,True),shot(normal)],[shot(normal),shot(mode),shot(normal),shot(mode),shot(normal)]):
            with self.subTest(rows=rows),self.assertRaises(AssertionError):verify_original_weapon_change(case,rows)

    def test_complete_skill_history_capacity_fails_before_gpu_instead_of_truncating(self):
        from portable_original_catalogue_cases import require_skill_history_capacity
        for count in (0,127,128):require_skill_history_capacity(dict(skill_trace=[None]*count))
        for count in (129,2048):
            native=dict(skill_trace=[None]*count)
            with self.assertRaisesRegex(ValueError,f'{count} > 128'):require_skill_history_capacity(native)
            self.assertEqual(len(native['skill_trace']),count)
if __name__=='__main__':unittest.main()
