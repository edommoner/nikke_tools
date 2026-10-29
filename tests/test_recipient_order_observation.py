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
            target=path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)

    def test_complete_wire_and_only_explicit_entry_are_admitted(self):
        from portable_backend import validate_composed_stride
        observation.check_layout(ROOT)
        validate_composed_stride(observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS)
        for source,iw,ow in [(observation.SOURCE,observation.INPUT_WORDS-1,observation.OUTPUT_WORDS),
                             (observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS+1),
                             ('gpu/world_coordinate_typed_ordered_unknown.slang',observation.INPUT_WORDS,observation.OUTPUT_WORDS)]:
            with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)

    def test_observation_does_not_rewrite_inputs_revival_flags_or_original_definitions(self):
        import nikke_gpu as cli
        from portable_specs import LIMITS as L
        m=dict(suite='original-catalogue-support',purpose='development',selected_cases=[])
        adapter=cli.open_suite(m);names=cli.SUITES[m['suite']]['frozen_cases']
        original,_=adapter.base.prepare_selected(names);observed,_=adapter.prepare_selected(names)
        for old,new in zip(original,observed):
            self.assertEqual(old[:2],new[:2]);self.assertEqual(old[2][0],new[2][0])
            meta=copy.copy(new[2][1]);self.assertTrue(meta['ordered_recipients'])
            meta['ordered_recipients']=old[2][1]['ordered_recipients'];self.assertEqual(meta,old[2][1])
            self.assertEqual(new[1][L['RECIPIENT_META_BASE']:L['RECIPIENT_META_BASE']+3],[0,0,0])

    def test_exact_inverse_retains_the_whole_prior_backend(self):
        result=project_sources(ROOT)
        before=result['app/portable_backend.py']
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(),BEFORE_BACKEND_SHA256)
        self.assertEqual(project_sources(ROOT,{'app/portable_backend.py':before})['app/portable_backend.py'],before)
        for name in ('app/portable_backend.py','gpu/world_coordinate_area_entry.slang',observation.SOURCE):
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

    def test_updated_hash_cannot_hide_unreviewed_backend_or_entry(self):
        for fault in ('backend','area','entry','anchor'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture_root(root)
                ledger=root/'tests/fixtures/portable-recipient-order-observation-source-delta.json'
                data=json.loads(ledger.read_text())
                if fault in ('backend','area'):
                    name='app/portable_backend.py' if fault=='backend' else 'gpu/world_coordinate_area_entry.slang'
                    target=root/name;target.write_text(target.read_text()+'\n// unreviewed\n')
                    data['files'][name]['after_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
                elif fault=='entry':
                    target=root/observation.SOURCE;target.write_text(target.read_text()+'\n')
                    data['added_sources'][observation.SOURCE]=hashlib.sha256(target.read_bytes()).hexdigest()
                else:data['files']['app/portable_backend.py']['before_sha256']='0'*64
                ledger.write_text(json.dumps(data))
                with self.assertRaises(ValueError):project_sources(root)

if __name__=='__main__':unittest.main()
