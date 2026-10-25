"""Actual full original definitions classify duplicate restrictions without battle."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from portable_original_identity_inventory import inspect
class IdentityInventoryTests(unittest.TestCase):
    def test_all_original_profiles_are_audited_without_battle_or_packing(self):
        from calculator import timeline
        import portable_runtime,portable_backend
        def forbidden(*args,**kwargs):raise AssertionError('Static identity audit cannot run or pack battle')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'build',forbidden):result=inspect()
        self.assertEqual(result['profiles'],266)
        self.assertEqual({row['character'] for row in result['duplicate_groups']},{'하란','쿠루미'})
        self.assertEqual(result['nonperiodic_duplicate_groups'],[])
        self.assertEqual(result['nonperiodic_admission_restriction'],'unobserved-restriction')
        self.assertFalse(result['gpu_supported'])
if __name__=='__main__':unittest.main()
