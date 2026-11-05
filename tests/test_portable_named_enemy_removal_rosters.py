"""The unchanged full profile must actually dispatch the global removal."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_named_enemy_removal_roster_cases import fixtures
from portable_named_enemy_removal_roster_contracts import verify
from world_named_enemy_removal_roster_native import observe
class NamedEnemyRemovalRosterTests(unittest.TestCase):
    def test_original_dispatch_counts_and_no_target_queries(self):
        for c in fixtures():
            n,_=observe(c);verify(c,n)
            n['named_enemy_removal']['selection']['rankings']=[{}]
            with self.assertRaises(AssertionError):verify(c,n)
    def test_entire_profile_packs_without_definition_or_target_rewrite(self):
        s=importlib.util.spec_from_file_location('test_named_removal_real_gpu',ROOT/'research/verify-world-named-enemy-removal-rosters-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,_=m.prepare();self.assertEqual(len(rows),2)
        for _,_,(c,meta,p,w) in rows:
            self.assertEqual(len(meta['effects']),80)
            removals=[r['effect'] for r in p['effects'] if (e:=r['effect']).get('stat')=='remove_named_buff' and str(e.get('target')).startswith('enemies_with_buff:')]
            self.assertEqual(len(removals),1);self.assertEqual(removals[0]['target'],'enemies_with_buff:안티 AT 필드');self.assertNotEqual(removals[0].get('remove_scope'),'target')
if __name__=='__main__':unittest.main()
