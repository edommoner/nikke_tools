"""Source-host envelopes cannot replace native semantics, or prove preservation."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import portable_partitioned_join as join
from portable_comparison_groups import partition
from test_portable_partitioned_cuda_receipt import c


class JoinTests(unittest.TestCase):
    def fixture(self):
        e=c.load(ROOT/'tests/fixtures/resident-current-envelope-v1-summary.json')
        g=c.load(ROOT/c.SUITES['coordinate-resident-frames']['golden']);m=dict(package_id='witness-owner',golden=g)
        facts=[];groups=[]
        for i,indices in enumerate(partition(106,8)):
            n=sum(k<63 for k in indices)
            f=dict(child_pid=900001+i,case_indices=indices,input_count=len(indices),native_cases=n,elapsed_seconds=1.)
            facts.append(f)
            groups.append(dict(calculation_verified=False,comparison_subset_verified=True,case_indices=indices,child_pid=f['child_pid'],
                elapsed_seconds=1.,input_count=len(indices),total_input_count=106,native_oracles=n,entries=[g['entries'][k] for k in indices],
                mismatches=[],generated_normalized=g['generated_normalized'],input_sha256=g['input_sha256'],
                raw_output_sha256=e['raw_output_sha256'],logical_output_sha256=g['output_sha256'],live_parent_receipt_present=False,gpu_calls=0))
        comparison=dict(calculation_verified=True,entries=g['entries'],input_count=106,native_oracles=63,input_sha256=g['input_sha256'],
            raw_output_sha256=e['raw_output_sha256'],logical_output_sha256=g['output_sha256'],independent_comparison=dict(
            schema='independent-metal-audit-groups-v1',input_count=106,native_cases=63,groups=facts,child_pids=[f['child_pid'] for f in facts],live_parent_receipt_present=False,per_group_timeout_seconds=180))
        w=dict(schema='partitioned-identical-wire-native-witness-v1',package_id=m['package_id'],source_package_id=e['source_package_id'],
            original_cuda_capture_observed=False,witness_calculation_verified=True,conditional_cuda_native_equivalence_verified=True,
            pending_original_cuda_envelope_audit=True,calculation_verified=False,comparison=comparison,
            wire=dict(output_bytes=e['output_bytes'],metal_cache_checks=[{}]*7))
        return m,w,groups,e

    def test_complete_separate_proofs_validate_without_promoting_environment_preservation(self):
        m,w,g,e=self.fixture();self.assertTrue(join.validate(m,w,g,e,63))
        self.assertFalse(e['original_environment_preservation_verified']);self.assertFalse(e['audit_preservation_verified'])

    def test_source_bytes_native_rows_all_groups_and_gpu_free_envelope_are_required(self):
        for kind in ('missing-group','duplicate-pid','native-row','native-count','raw','input','source','generation','unseen','gpu','claim','sequence','timeout','parent-cache','subset','status'):
            with self.subTest(kind=kind):
                m,w,g,e=copy.deepcopy(self.fixture())
                if kind=='missing-group':g.pop()
                elif kind=='duplicate-pid':w['comparison']['independent_comparison']['child_pids'][1]=900001
                elif kind=='native-row':g[0]['entries'][0]=dict(g[0]['entries'][0],native_sha256='0'*64)
                elif kind=='native-count':w['comparison']['native_oracles']=62
                elif kind=='raw':e['raw_output_sha256']='0'*64
                elif kind=='input':e['input_sha256']='0'*64
                elif kind=='source':e['source_package_id']='other'
                elif kind=='generation':g[0]['generated_normalized']={}
                elif kind=='unseen':e['original_capture_observed']=False
                elif kind=='gpu':e['gpu_calls']=True
                elif kind=='claim':e['original_claims_modified']=True
                elif kind=='sequence':e['original_sequence_arguments_verified']=False
                elif kind=='timeout':e['audit_timed_out']=True
                elif kind=='parent-cache':g[0]['live_parent_receipt_present']=True
                elif kind=='subset':g[0]['calculation_verified']=True
                else:g[0]['mismatches']=[dict(reason='status mismatch')]
                with self.assertRaises(ValueError):join.validate(m,w,g,e,63)


if __name__=='__main__':unittest.main()
