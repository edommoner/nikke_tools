"""Generation metadata cannot substitute for actual inherited Job inspection."""
import importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_generation_gate as gate
spec=importlib.util.spec_from_file_location('packet_gate_tests',ROOT/'scripts/run-gpu-packet.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
GOOD=dict(in_job=True,priority_class=0x4000,job_memory_limit_bytes=2147483648,job_limit_flags=0x2200,job_peak_memory_bytes=123)

class GenerationGateTests(unittest.TestCase):
    def test_standalone_is_still_rejected_before_native_inspection(self):
        with patch.object(gate,'current_containment') as inspect:
            with self.assertRaisesRegex(ValueError,'Standalone'):gate.verify_packet_generation(ROOT,None,'/tmp/proof')
        inspect.assert_not_called()
    def exercise(self,change=None,facts=None):
        with tempfile.TemporaryDirectory() as d:
            folder=(Path(d)/'stage').resolve();folder.mkdir();out=folder/'proof'
            with patch.dict(os.environ,{'NIKKE_SLANG_GENERATION_CACHE':str(Path(d)/'cache')}):
                plan=packet.recipe('id','generation','cuda',folder,Path(d)/'original',180)
                rows={'recipe.json':plan,'child.json':dict(pid=os.getpid(),ppid=os.getppid(),package_id='id'),'start.json':{},'command.json':dict(argv=['python',str(ROOT/'scripts/run-gpu-packet.py'),'--_child','--capture',str(folder)],base_python='python',cwd=str(ROOT),shell=False,timeout_seconds=180)}
                if change:change(rows)
                for name,row in rows.items():(folder/name).write_text(json.dumps(row))
                # Only replace the package header read; all stage files and recipe
                # validation use real paths and the existing packet implementation.
                original=Path.read_text
                def read(path,*a,**kw):
                    return json.dumps(dict(package_id='id')) if path==ROOT/'gpu-package.json' else original(path,*a,**kw)
                with patch.object(Path,'read_text',read),patch.object(gate,'current_containment',return_value=GOOD if facts is None else facts):
                    return gate.verify_packet_generation(ROOT,folder,out)
    def test_complete_metadata_and_actual_limits_are_both_required(self):
        self.assertTrue(self.exercise()['packet_stage_verified'])
        changes=[lambda r:r.pop('start.json'),lambda r:r['start.json'].update(forged=True),lambda r:r['child.json'].update(pid=-1),lambda r:r['child.json'].update(ppid=-1),lambda r:r['child.json'].update(package_id='other'),lambda r:r['recipe.json'].update(stage='gpu'),lambda r:r['recipe.json'].update(timeout_seconds=181),lambda r:r['recipe.json'].update(memory_limit_mb=4096),lambda r:r['command.json'].update(shell=True),lambda r:r['command.json'].update(argv=['python','other'])]
        for change in changes:
            with self.subTest(change=change),self.assertRaises((ValueError,FileNotFoundError)):self.exercise(change)
    def test_forged_metadata_never_replaces_native_limit_checks(self):
        for change in (dict(in_job=False),dict(priority_class=0x20),dict(job_memory_limit_bytes=None),dict(job_memory_limit_bytes=4294967296),dict(job_limit_flags=0x200)):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'native containment'):self.exercise(facts=dict(GOOD,**change))
        with patch.object(gate.C,'WinDLL',side_effect=OSError('inspection denied'),create=True):
            with self.assertRaisesRegex(OSError,'inspection denied'):gate.current_containment()
    def test_shared_limit_inspector_exposes_flags_only_on_request(self):
        from portable_job_limits import read_job_limits,ExtendedLimitInformation
        import ctypes as C
        class Query:
            def __call__(self,h,k,p,n,returned):
                limits=C.cast(p,C.POINTER(ExtendedLimitInformation)).contents;limits.basic.flags=0x2200;limits.job_mem=2147483648
                C.cast(returned,C.POINTER(C.c_uint32)).contents.value=n;return 1
        from types import SimpleNamespace
        result=read_job_limits(SimpleNamespace(QueryInformationJobObject=Query()),None,include_flags=True)
        self.assertEqual(result['job_limit_flags'],0x2200);self.assertEqual(result['job_memory_limit_bytes'],2147483648)

if __name__=='__main__':unittest.main()
