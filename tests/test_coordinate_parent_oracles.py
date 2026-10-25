"""Real saved Metal fixtures exercise every old comparator under live reuse."""
import array,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('coordinate_parent_test',ROOT/'research/verify-coordinate-burst-control-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_parent_oracles import ParentOracles,provider
import portable_coordinate_parent_check as checker

class CoordinateParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,_=a.prepare();cls.golden=json.loads((ROOT/'research/portable-coordinate-burst-control-short-expected.json').read_text())
        cls.fixture=json.loads((ROOT/'tests/fixtures/portable-coordinate-parent-oracle-raw.json').read_text())
    def test_every_domain_resolves_to_its_original_native_provider(self):
        found=[provider(a,d) for _,_,d in self.rows if d is not None];self.assertEqual(len(found),246)
        for _,_,domain in self.rows:
            if domain is None:continue
            target=provider(a,domain);node=a.native_comparison_adapter(domain)
            self.assertIs(target[0],node.__dict__);self.assertIs(target[2],node.native_reference);self.assertIs(target[3],domain)
    def test_cpu_checker_rejects_input_native_and_source_drift_before_reading_fixtures(self):
        baseline=dict(suite='coordinate-burst-control',golden=self.golden,files=[])
        for change in ('input','native','source'):
            current=copy.deepcopy(baseline)
            if change=='input':current['golden']['input_sha256']='0'*64
            elif change=='native':current['golden']['entries'][0]['native_sha256']='0'*64
            else:current['golden']['source_sha256']={'unreviewed':'0'*64}
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'baseline changed'):
                checker.admission(current,baseline,Path('/missing'),Path('/missing'))
    def test_cpu_checker_rejects_changed_original_comparator(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=Path(tmp)/'old';new=Path(tmp)/'new'
            for root in (old,new):(root/'research').mkdir(parents=True)
            (old/'research/verify-coordinate-burst-control-short.py').write_text('def compare(block,domain):\n    return 1\n')
            (new/'research/verify-coordinate-burst-control-short.py').write_text('def compare(block,domain):\n    return 2\n')
            baseline=dict(suite='coordinate-burst-control',golden=self.golden,files=[])
            with patch.object(checker,'ROOT',new),self.assertRaisesRegex(ValueError,'comparator changed'):
                checker.admission(baseline,baseline,old,Path('/missing'))
    def test_real_creation_receipts_and_controller_state_reuse_without_fresh_native(self):
        from portable_coordinate_sampling_bank import LAYOUT as BANK
        from portable_coordinate_sampled_burst_wire import BASE,HITS
        from portable_burst_control_specs import STATE_BASE
        context=a.NATIVE_COMPARISON_CONTEXT
        import world_coordinate_sampled_skill_native as source
        for row in self.fixture['records']:
            name,w,domain=self.rows[row['index']];self.assertEqual(name,row['name']);self.assertEqual(row['native_sha256'],self.golden['entries'][row['index']]['native_sha256'])
            block=array.array('I',[0])*self.fixture['case_words']
            for at,value in row['nonzero']:block[at]=value
            raw=block.tobytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['output_sha256'])
            target=a.native_comparison_adapter(domain);original=target.native_reference;calls=[]
            def witness(d):
                calls.append(True)
                if len(calls)>1:raise AssertionError('Repeated native during live-parent comparison')
                return original(d)
            previous_profile=sys.getprofile();creation_factory=source.creation_indices
            with self.subTest(case=name),tempfile.TemporaryDirectory() as tmp,patch.object(target,'native_reference',witness):
                manifest=dict(package_id='coordinate-live-parent-fixture',golden=dict(entries=[dict(native_sha256=row['native_sha256'])]));parent=ParentOracles(manifest,Path(tmp))
                try:
                    parent.prepare(a,[(name,w,domain)]);before=parent.before(0)
                    with parent.observe(0,before):native=a.native_reference(domain)
                    parent.remember(0,before,native,a.cross.digest);parent.finish();self.assertTrue(parent.usable)
                    auxiliary=copy.deepcopy(parent.records[0]['context']['value'])
                    if name.endswith('/legacy-three'):self.assertTrue(auxiliary);self.assertTrue(any(r['hits']==3 for r in auxiliary))
                    parent.start(manifest,Path(tmp))
                    with parent.comparison(0):actual=a.compare(block,domain)
                    self.assertEqual(a.cross.digest(actual),row['native_sha256']);self.assertEqual(len(calls),1);self.assertEqual(parent.receipt()['reused_native_cases'],1)
                    if name.endswith('/legacy-three'):
                        event=native['sampled_legacy_damage'][0];at=BASE+(event['index']*HITS+event['hit']-1)*2+1
                    elif name.endswith('/reentry'):at=STATE_BASE+2
                    else:at=BANK['RNG']+8
                    bad=array.array('I',block);bad[at]^=1
                    # Only this unit's fault injection uses its verified value;
                    # production saved-result/independent audits remain fresh.
                    with patch.object(target,'native_reference',return_value=copy.deepcopy(native)),context.restore(domain,copy.deepcopy(auxiliary)):
                        with self.assertRaises(AssertionError):a.compare(bad,domain)
                finally:parent.close()
            self.assertIs(target.native_reference,original)
            self.assertIs(source.creation_indices,creation_factory);self.assertIs(sys.getprofile(),previous_profile)

if __name__=='__main__':unittest.main()
