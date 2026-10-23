"""Pinned metadata repair must never admit changed physics or input baselines."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_leftmost_replay_migration import verify,ORIGIN,ADAPTER,REJECTED,digest
import json

class LeftmostReplayTests(unittest.TestCase):
    def setUp(self):
        pins=json.loads((ROOT/'tests/fixtures/portable-leftmost-replay-migration.json').read_text())
        self.old=dict(package_id=ORIGIN,suite='leftmost-retention',files=[dict(path=ADAPTER,sha256=pins['old_adapter_sha256']),dict(path='app/reference.py',sha256='fixed')],golden=dict(input_sha256='fixed',source_sha256={'gpu/source':'fixed'},entries=[dict(name=('family/reject/' if i in REJECTED else 'family/positive/')+str(i),input_sha256=str(i),native_sha256=digest(dict(rejected=True)) if i in REJECTED else str(i)) for i in range(74)]))
        self.new=copy.deepcopy(self.old);self.new['files'][0]['sha256']=pins['new_adapter_sha256']
        for i in REJECTED:self.new['golden']['entries'][i]['native_sha256']=digest(dict(status=64))
        self.entries=[(r['name'],[],None if i in REJECTED else ('positive',i)) for i,r in enumerate(self.old['golden']['entries'])]
    def test_only15_rejection_domains_change(self):
        r=verify(self.old,self.new,self.entries);self.assertEqual(r['corrected_rejections'],15);self.assertEqual(r['gpu_calls'],0)
    def test_source_input_positive_native_rejection_and_origin_tampering_reject(self):
        for fault in ('origin','suite','adapter','native-source','input','gpu','positive','negative','domain','case','count'):
            old=copy.deepcopy(self.old);new=copy.deepcopy(self.new);entries=copy.deepcopy(self.entries)
            if fault=='origin':old['package_id']='other'
            elif fault=='suite':new['suite']='other'
            elif fault=='adapter':new['files'][0]['sha256']='other'
            elif fault=='native-source':new['files'][1]['sha256']='other'
            elif fault=='input':new['golden']['input_sha256']='other'
            elif fault=='gpu':new['golden']['source_sha256']['gpu/source']='other'
            elif fault=='positive':new['golden']['entries'][0]['native_sha256']='other'
            elif fault=='negative':new['golden']['entries'][40]['native_sha256']='other'
            elif fault=='domain':entries[40]=(entries[40][0],[],('positive',40))
            elif fault=='case':entries[40]=('different',[],None)
            else:entries.pop()
            with self.subTest(fault=fault),self.assertRaises(ValueError):verify(old,new,entries)
    def test_existing_combiner_retains_none_for_exact15_rejections(self):
        s=importlib.util.spec_from_file_location('leftmost_retention_test',ROOT/ADAPTER);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,data=m.prepare();self.assertEqual(tuple(i for i,(_,_,d) in enumerate(rows) if d is None),REJECTED);self.assertEqual(len(data),4+74*104400*4)

if __name__=='__main__':unittest.main()
