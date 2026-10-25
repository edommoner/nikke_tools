"""Source reuse refuses changed kernels, tools and consumers; never certifies CUDA."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_source_reuse import compatible,CONSUMERS
class SourceReuseTests(unittest.TestCase):
    def sample(self):return dict(source_sha256={'gpu/fixed.slang':'source'},identity={'compiler':'pinned','source':'fixed'},artifacts={'cuda':'cu','metal':'msl','cuda-reflection':'cr','metal-reflection':'mr'},consumers={n:'digest' for n in CONSUMERS},cache_hit=True,compiler_invocations=0)
    def test_case_metadata_is_not_a_gpu_source_change_or_calculation_proof(self):
        a=self.sample();b=copy.deepcopy(a);a.update(package_id='old',cases=6,cache_hit=False,compiler_invocations=2);b.update(package_id='new',cases=3)
        r=compatible(a,b);self.assertTrue(r['source_reuse_verified']);self.assertTrue(r['candidate_generation_cache_hit']);self.assertFalse(r['cuda_compiler_cache_hit_verified']);self.assertFalse(r['metal_pipeline_cache_hit_verified']);self.assertFalse(r['calculation_verified'])
    def test_kernel_compiler_or_artifact_changes_refuse_reuse(self):
        a=self.sample()
        for field in ('source_sha256','identity','artifacts'):
            b=copy.deepcopy(a);b[field]['changed']='different'
            with self.subTest(field=field),self.assertRaises(ValueError):compatible(a,b)
    def test_missing_or_changed_transport_and_cache_consumers_refuse_reuse(self):
        a=self.sample()
        for name in CONSUMERS:
            for missing in (False,True):
                b=copy.deepcopy(a)
                if missing:b['consumers'].pop(name)
                else:b['consumers'][name]='changed'
                with self.subTest(name=name,missing=missing),self.assertRaises(ValueError):compatible(a,b)
if __name__=='__main__':unittest.main()
