"""Static packing is auditable without admitting or executing a GPU battle."""
import copy,contextlib,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
import engine_worker
class EntryInventoryTests(unittest.TestCase):
    def prepared(self,name):
        spec=importlib.util.spec_from_file_location('entry_inventory_test_roster',ROOT/'research/audit-world-roster-input.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
        from detail_coverage import body_for
        return engine_worker.evaluate(dict(body_for(policy.roster_for(name),30),burst_gauge_mode='accumulate',_portable_static_inputs=True))











    def test_shared_identity_catalog_remains_nonpacking(self):
        from portable_original_identity_inventory import inspect
        import portable_runtime
        with patch.object(portable_runtime,'compile_program',side_effect=AssertionError('Identity catalog cannot pack')):result=inspect()
        self.assertEqual(result['profiles'],269);self.assertEqual(result['nonperiodic_duplicate_groups'],[])
if __name__=='__main__':unittest.main()
