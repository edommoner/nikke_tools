"""Control repairs are a fixed exception, not arbitrary test/source replacement."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_continuation_package as cap


class ReviewedControlsTests(unittest.TestCase):
    def original(self):
        r=json.loads((ROOT/cap.REPAIR_LEDGER).read_text())
        files={n:dict(path=n,**v['before']) for n,v in r['changed'].items()}
        for n in (*cap.FULL_REPLACED,'tests/test_portable_staged_continuation.py'):files.setdefault(n,dict(path=n,bytes=1,sha256='placeholder'))
        files['tests/fixtures/portable-generation-extraction.json']=dict(path='tests/fixtures/portable-generation-extraction.json',bytes=0,sha256=r['original_extraction_expected_sha256'])
        return dict(package_id=r['base_package_id'],files=list(files.values()))

    def test_fixed_owner_and_original_and_repaired_file_fingerprints_are_required(self):
        m=self.original();r=cap.repair_manifest(ROOT,m)
        schema,replaced,added=cap.layout(m,repair_controls=True)
        self.assertEqual(schema,cap.REPAIRED_SCHEMA)
        self.assertEqual(set(replaced),set(cap.FULL_REPLACED)|set(r['changed']))
        self.assertTrue(set(cap.REPAIR_ORIGINALS)<=set(added))
        for change in ('owner','before','addition'):
            bad=copy.deepcopy(m)
            if change=='owner':bad['package_id']='wrong'
            elif change=='before':next(v for v in bad['files'] if v['path']==cap.REPAIR_CHANGED[0])['sha256']='wrong'
            else:bad['files'].append(dict(path=cap.REPAIR_ADDED[0],bytes=0,sha256='wrong'))
            with self.subTest(change=change),self.assertRaises(ValueError):cap.repair_manifest(ROOT,bad)

    def test_modified_ledger_or_repaired_bytes_are_not_admitted(self):
        m=self.original()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            names=[cap.REPAIR_LEDGER,*cap.REPAIR_CHANGED,*cap.REPAIR_ADDED,'tests/fixtures/portable-generation-extraction.json']
            for n in names:
                p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
            cap.repair_manifest(root,m)
            for n in (cap.REPAIR_LEDGER,*cap.REPAIR_CHANGED,*cap.REPAIR_ADDED,'tests/fixtures/portable-generation-extraction.json'):
                p=root/n;original=p.read_bytes();p.write_bytes(original+b'\n')
                with self.subTest(name=n),self.assertRaises(ValueError):cap.repair_manifest(root,m)
                p.write_bytes(original)


if __name__=='__main__':unittest.main()
