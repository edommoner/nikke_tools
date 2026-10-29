"""Saved blockers are ranked by unique profiles, never by summed target counts."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli,portable_original_entry_inventory as inventory
from portable_entry_plan import plan,run

class EntryPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        cls.source=cls.folder/'inventory.json'
        inventory.run(cls.source,write=cli.write,forbid_gpu=cli.forbid_gpu,source=inventory.TYPED_SOURCE,input_policy='body-owned-hp-shield-v1',characters=['베이'])
        cls.report=json.loads(cls.source.read_text())
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_real_four_stages_with_two_targets_are_four_profiles_not_eight(self):
        before=copy.deepcopy(self.report);r=plan(self.report)
        self.assertEqual(self.report,before);self.assertEqual((r['profile_count'],r['blocked_profiles']),(4,4))
        self.assertEqual(len(r['operator_families']),1);f=r['operator_families'][0]
        self.assertEqual(f['affected_profiles'],4);self.assertEqual([p['favorite_stage'] for p in f['profiles']],[0,1,2,3])
        self.assertEqual(set(f['targets']),{'all_allies','self_cover'})
        self.assertFalse(r['calculation_verified']);self.assertFalse(r['gpu_admission_verified']);self.assertFalse(r['current_source_revalidated'])
        self.assertFalse(f['published_evidence'][0]['exact_cover_weight_verified'])
        f['published_evidence'][0]['exact_cover_weight_verified']=True
        self.assertEqual(self.report,before)
    def test_duplicate_id_bad_counts_or_runtime_claims_cannot_be_ranked(self):
        bad=[]
        r=copy.deepcopy(self.report);r['profiles'].append(copy.deepcopy(r['profiles'][0]));r['profile_count']+=1;bad.append(r)
        for key,value in [('profile_count',True),('packed_profiles',2),('full_character_verified',1),('calculation_verified',True),('gpu_admission_verified',True),('passed',False)]:
            r=copy.deepcopy(self.report);r[key]=value;bad.append(r)
        r=copy.deepcopy(self.report);r['forbidden_calls']['gpu']=False;bad.append(r)
        r=copy.deepcopy(self.report);r['profiles'][0]['original_definitions_sha256']='bad';bad.append(r)
        r=copy.deepcopy(self.report);r['profiles'][0]['gpu_admission_verified']=True;bad.append(r)
        r=copy.deepcopy(self.report);r['kind_rejected_profiles']=1;bad.append(r)
        for r in bad:
            with self.assertRaises(ValueError):plan(r)
    def test_saved_file_is_bound_without_preparation_or_gpu_and_never_overwritten(self):
        import engine_worker,hashlib
        target=self.folder/'plan.json'
        with patch.object(engine_worker,'evaluate',side_effect=AssertionError('No new preparation')),cli.forbid_gpu():result=run(self.source,target,write=cli.write)
        saved=json.loads(target.read_text());self.assertEqual(saved['source_inventory_sha256'],hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(saved['blocked_profiles'],result['blocked_profiles']);self.assertEqual(saved['gpu_calls'],0)
        with self.assertRaises(FileExistsError):run(self.source,target,write=cli.write)
    def test_scoped_metal_fact_does_not_promote_parent_cuda_or_default_admission(self):
        r=copy.deepcopy(self.report);rr=r['packing_priorities'][0]['reference_readiness']
        rr['retained_scope']=dict(suite='actual-scoped-suite',inputs=3,metal_verified=True,cuda_verified=False,scope='three fixed inputs')
        p=plan(r);proof=next(x for x in p['operator_families'][0]['scoped_suites'] if x['suite']=='actual-scoped-suite')
        self.assertTrue(proof['metal_verified']);self.assertFalse(proof['cuda_verified'])
        self.assertFalse(p['operator_families'][0]['default_admission_changed']);self.assertFalse(p['gpu_admission_verified'])

if __name__=='__main__':unittest.main()
