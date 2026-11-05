"""The readback opt-in preserves inputs and cannot relax historical guards."""
import copy,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_recipient_order_observation as observation
from portable_recipient_order_source_contract import project_sources,BEFORE_BACKEND_SHA256

class RecipientOrderObservation(unittest.TestCase):
    def fixture_root(self,path):
        names=[observation.SOURCE,'gpu/world_coordinate_typed_entry.slang','gpu/skill_history_layout.slang',
               'gpu/world_coordinate_area_entry.slang','app/portable_backend.py','tests/fixtures/portable-recipient-order-observation-source-delta.json']
        for name in names:
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            target=path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)

    def test_complete_wire_and_only_explicit_entry_are_admitted(self):
        from portable_backend import validate_composed_stride
        observation.check_layout(ROOT)
        validate_composed_stride(observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS)
        for source,iw,ow in [(observation.SOURCE,observation.INPUT_WORDS-1,observation.OUTPUT_WORDS),
                             (observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS+1),
                             ('gpu/world_coordinate_typed_ordered_unknown.slang',observation.INPUT_WORDS,observation.OUTPUT_WORDS)]:
            with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)



    def test_exact_inverse_retains_the_whole_prior_backend(self):
        result=project_sources(ROOT)
        before=result['app/portable_backend.py']
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(),BEFORE_BACKEND_SHA256)
        self.assertEqual(project_sources(ROOT,{'app/portable_backend.py':before})['app/portable_backend.py'],before)
        for name in ('app/portable_backend.py','gpu/world_coordinate_area_entry.slang',observation.SOURCE):
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

    def test_updated_hash_cannot_hide_unreviewed_backend_or_entry(self):
        for fault in ('backend','area','backend-hunks','area-hunks','entry','anchor'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture_root(root)
                ledger=root/'tests/fixtures/portable-recipient-order-observation-source-delta.json'
                data=json.loads(ledger.read_text())
                if fault in ('backend','area','backend-hunks','area-hunks'):
                    name='app/portable_backend.py' if fault.startswith('backend') else 'gpu/world_coordinate_area_entry.slang'
                    target=root/name;target.write_text(target.read_text()+'\n// unreviewed\n')
                    data['files'][name]['after_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
                    if fault.endswith('-hunks'):
                        data['files'][name]['hunks'].append(dict(before='',after='\n// unreviewed\n'))
                elif fault=='entry':
                    target=root/observation.SOURCE;target.write_text(target.read_text()+'\n')
                    data['added_sources'][observation.SOURCE]=hashlib.sha256(target.read_bytes()).hexdigest()
                else:data['files']['app/portable_backend.py']['before_sha256']='0'*64
                ledger.write_text(json.dumps(data))
                with self.assertRaises(ValueError):project_sources(root)

if __name__=='__main__':unittest.main()
