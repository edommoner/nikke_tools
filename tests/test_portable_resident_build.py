"""Fresh paired Slang artifacts must exist before resident outputs are published."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_backend as backend
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_portable_resident_layout import document


class ResidentBuildTests(unittest.TestCase):
    def run_build(self,problem=None,windows=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'gpu').mkdir()
            (root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n')
            folder=root/'research/portable-build';folder.mkdir(parents=True)
            local=root/'LocalAppData';(local/'Temp').mkdir(parents=True)
            old={}
            for suffix in ('cu','metal','cu.reflection.json','metal.reflection.json'):
                path=folder/('entry.'+suffix);path.write_bytes(b'previous artifact');old[path]=path.read_bytes()
            calls=[]
            def compiler(args,**kwargs):
                target=args[args.index('-target')+1];calls.append(target)
                output=Path(args[args.index('-o')+1]);reflection=Path(args[args.index('-reflection-json')+1])
                self.assertEqual(output.parent,reflection.parent)
                self.assertNotEqual(output.parent,folder)
                if windows:self.assertEqual(output.parent.parent,local/'Temp')
                self.assertFalse(output.exists());self.assertFalse(reflection.exists())
                if problem=='exit':return subprocess.CompletedProcess(args,1,b'',b'compiler diagnostic')
                output.write_bytes(b'struct Runtime_0\n{ unsigned small; unsigned long long large; };\n' if target=='cuda' else b'metal code')
                if problem=='missing' and target=='metal':pass
                elif problem=='empty' and target=='metal':reflection.write_bytes(b'')
                else:
                    doc=document(target)
                    if problem=='layout' and target=='metal':doc['parameters'][2]['binding']['index']=1
                    reflection.write_text(json.dumps(doc))
                if problem=='source':(root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n// changed\n')
                return subprocess.CompletedProcess(args,0,b'',b'warning retained on failure')
            with patch.object(backend,'ROOT',root),patch.object(backend.subprocess,'run',side_effect=compiler),patch.object(backend.platform,'system',return_value='Windows' if windows else 'Darwin'),patch.dict(os.environ,{'LOCALAPPDATA':str(local),'TEMP':str(folder),'TMP':str(folder)}):
                if problem:
                    with self.assertRaises((RuntimeError,ValueError)) as caught:backend.build('gpu/entry.slang','portableEvents')
                    for path,raw in old.items():self.assertEqual(path.read_bytes(),raw)
                    if problem=='missing':self.assertIn('artifact missing or empty',str(caught.exception));self.assertIn('warning retained',str(caught.exception))
                else:
                    outputs,hashes=backend.build('gpu/entry.slang','portableEvents')
                    self.assertEqual(calls,['cuda','metal'])
                    self.assertEqual(set(outputs),{'cuda','metal'})
                    self.assertIn(b'static_assert(sizeof(Runtime_0) == 16',outputs['cuda'].read_bytes())
                    self.assertEqual(backend.resident_plan('gpu/entry.slang','portableEvents',outputs)['stride'],16)
            self.assertFalse(list(folder.glob('*resident-build-*')))
            self.assertFalse(list((local/'Temp').iterdir()))

    def test_explicit_files_are_validated_and_published(self):self.run_build()

    def test_windows_scratch_uses_os_temp_despite_redirected_child_temp(self):self.run_build(windows=True)

    def test_missing_empty_or_malformed_fresh_reflection_never_reuses_old_files(self):
        for problem in ('missing','empty','layout'):
            with self.subTest(problem=problem):self.run_build(problem)

    def test_compiler_failure_or_source_change_keeps_previous_artifacts(self):
        for problem in ('exit','source'):
            with self.subTest(problem=problem):self.run_build(problem)


if __name__=='__main__':unittest.main()
