"""Low storage must stop before a GPU claim, not shrink a workload."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_capture_storage import space_status

class StorageBudgetTests(unittest.TestCase):
    def test_exact_boundary_and_invalid_budgets(self):
        with tempfile.TemporaryDirectory() as folder,patch('portable_capture_storage.shutil.disk_usage',return_value=types.SimpleNamespace(free=110)):
            self.assertTrue(space_status(Path(folder)/'new'/'capture',100,reserve=10)['passed'])
            self.assertFalse(space_status(folder,101,reserve=10)['passed'])
            for needed,reserve in [(True,0),(-1,0),(1,-1),(1,1.)]:
                with self.assertRaises(ValueError):space_status(folder,needed,reserve=reserve)
    def manifest(self):return dict(suite='destructible-original-battle',golden=dict(entries=[{}]*8))

if __name__=='__main__':unittest.main()
