"""Regression for the heterogeneous catalog batch that faulted on SM86."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('batch_regression',ROOT/'scripts/verify-catalog-batch-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class HeterogeneousBatchTests(unittest.TestCase):
    def test_independent_real_squads_keep_cpu_parity(self):
        items=[]
        for name in ['D','미카','미카 : 스노우 버디','브리드','솔린','디젤','브리드 : 사일런트 트랙','솔린 : 프로스트 티켓']:
            names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
            body=v.body_for(names,30,True)
            body.update(seed=12345,shooting_policy='auto',burst_policy='rules',burst_gauge_mode='fixed',_debug_random_state=True)
            items.append((name,body,v.a.evaluate({**body,'_compile_gpu_detail':True})))
        for flag in (False,True):
            name='신데렐라 : 크리스탈 웨이브'
            body=v.body_for([name,'리타','크라운','앨리스','모더니아'],30,True)
            body.update(seed=12345,shooting_policy='auto',burst_policy='rules',burst_gauge_mode='fixed',_debug_random_state=True,weapon_mode_swap=flag)
            items.append((name+' mode='+str(flag),body,v.a.evaluate({**body,'_compile_gpu_detail':True})))
        device=v.Cuda()
        try:rows=v.evaluate_batch(device,items,'native')
        finally:device.close()
        self.assertEqual(len(rows),10)
        self.assertEqual([row['weapon_mode_swap'] for row in rows[-2:]],[False,True])
        self.assertTrue(all(row['gpu_group_size']==10 for row in rows))
        self.assertTrue(all(row['passed'] for row in rows),[r for r in rows if not r['passed']])

if __name__=='__main__':unittest.main()
