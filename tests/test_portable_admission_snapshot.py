"""No GPU proof from bytes alone; immutable archives detect every changed input."""
import copy,json,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_admission_snapshot as snap


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        self.sources=self.root/'sources';self.sources.mkdir();self.out=self.root/'snapshot.zip'
        self.bind=dict(owner_package_id='a'*64,controller_package_id='b'*64,transaction_nonce='c'*32,input_sha256='d'*64,artifact_sha256='e'*64,future_capture=str(self.root/'future'))
        rows=[]
        for name,data in [('input.bin',b'input'),('copy.bin',b'input'),('image.cubin',b'artifact'),('empty',b'')]:
            (self.sources/name).write_bytes(data);rows.append(dict(root=str(self.sources),path=name,bytes=len(data),sha256=snap.digest(data)))
        self.inventory=dict(schema=snap.INVENTORY,binding=self.bind,files=rows)
    def freeze(self):return snap.freeze(self.inventory,self.out)
    def test_deduplicates_storage_but_keeps_all_sources_and_requires_external_anchor(self):
        report=self.freeze();self.assertEqual((report['input_files'],report['unique_blobs']),(4,3))
        self.assertTrue(report['snapshot_bytes_verified']);self.assertFalse(report['admission_verified']);self.assertFalse(report['calculation_verified']);self.assertEqual(report['gpu_calls'],0)
        with snap.Snapshot(self.out,report['snapshot_sha256'],expected_binding=self.bind) as reader:
            for row in self.inventory['files']:self.assertEqual(reader.read(self.sources,row['path']),(self.sources/row['path']).read_bytes())
            with self.assertRaises(ValueError):reader.read(self.sources,'missing')
        with self.assertRaises(ValueError):snap.check(self.out,'f'*64)
        with self.assertRaises(FileExistsError):self.freeze()
    def test_inventory_and_every_duplicate_source_are_checked(self):
        (self.sources/'copy.bin').write_bytes(b'INPUT')
        with self.assertRaisesRegex(ValueError,'bytes changed'):self.freeze()
        self.assertTrue(self.out.exists(),'Retain partial evidence')
        with self.assertRaises(FileExistsError):self.freeze()
    def test_invalid_paths_counts_sizes_and_bindings_rejected_before_publication(self):
        cases=[]
        for field,value in [('path','../escape'),('path','x/./y'),('path','C:/escape'),('root','relative'),('bytes',True),('bytes',snap.MAX_FILE+1),('sha256','bad')]:
            x=copy.deepcopy(self.inventory);x['files'][0][field]=value;cases.append(x)
        x=copy.deepcopy(self.inventory);x['files'].append(x['files'][0]);cases.append(x)
        x=copy.deepcopy(self.inventory);x['binding']['transaction_nonce']='wrong';cases.append(x)
        x=copy.deepcopy(self.inventory);x['binding']['unexpected']='yes';cases.append(x)
        for x in cases:
            with self.subTest(x=x),self.assertRaises(ValueError):snap.freeze(x,self.out)
            self.assertFalse(self.out.exists())
    def test_source_symlinks_or_ancestors_and_output_in_input_root_rejected(self):
        with self.assertRaises(ValueError):snap.freeze(self.inventory,self.sources/'snapshot.zip')
        p=self.sources/'copy.bin';p.unlink();p.symlink_to(self.sources/'input.bin')
        with self.assertRaises(ValueError):self.freeze()
    def test_binding_and_post_use_archive_mutation_are_checked(self):
        report=self.freeze();bad=dict(self.bind,transaction_nonce='0'*32)
        with self.assertRaisesRegex(ValueError,'binding'):snap.Snapshot(self.out,report['snapshot_sha256'],expected_binding=bad)
        with self.assertRaisesRegex(ValueError,'during use'):
            with snap.Snapshot(self.out,report['snapshot_sha256']):
                with self.out.open('ab') as f:f.write(b'changed')
    def rewrite(self,edit):
        self.freeze()
        with zipfile.ZipFile(self.out) as z:data={n:z.read(n) for n in z.namelist()}
        meta=json.loads(data['manifest.json']);edit(data,meta);data['manifest.json']=snap.canonical(meta)
        p=self.root/'forged.zip'
        with zipfile.ZipFile(p,'x') as z:
            for name,raw in data.items():z.writestr(name,raw)
        return p
    def test_even_newly_anchored_archives_reject_unlisted_paths_and_wrong_uncompressed_hash(self):
        p=self.rewrite(lambda data,meta:data.update({'../extra':b'x'}))
        with self.assertRaisesRegex(ValueError,'Unlisted'):snap.check(p,snap.file_sha(p))
    def test_selected_blob_hash_is_checked_beyond_archive_hash(self):
        def corrupt(data,meta):
            row=next(r for r in meta['files'] if r['path']=='input.bin');data[row['blob']]=b'INPUT'
        p=self.rewrite(corrupt)
        with snap.Snapshot(p,snap.file_sha(p)) as reader:
            with self.assertRaisesRegex(ValueError,'blob changed'):reader.read(self.sources,'input.bin')
    def test_windows_metadata_remains_readable_on_posix_without_opening_original_paths(self):
        def windows(data,meta):
            meta['binding']['future_capture']='C:/proof/future'
            for row in meta['files']:row['root']='C:/proof/original'
        p=self.rewrite(windows)
        with snap.Snapshot(p,snap.file_sha(p)) as reader:self.assertEqual(reader.read('C:/proof/original','input.bin'),b'input')
    def test_metadata_inspection_cannot_mutate_the_validated_read_binding(self):
        r=self.freeze()
        with snap.Snapshot(self.out,r['snapshot_sha256']) as reader:
            view=reader.meta;view['binding']['transaction_nonce']='0'*32
            next(x for x in view['files'] if x['path']=='input.bin')['blob']='blobs/'+snap.digest(b'artifact')
            self.assertEqual(reader.meta['binding'],self.bind)
            self.assertEqual(reader.read(self.sources,'input.bin'),b'input')


if __name__=='__main__':unittest.main()
