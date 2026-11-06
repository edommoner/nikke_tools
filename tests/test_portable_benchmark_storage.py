"""Migration must preserve byte evidence across faults and repeated operations."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_capture_storage as core
import portable_benchmark_storage as storage


class BundleTests(unittest.TestCase):
    def test_preflight_budgets_entire_run_and_rejects_low_space(self):
        with patch.object(core,'require_space') as check:
            size=core.benchmark_space_preflight('.',10,20,[5,2],7)
            self.assertEqual(size,4*(2*7+7*4*1024*2)*30+4*(2*(2+7*4)))
            check.assert_called_once_with('.',size)
        with patch.object(core.shutil,'disk_usage',return_value=type('Usage',(),dict(free=100))()):
            with self.assertRaisesRegex(ValueError,'Insufficient'):core.require_space('.',101,reserve=0)

    def fixture(self,root):
        data=(bytes(range(256))*1000)+os.urandom(4096)
        src=root/'raw';src.write_bytes(data)
        anchor=dict(path='raw',size=len(data),sha256=hashlib.sha256(data).hexdigest(),evidence_sha256='a'*64,report_sha256='b'*64)
        return src,root/'bundle',anchor,data

    def test_multichunk_roundtrip_resume_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td,patch.object(core,'CHUNK',127):
            root=Path(td);src,bundle,a,data=self.fixture(root)
            core.archive_bundle(src,bundle,a)
            self.assertEqual(src.read_bytes(),data)
            self.assertEqual(core.archive_bundle(src,bundle,a)['anchor'],a)
            core.restore_bundle(bundle,a,root/'restored')
            self.assertEqual((root/'restored').read_bytes(),data)
            with self.assertRaises(ValueError):core.restore_bundle(bundle,a,src)

    def test_failure_before_publication_and_after_publication_can_resume(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src,bundle,a,data=self.fixture(root)
            with patch.object(core,'write_synced_json',side_effect=OSError('receipt failure')):
                with self.assertRaises(OSError):core.archive_bundle(src,bundle,a)
            self.assertFalse(bundle.exists());self.assertEqual(src.read_bytes(),data)
            with patch.object(core,'sync_directory',side_effect=[None,OSError('publication interrupted')]):
                with self.assertRaises(OSError):core.archive_bundle(src,bundle,a)
            self.assertTrue(bundle.exists())
            self.assertEqual(core.archive_bundle(src,bundle,a)['anchor'],a)

    def test_corrupt_archive_or_anchor_refuses_restore(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src,bundle,a,data=self.fixture(root)
            core.archive_bundle(src,bundle,a)
            with self.assertRaises(ValueError):core.verify_bundle(bundle,dict(a,sha256='0'*64))
            (bundle/'payload.gz').write_bytes(b'broken')
            with self.assertRaises(ValueError):core.restore_bundle(bundle,a,root/'restored')
            self.assertFalse((root/'restored').exists());self.assertEqual(src.read_bytes(),data)

    def test_source_mutation_symlink_hardlink_and_space_failure_retain_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src,bundle,a,data=self.fixture(root)
            try:(root/'symlink').symlink_to(src)
            except OSError:
                if os.name!='nt':raise
            else:
                with self.assertRaises(ValueError):core.archive_bundle(root/'symlink',bundle,a)
            os.link(src,root/'hardlink')
            with self.assertRaises(ValueError):core.archive_bundle(src,bundle,a)
            (root/'hardlink').unlink()
            with patch.object(core,'require_space',side_effect=ValueError('no space')):
                with self.assertRaises(ValueError):core.archive_bundle(src,bundle,a)
            original=core.regular_signature;calls=0
            def changed(path):
                nonlocal calls
                calls+=1
                result=original(path)
                if calls==2:result['st_mtime_ns']+=1
                return result
            with patch.object(core,'regular_signature',side_effect=changed):
                with self.assertRaisesRegex(ValueError,'changed'):core.archive_bundle(src,bundle,a)
            self.assertFalse(bundle.exists());self.assertEqual(src.read_bytes(),data)


class LegacyMigrationTests(unittest.TestCase):
    def test_running_benchmark_or_gpu_execution_blocks_migration(self):
        for command in ('123 /usr/bin/python3 -u research/benchmark-enemy-target-scalar.py',
                        '456 /repo/.venv/bin/python scripts/nikke_gpu.py run --capture test'):
            with patch.object(storage.subprocess,'check_output',return_value=command):
                with self.assertRaisesRegex(ValueError,'active'):storage.ensure_idle()

    def test_batched_input_size_uses_historical_logical_header(self):
        e=dict(transport=dict(input_bytes=108,output_bytes=200,cases=3),
               dispatches=[dict(transport=dict(input_bytes=68,cases=2)),dict(transport=dict(input_bytes=40,cases=1))],
               logical_input_hash='uint32 total count followed by all ordered program words; per-dispatch headers excluded')
        self.assertEqual(storage.evidence_size(e,'input.bin'),104)
        self.assertEqual(storage.evidence_size(e,'readback.bin'),200)
        e['logical_input_hash']='unknown'
        with self.assertRaises(ValueError):storage.evidence_size(e,'input.bin')

    def fixture(self,root):
        repo=root/'repo';research=repo/'research';research.mkdir(parents=True)
        folder='test-benchmark';base=research/'portable-build'/folder;entries=[]
        for label in ('work-0-control','full-core-control'):
            capture=base/label;capture.mkdir(parents=True)
            e=dict(transport={})
            for name,key,sizekey in [('input.bin','input_sha256','input_bytes'),('readback.bin','output_sha256','output_bytes')]:
                data=(label+name).encode()*1500;(capture/name).write_bytes(data)
                e[key]=hashlib.sha256(data).hexdigest();e['transport'][sizekey]=len(data)
            (capture/'evidence.json').write_text(json.dumps(e))
            entries.append(dict(captured=str(capture),input_sha256=e['input_sha256'],output_sha256=e['output_sha256']))
        (research/'report-benchmark.json').write_text(json.dumps(dict(passed=True,samples=entries)))
        return repo,root/'archives',[(folder,'report-benchmark.json')]

    def quiet(self,*a,**kw):pass

    def test_inventory_archive_remove_restore_relocation_and_resume(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td))
            m=storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            self.assertEqual(len(m['files']),4);self.assertEqual(sum(r['selected'] for r in m['files']),2)
            with storage.locked(archive):
                with self.assertRaisesRegex(ValueError,'Another'):
                    with storage.locked(archive):pass
                first=storage.migrate(archive,progress=self.quiet)
                self.assertEqual(first['removed_files'],0)
                result=storage.migrate(archive,remove_original=True,progress=self.quiet)
                self.assertEqual(result['removed_files'],2);self.assertEqual(result['kept_raw_files'],2)
                self.assertEqual(storage.migrate(archive,remove_original=True,progress=self.quiet)['removed_files'],2)
                row=next(r for r in m['files'] if r['selected'])
                storage.restore(archive,row['path'])
                self.assertEqual(core.file_digest(repo/row['path']),row['sha256'])
                storage.migrate(archive,remove_original=True,progress=self.quiet)
            relocated=repo.with_name('moved');repo.rename(relocated)
            storage.restore(archive,row['path'],repository=relocated)
            self.assertEqual(core.file_digest(relocated/row['path']),row['sha256'])

    def test_changed_report_or_corrupted_archive_never_removes_raw(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td));m=storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            storage.migrate(archive,progress=self.quiet)
            row=next(r for r in m['files'] if r['selected']);bundle=storage.bundle_path(archive,row)
            (bundle/'receipt.json').write_text('{')
            with self.assertRaises(ValueError):storage.migrate(archive,remove_original=True,progress=self.quiet)
            self.assertTrue((repo/row['path']).exists())
            (repo/row['report']).write_text('{}')
            with self.assertRaisesRegex(ValueError,'Preserved'):storage.migrate(archive,remove_original=True,progress=self.quiet)

    def test_full_status_also_checks_retained_timing_originals(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td));m=storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            storage.migrate(archive,progress=self.quiet)
            row=next(r for r in m['files'] if r['selected'])
            (repo/row['path']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Retained'):storage.status(archive,verify=True)

    def test_cleanup_gate_fails_until_raw_removed_and_fast_check_detects_corruption(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td));m=storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            self.assertFalse(storage.storage_check(repo,storage=archive,require_archived=True)['passed'])
            storage.migrate(archive,remove_original=True,progress=self.quiet)
            with patch.object(core,'decompress',side_effect=AssertionError('Fast check must not expand raw')):
                result=storage.storage_check(repo,storage=archive,require_archived=True)
            self.assertTrue(result['passed']);self.assertEqual(result['archives']['raw_files_requiring_restore'],2)
            self.assertFalse(result['archives']['all_archives_verified'])
            row=next(r for r in m['files'] if r['selected'])
            (storage.bundle_path(archive,row)/'payload.gz').write_bytes(b'broken')
            with self.assertRaisesRegex(ValueError,'Compressed'):storage.storage_check(repo,storage=archive)

    def test_storage_budget_and_deep_check_arguments_fail_closed(self):
        with self.assertRaises(ValueError):storage.storage_check('.',needed=-1)
        with self.assertRaises(ValueError):storage.storage_check('.',verify=True)
        with self.assertRaises(ValueError):storage.storage_check('.',require_archived=True)

    def test_external_reference_pins_raw_and_changed_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td))
            capture=repo/'research/portable-build/test-benchmark/work-0-control'
            (repo/'research/consumer.json').write_text(json.dumps(dict(captured=str(capture))))
            m=storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            self.assertFalse(any(r['selected'] for r in m['files']))
            (archive/'inventory.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Inventory'):storage.status(archive)

    def test_removed_state_is_recovered_after_journal_failure(self):
        with tempfile.TemporaryDirectory() as td,patch.object(storage,'ensure_idle'),patch.object(storage.subprocess,'check_output',return_value='test-commit'):
            repo,archive,targets=self.fixture(Path(td));storage.inventory(repo,archive,targets=targets,progress=self.quiet)
            actual=storage.journal
            def fail(storage_path,event,row,**kw):
                if event=='removed':raise OSError('interrupted after unlink')
                return actual(storage_path,event,row,**kw)
            with patch.object(storage,'journal',side_effect=fail):
                with self.assertRaises(OSError):storage.migrate(archive,remove_original=True,progress=self.quiet)
            self.assertEqual(storage.migrate(archive,remove_original=True,progress=self.quiet)['removed_files'],2)

    def test_torn_last_journal_record_is_preserved_and_repaired(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'events.jsonl';path.write_bytes(b'{"event":"old"}\n{"event":')
            storage.journal(root,'verified',dict(path='test.bin'))
            records=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([r['event'] for r in records],['old','verified'])
            self.assertEqual(len(list(root.glob('incomplete-event-*.json'))),1)


if __name__=='__main__':unittest.main()
