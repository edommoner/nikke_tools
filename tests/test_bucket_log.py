"""Focused tests for the external S17 CPU observer."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bucket_log', ROOT/'research/team-search/bucket_log.py')
bucket = importlib.util.module_from_spec(SPEC)
_path_before_import = sys.path[:]
_bytecode_before_import = sys.dont_write_bytecode
try:
    SPEC.loader.exec_module(bucket)
finally:
    sys.path[:] = _path_before_import
    sys.dont_write_bytecode = _bytecode_before_import


class BucketTests(unittest.TestCase):
    def test_original_result_identity_and_profile_restore(self):
        result = {'damage': 73, 'is_crit': False, 'crit_frac': .15}
        def calc_damage():
            f1 = f2 = f3 = f4 = f5 = f6 = f7 = 1.
            hit_type = {}; buffs = {}; crit_frac = .15; is_crit = False
            return result
        observer = bucket.BucketLog()
        previous = sys.getprofile()
        self.assertIs(observer.wrapper(calc_damage)(), result)
        self.assertIs(sys.getprofile(), previous)
        self.assertEqual(observer.scalars[0]['factors'], [1.]*7)

    def test_exception_restores_profile(self):
        def fail(): raise ValueError('fixture')
        previous = sys.getprofile()
        with self.assertRaisesRegex(ValueError, 'fixture'):
            bucket.BucketLog().wrapper(fail)()
        self.assertIs(sys.getprofile(), previous)

    def test_tiny_real_fixture_unchanged_and_reconciled(self):
        # Each reference run is isolated exactly as engine_worker requires.
        code = """import json,sys
sys.path.insert(0,'app')
import engine_worker as e
x=e.detail_demo()
b=dict(profile=x['profile'],squad=x['squad'],duration=1,level=400,compute_backend='cpu')
print(json.dumps(b))
"""
        body = json.loads(subprocess.check_output([sys.executable, '-B', '-c', code], cwd=ROOT, text=True))
        values=[]
        for logged in (False, True):
            r=subprocess.run([sys.executable, '-B', str(ROOT/'research/team-search/bucket_log.py'), '--worker'],
                             input=json.dumps(dict(body=body,logged=logged)),cwd=ROOT,text=True,capture_output=True,check=True)
            values.append(json.loads(r.stdout))
        self.assertEqual(values[0]['payload'],values[1]['payload'])
        b=values[1]['buckets']
        self.assertTrue(b['reconciliation'])
        self.assertGreater(b['landed_hits'],0)
        self.assertEqual(sum(b['member_hit_damage'].values()),values[0]['payload']['total_damage'])
        self.assertEqual(sum(g['damage'] for g in b['groups'])+b['uncovered_damage'],values[0]['payload']['total_damage'])

    def test_typed_clone_preserves_factor5_override(self):
        code = """import sys
sys.path.insert(0,'app')
sys.path.insert(0,'research/team-search')
import engine_worker, bucket_log
from calculator import damage
from destructible_damage_policy import calculate
from impact_specs import ActorKind
original=damage.calc_damage
args=dict(base_atk=50000.,buffs={'projectile_dmg_pct':25.},weapon={'damage_coeff':20.},expected=True,kind=ActorKind.PROJECTILE)
plain=calculate(**args)
with bucket_log.BucketLog() as observer:
    import destructible_damage_policy
    wrapped=destructible_damage_policy.calculate(**args)
    assert damage.calc_damage is original
assert plain==wrapped
assert len(observer.scalars)==1
assert observer.scalars[0]['factors'][4]==1.25
assert damage.calc_damage is original
"""
        subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True, text=True, check=True)

    def test_existing_patch_adds_to_scalar_and_list(self):
        body={'squad':['a','b'],'profile':{'chars':{'a':{'equip_skills':{'crit_dmg':[1,2]}},'b':{'equip_skills':{'crit_dmg':4}}}}}
        changed=bucket.perturb(body,'crit_dmg',5)
        self.assertEqual(changed['patches']['a']['equip_skills']['crit_dmg'],8)
        self.assertEqual(changed['patches']['b']['equip_skills']['crit_dmg'],9)
        self.assertNotIn('patches',body)

if __name__=='__main__':unittest.main()
