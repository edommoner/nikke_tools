import importlib.util,tempfile,unittest,zipfile
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'scripts/setup-engine.py'
spec=importlib.util.spec_from_file_location('portable_engine_setup',path);setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
TMP=path.parents[1]/'research/portable-build/test-tmp';TMP.mkdir(parents=True,exist_ok=True)


class EngineSetupTests(unittest.TestCase):
    def archive(self,root,*,revision=setup.REVISION,extra=None,prefix=setup.PREFIX):
        path=root/'source.zip'
        with zipfile.ZipFile(path,'w') as z:
            z.comment=revision.encode()
            for name in setup.REQUIRED:z.writestr(f'{prefix}/{name}','pinned fixture')
            if extra:z.writestr(extra,'invalid')
        return path

    def test_offline_install_and_existing_engine_preserved(self):
        for prefix in (setup.PREFIX,'nikke-calc-master'):
            with self.subTest(prefix=prefix),tempfile.TemporaryDirectory(dir=TMP) as d:
                root=Path(d);archive=self.archive(root,prefix=prefix)
                self.assertFalse(setup.setup(root,archive)['already_present'])
                marker=root/'research/upstream/nikke-calc-master/runner/sim.py';marker.write_text('local preserved')
                self.assertTrue(setup.setup(root,archive)['already_present']);self.assertEqual(marker.read_text(),'local preserved')

    def test_reject_wrong_revision_and_escaping_archive_before_install(self):
        for revision,extra in [('wrong',None),(setup.REVISION,f'{setup.PREFIX}/../escaped'),(setup.REVISION,'/absolute')]:
            with self.subTest(extra=extra),tempfile.TemporaryDirectory(dir=TMP) as d:
                root=Path(d);archive=self.archive(root,revision=revision,extra=extra)
                with self.assertRaises(ValueError):setup.setup(root,archive)
                self.assertFalse((root/'research/upstream/nikke-calc-master').exists())


if __name__=='__main__':unittest.main()
