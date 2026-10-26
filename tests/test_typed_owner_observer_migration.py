"""Empty witness migration cannot change another CPU value or any input."""
import copy,errno,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_typed_owner_observer_migration as migration
s=importlib.util.spec_from_file_location('observer_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class MigrationTests(unittest.TestCase):
    def fixture(self):
        names=['coordinate-typed-owner/'+str(i) for i in range(5)];native=dict(battle=dict(enemy_fields=dict(queries=[],nonzero_immunity_used=[])),unchanged='state');prior=copy.deepcopy(native);del prior['battle']['enemy_fields']['nonzero_immunity_used'];data=b'count'+b'word'*5
        rows=[dict(name=n,input_sha256=cli.sha(data[4+i*4:8+i*4]),native_sha256=migration.digest(prior)) for i,n in enumerate(names)];old=dict(package_id=migration.SOURCE_PACKAGE_ID,purpose='development',selected_cases=[],suite=migration.SUITE,files=[],golden=dict(input_sha256=cli.sha(data),source_sha256={},entries=rows))
        adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1));api=SimpleNamespace(ROOT=ROOT,verify_saved_package=lambda p:old,forbid_gpu=cli.contextlib.nullcontext,open_suite=lambda m:adapter,prepare_entries=lambda a,m:([(n,[0],i) for i,n in enumerate(names)],data),sha=cli.sha,native_value=lambda a,d:copy.deepcopy(native))
        return old,api,native,dict(case_names=names)
    def test_exact_addition_binds_old_and_new_native_hashes_and_still_requires_fresh_replay(self):
        old,api,native,spec=self.fixture()
        with patch.object(migration,'check_sources',return_value=spec):g,r=migration.baseline(api,migration.SUITE,ROOT,[])
        self.assertEqual(r['native_domains_recomputed'],5);self.assertTrue(r['full_fresh_saved_replay_required']);self.assertFalse(r['calculation_verified']);self.assertEqual(r['gpu_calls'],0)
        current=dict(suite=migration.SUITE,files=[],golden=g,baseline_migration=r)
        with patch.object(migration,'check_sources',return_value=spec):self.assertEqual(migration.verify(api,old,current),r['receipt'])
    def test_nonempty_witness_or_other_native_change_cannot_use_this_mapping(self):
        for mode in ('nonempty','other'):
            old,api,n,spec=self.fixture()
            if mode=='nonempty':n['battle']['enemy_fields']['nonzero_immunity_used']=[dict(used=1)]
            else:n['unchanged']='changed'
            with patch.object(migration,'check_sources',return_value=spec),self.assertRaises(ValueError):migration.baseline(api,migration.SUITE,ROOT,[])
    def test_another_golden_or_input_change_is_not_a_witness_migration(self):
        old,api,n,spec=self.fixture()
        with patch.object(migration,'check_sources',return_value=spec):g,r=migration.baseline(api,migration.SUITE,ROOT,[])
        for key in ('input_sha256','source_sha256'):
            current=dict(suite=migration.SUITE,files=[],golden=copy.deepcopy(g),baseline_migration=r);current['golden'][key]='changed'
            with patch.object(migration,'check_sources',return_value=spec),self.assertRaises(ValueError):migration.verify(api,old,current)
    def test_spec_cannot_allow_an_unrelated_gpu_or_canonical_change(self):
        old,api,native,_=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/migration.SPEC;path.parent.mkdir(parents=True)
            spec=dict(case_names=['coordinate-typed-owner/'+str(i) for i in range(5)],changes={'gpu/unreviewed.slang':dict(before=None,after='hash')})
            path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'cannot change GPU'):migration.check_sources(root,old,dict(suite=migration.SUITE,files=[]))

    def test_source_package_is_fixed_before_reading_any_spec(self):
        old,api,n,spec=self.fixture();old['package_id']='other'
        with self.assertRaisesRegex(ValueError,'Exact full'):migration.check_sources(Path('unused'),old,dict(suite=migration.SUITE))

class SavedSharingTests(unittest.TestCase):
    def test_real_hardlinks_preserve_every_byte_and_default_copy_stays_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir();shared=root/'shared';shared.mkdir();copied=root/'copied';copied.mkdir()
            names=('input.bin','readback.bin','evidence.json','generated.cu','generated.metal')
            for i,n in enumerate(names):(source/n).write_bytes(bytes([i])*100)
            before=cli.file_records(source,names);cli.copy_replay_inputs(shared,source,reuse_source_bytes=True);cli.copy_replay_inputs(copied,source)
            self.assertEqual(cli.file_records(source,names),before);self.assertEqual(cli.file_records(shared,names),before)
            for n in names:self.assertEqual((source/n).stat().st_ino,(shared/n).stat().st_ino);self.assertNotEqual((source/n).stat().st_ino,(copied/n).stat().st_ino)
            self.assertFalse(cli.load(shared/'shared-inputs.json')['calculation_verified'])
    def test_sharing_never_falls_back_to_unbudgeted_cross_device_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir();dest=root/'dest';dest.mkdir()
            for n in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal'):(source/n).write_bytes(b'bytes')
            with patch.object(cli.os,'link',side_effect=OSError(errno.EXDEV,'injected cross-device')),self.assertRaises(OSError):cli.copy_replay_inputs(dest,source,reuse_source_bytes=True)
            self.assertEqual(list(dest.iterdir()),[])

if __name__=='__main__':unittest.main()
