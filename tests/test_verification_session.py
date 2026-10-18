import sys, types, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verification_session import VerificationSession

def comparator(device,name,body,extra,backend):
    device.calls+=1
    body['changed']=True
    return {'passed':extra.get('passed',True),'checks':{'witness':True},'backend':backend}

class Device:
    def __init__(self):self.calls=0;self.closed=False
    def close(self):self.closed=True

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.s=VerificationSession(Device);self.s.fingerprint=lambda:1
        self.oracle=types.SimpleNamespace(compare=comparator)
    def tearDown(self):self.s.close()
    def test_identical_comparisons_reuse_execution_preserve_assertions_and_inputs(self):
        body={'value':[1,2]};r=self.s.compare(self.oracle,'a',body,{})
        r['checks']['witness']=False
        self.assertTrue(self.s.compare(self.oracle,'a',body,{})['checks']['witness'])
        self.assertEqual(body,{'value':[1,2]})
        self.assertEqual(self.s.stats()['reused_exact_cases'],1)
        self.assertEqual(self.s.device.calls,1)
    def test_name_witness_backend_and_input_changes_never_reuse(self):
        for name,body,extra,backend in [('a',{}, {},'native'),('b',{}, {},'native'),
            ('a',{'v':1},{},'native'),('a',{}, {'v':1},'native'),('a',{}, {},'ptx')]:
            self.s.compare(self.oracle,name,body,extra,backend)
        self.assertEqual(self.s.executed,5)
    def test_failed_comparisons_and_source_epoch_changes_are_not_reused(self):
        for _ in range(2):self.s.compare(self.oracle,'a',{}, {'passed':False})
        self.s.compare(self.oracle,'b',{}, {})
        self.s.fingerprint=lambda:2
        self.s.compare(self.oracle,'b',{}, {})
        self.assertEqual(self.s.executed,4)
    def test_device_is_reused_and_closed(self):
        self.s.compare(self.oracle,'a',{},{});device=self.s.device
        self.s.compare(self.oracle,'b',{},{});self.s.close()
        self.assertEqual(device.calls,2);self.assertTrue(device.closed)

if __name__=='__main__':unittest.main()
