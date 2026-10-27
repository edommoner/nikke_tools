"""Selected original diagnostics cannot prepare hidden profiles or certify GPU work."""
import contextlib,copy,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,nikke_gpu as cli,portable_original_entry_inventory as inventory
from portable_original_identity_inventory import selected_profile_bodies,selected_prepared_profiles

class OriginalEntrySelection(unittest.TestCase):
    def test_invalid_selection_fails_before_any_preparation(self):
        invalid=[([],None),(['missing'],None),(['벨벳','missing'],None),(['벨벳','벨벳'],None),([False],None),(['벨벳'],True),(['벨벳'],-1),(['벨벳'],4),(['벨벳'],3),(None,False)]
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('No preparation')):
            for names,stage in invalid:
                with self.subTest(names=names,stage=stage),self.assertRaises(ValueError):list(selected_prepared_profiles(names,stage))

    def test_all_favorite_snapshots_are_independent_and_original(self):
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('Metadata only')):rows=selected_profile_bodies(['베이'])
        self.assertEqual([s for _,s,_ in rows],[0,1,2,3])
        self.assertEqual([b['profile']['chars']['베이']['favorite_stage'] for _,_,b in rows],[0,1,2,3])
        before=copy.deepcopy(rows[1]);rows[0][2]['profile']['chars']['베이']['favorite_stage']=99;self.assertEqual(rows[1],before)
        stages=selected_profile_bodies(favorite_stage=3)
        self.assertTrue(stages);self.assertTrue(all(stage==3 for _,stage,_ in stages))

    def test_filter_is_applied_before_evaluate_and_keeps_original_body(self):
        selected=selected_profile_bodies(['벨벳','앤 : 미라클 페어리'],0);expected=[copy.deepcopy(b) for _,_,b in selected];observed=[]
        def prepare(body):observed.append(copy.deepcopy(body));return {'prepared':True}
        with patch.object(engine_worker,'evaluate',side_effect=prepare):rows=list(selected_prepared_profiles(['벨벳','앤 : 미라클 페어리'],0))
        self.assertEqual([(n,s) for n,s,_ in rows],[(n,s) for n,s,_ in selected])
        self.assertEqual(observed,[dict(b,_portable_static_inputs=True) for b in expected])

    def test_selected_real_blockers_retain_exact_owners_and_existing_model_gap_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json';original=engine_worker.evaluate;seen=[]
            def prepare(body):seen.append(body['squad'][0]);return original(body)
            with patch.object(engine_worker,'evaluate',side_effect=prepare):
                result=inventory.run(output,write=cli.write,forbid_gpu=cli.forbid_gpu,source=inventory.TYPED_SOURCE,input_policy='body-owned-hp-shield-v1',characters=['벨벳','앤 : 미라클 페어리'],favorite_stage=0)
            report=json.loads(output.read_text())
        self.assertEqual(set(seen),{'벨벳','앤 : 미라클 페어리'});self.assertEqual(len(seen),2)
        self.assertEqual(result['profile_count'],2);self.assertFalse(result['profile_selection']['all_profiles']);self.assertEqual(report['forbidden_calls'],dict(cpu_battle=0,gpu=0))
        self.assertFalse(report['calculation_verified']);self.assertFalse(report['gpu_admission_verified'])
        for row in report['profile_explanations']:
            self.assertFalse(row['input_packed']);self.assertEqual(len(row['blockers']),1)
            b=row['blockers'][0];self.assertEqual(b['owner'],row['character']);self.assertEqual(b['issue']['target'],'all_enemies')
            self.assertEqual(b['reference_readiness']['lane'],'reference_model_gap');self.assertEqual(len(b['effect_sha256']),64)

    def test_explanation_rejects_corrupted_original_identity(self):
        eff=dict(type='buff',name='same',stat='heal_received_pct',target='all_enemies')
        prepared=dict(effects=[dict(owner='original',effect=eff)]);issue=dict(phase='effect',kind='buff',stat='heal_received_pct',target='all_enemies')
        row=dict(character='original',favorite_stage=0,original_definitions_sha256='a'*64,input_packed=False,effect_blockers=[dict(index=0,owner='original',name='same',issue=issue)])
        before=copy.deepcopy((row,prepared));result=inventory.profile_explanation(row,prepared)
        self.assertEqual((row,prepared),before);self.assertEqual(result['blockers'][0]['effect_sha256'],hashlib.sha256(json.dumps(eff,ensure_ascii=False,sort_keys=True).encode()).hexdigest())
        for replacement in [dict(index=False),dict(index=1),dict(owner='other'),dict(name='other')]:
            bad=copy.deepcopy(row);bad['effect_blockers'][0].update(replacement)
            with self.assertRaises(ValueError):inventory.profile_explanation(bad,prepared)

    def test_cli_forwards_selection_without_changing_default_dispatch(self):
        with patch.object(inventory,'run',return_value={'passed':True}) as run,contextlib.redirect_stdout(io.StringIO()):
            cli.main(['entry-inventory','--suite','original-shield-weapons','--character','벨벳','--favorite-stage','0','--out','/tmp/not-written-selected-entry.json'])
        self.assertEqual(run.call_args.kwargs['characters'],['벨벳']);self.assertEqual(run.call_args.kwargs['favorite_stage'],0)
        with patch.object(inventory,'run',return_value={'passed':True}) as run,contextlib.redirect_stdout(io.StringIO()):cli.main(['entry-inventory','--out','/tmp/not-written-full-entry.json'])
        self.assertNotIn('characters',run.call_args.kwargs);self.assertNotIn('favorite_stage',run.call_args.kwargs)

    def test_invalid_mixed_selection_retains_failure_without_partial_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'failed.json'
            with patch.object(engine_worker,'evaluate',side_effect=AssertionError('No partial preparation')):
                with self.assertRaisesRegex(ValueError,'Unknown original character'):
                    inventory.run(output,write=cli.write,forbid_gpu=cli.forbid_gpu,characters=['벨벳','missing'])
            report=json.loads(output.read_text())
        self.assertFalse(report['passed']);self.assertEqual(report['profiles'],[]);self.assertEqual(report['profile_explanations'],[])
        self.assertEqual(report['forbidden_calls'],dict(cpu_battle=0,gpu=0));self.assertIn('Unknown original character',report['error'])

if __name__=='__main__':unittest.main()
