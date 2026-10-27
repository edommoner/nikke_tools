"""Full-runtime opt-in source and arena contract, before device certification."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_logical_geometry_source_contract import project_sources
from portable_logical_geometry_wire import check_schema,input_regions,output_regions,SCRATCH
from portable_arena_specs import audit_regions

class LogicalGeometryRuntime(unittest.TestCase):
    def test_exact_historical_projection_and_shared_receipt_tail(self):
        sources=project_sources(ROOT)
        self.assertEqual(len(sources),5)
        self.assertNotIn('PORTABLE_COORDINATE_LOGICAL_ACTORS',''.join(sources.values()))

    def test_full_input_and_output_have_disjoint_owners(self):
        check_schema(ROOT)
        rows=input_regions()+output_regions()
        audit=audit_regions(rows,115680,SCRATCH['OUTPUT_WORDS'])
        self.assertTrue(audit['address_plan_verified'])
        for domain,words in [('input',115680),('output',2032000)]:
            owned=sorted((r.base,r.end) for r in rows if r.domain==domain)
            self.assertEqual(owned[0][0],0);self.assertEqual(owned[-1][1],words)
            self.assertTrue(all(a[1]==b[0] for a,b in zip(owned,owned[1:])))

    def test_history_uses_common_capacity_and_addresses(self):
        from portable_skill_history import shader_layout
        common=shader_layout().splitlines();logical=(ROOT/'gpu/logical_actor_geometry_history.slang').read_text().splitlines()
        self.assertEqual(common[1:-1],logical[1:-1])
        self.assertIn('0x4c414731U',logical[-1]);self.assertNotIn('+13U',logical[-1])

    def test_modified_or_added_source_poison_cannot_enter_historical_projection(self):
        for name in ('app/portable_specs.py','gpu/coordinate_sampling_runtime.slang','gpu/logical_actor_geometry_runtime.slang','gpu/coordinate_group_actor_receipt.slang'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed source\n'})

if __name__=='__main__':unittest.main()
