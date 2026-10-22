import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_parts_skill_specs import verify_layout,validate,BASE,CAPACITY,END
from portable_specs import LIMITS as L
class PartsSkillGpuTests(unittest.TestCase):
    def test_native_cleared_observation_uses_real_targets_and_open_lifetime(self):
        from types import SimpleNamespace as N
        from world_schedule_native import cleared_run
        r=N(opens=0,p=N(until_cleared=True,summon=None),targets=[N(destroyed=True,spec=N(breakable=True))])
        self.assertFalse(cleared_run(r));r.opens=2;self.assertTrue(cleared_run(r))
        r.targets[0].destroyed=False;self.assertFalse(cleared_run(r))
        r.targets[0].destroyed=True;r.p.until_cleared=False;self.assertFalse(cleared_run(r))
    def test_receipt_bank_capacity_and_no_periodic_or_diagnostic_overlap(self):
        self.assertEqual(verify_layout(L),dict(base=781328,end=785424,capacity=2048,words=4096))
        self.assertEqual(BASE+2*(CAPACITY-1)+2,END)
        for key,value in [('LANDINGS',2049),('LANDING_WORDS',12),('WORLD_PERIODIC_HEAD_BASE',BASE),('WORLD_RELOAD_OUTPUT_WORDS',END)]:
            bad=dict(L);bad[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):verify_layout(bad)
    def test_part_marker_scope_and_types(self):
        for marker in (False,True):self.assertTrue(validate(dict(type='damage',hits_parts=marker),combat={},world_frame=True))
        for marker in (1,None,'true',[]):
            with self.subTest(marker=marker),self.assertRaises(ValueError):validate(dict(type='damage',hits_parts=marker),combat={},world_frame=True)
        with self.assertRaises(ValueError):validate(dict(type='buff',hits_parts=True),combat={},world_frame=True)
        with self.assertRaises(ValueError):validate(dict(type='damage',hits_parts=True),combat={},world_frame=False)
    def test_all_reference_cases_remain_and_unported_adapters_reject_explicitly(self):
        spec=importlib.util.spec_from_file_location('parts_gpu_adapter',ROOT/'research/verify-world-parts-skill-short.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertEqual(len(m.fixtures()),43);self.assertEqual(len(m.HOST_REJECT),0)
        entries,data=m.prepare();self.assertEqual(len(entries),46);self.assertEqual(sum(d is not None for _,_,d in entries),41)
        self.assertEqual(len(data),4*(1+46*m.suite.INPUT))
        for name,_,domain in entries:
            if domain is not None:continue
            m.validate_rejection([64],name)
            with self.assertRaises(AssertionError):m.validate_rejection([0],name)
