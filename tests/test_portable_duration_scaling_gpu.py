"""Static tagged reference union, private scope and immutable source guards."""
import array,importlib.util,struct,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import validate_effect,UnsupportedPortable
from portable_reference_specs import duration_reference
from portable_scratch_layout import verify
from portable_duration_scaling_source_contract import project_sources

def adapter():
    s=importlib.util.spec_from_file_location('duration_gpu_test',ROOT/'research/verify-world-duration-scaling-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class DurationScalingGPUTests(unittest.TestCase):
    def test_all47_static_inputs_keep_reference_marker_and_rejection_fields(self):
        m=adapter();rows,data=m.prepare();self.assertEqual(len(rows),47);self.assertEqual(sum(r[2] is not None for r in rows),40);self.assertEqual(len(data),4+47*104400*4)
        for name,w,d in rows[:40]:self.assertTrue(any(w[L['REFERENCE_DEFINITION_BASE']+i*4+3]&0x80000000 for i in range(w[1])))
        for name,w,d in rows[40:]:self.assertIsNone(d);m.validate_rejection([64],name)
        self.assertTrue(verify(L,mode='duration-scaling-diagnostic')['verified'])
    def test_host_rejects_nonprivate_wrong_kind_and_malformed_reference(self):
        from portable_duration_scaling_cases import synthetic_fixtures
        e=synthetic_fixtures()[0]['effects'][-1]
        for changes in (dict(duration_scaling='prob'),dict(type='instant'),dict(duration_scaling_ref=3)):
            with self.assertRaises(ValueError):duration_reference(dict(e,**changes))
        for combat,world in ((None,True),({},False)):
            with self.assertRaises(UnsupportedPortable):validate_effect(e,combat=combat,world_frame=world)
        validate_effect(e,combat={},world_frame=True);self.assertEqual(duration_reference(dict(e,duration_scaling_ref='')),'')
    def test_reviewed_helper_and_expiry_order_reject_mutations(self):
        project_sources(ROOT)
        for name,old,new in [('gpu/duration_scaling_runtime.slang','f64Mul(base,present?count:uint64_t(0))','f64Mul(base,ONE)'),('gpu/dispatch_phases.slang','definitionExpiry(s,sourceRow,f.time)','definitionExpiry(s,row,f.time ^ F64_SIGN)'),('gpu/event_runtime.slang','passiveDefinitionExpiry(s,j,when)','definition_duration(s.inputBase,j)')]:
            text=(ROOT/name).read_text();self.assertEqual(text.count(old),1)
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(old,new,1)})
    def test_diagnostic_decode_accepts_array_and_list_without_masking_fields(self):
        m=adapter();block=[0]*786432;h=L['NATIVE_DIAG_BASE'];block[h:h+3]=[0x44555331,1,0];at=h+16;block[at:at+4]=[0,0,1,0]
        for offset,value in ((4,.5),(6,.25),(8,0.),(10,.5)):block[at+offset:at+offset+2]=struct.unpack('<II',struct.pack('<d',value))
        block[at+12]=0x80000000;words=[0]*104400;words[L['REFERENCE_DEFINITION_BASE']+3]=0x80000000
        row=dict(definition=0,owner=0,time=.5,duration=.25,duration_values=None,reads=[dict(value=None)],expires_at=.5)
        expected=dict(duration=dict(checks=[row]));domain=({'name':'container-guard'},None,None,words)
        with patch.object(m,'compare',return_value=expected):
            for data in (block,array.array('I',block)):self.assertEqual(m.compare_diagnostic(data,domain),expected)
            block[at+9]=0x80000000
            with self.assertRaises(AssertionError):m.compare_diagnostic(array.array('I',block),domain)
            block[at+9]=0
            block[at+3]=1
            with self.assertRaises(AssertionError):m.compare_diagnostic(array.array('I',block),domain)

if __name__=='__main__':unittest.main()
