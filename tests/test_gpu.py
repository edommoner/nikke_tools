import json,random,sys,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from gpu_selector import Cuda,cpu_expand,probe,select_teams

class GPUSelectionTests(unittest.TestCase):
    def test_cpu_selection_preserves_large_integer_damage_and_disjointness(self):
        teams=[{'squad':[f'{i}:{j}' for j in range(5)],'damage':2**40+i} for i in range(7)]
        result=select_teams({'candidates':teams,'teamCount':5})['recommendation']
        self.assertEqual(result['damage'],sum(2**40+i for i in range(2,7)))
        self.assertEqual(len(set(n for t in result['teams'] for n in t['squad'])),25)
        self.assertIsNone(select_teams({'candidates':teams[:4],'teamCount':5})['recommendation'])
    def test_cuda_matches_cpu_on_overlaps_masks_and_large_integer_scores(self):
        status=probe()
        if not status['available']: self.skipTest(status['reason'])
        rng=random.Random(71);candidates=[]
        for i in range(160):candidates.append({'squad':rng.sample([f'c{j}' for j in range(230)],5),'damage':2**40+rng.randrange(10**8)})
        body={'candidates':candidates,'teamCount':5,'width':256}
        cpu=select_teams({**body,'backend':'cpu'});gpu=select_teams({**body,'backend':'cuda'})
        self.assertEqual(cpu['recommendation'],gpu['recommendation'])
        self.assertEqual(cpu['expanded'],gpu['expanded'])
        print(json.dumps({'device':gpu['device'],'cpu_total_ms':cpu['elapsed_ms'],'gpu_total_ms':gpu['elapsed_ms'],'cpu_expand_ms':cpu['expansion_ms'],'gpu_expand_ms':gpu['expansion_ms'],'expanded':gpu['expanded'],'exact_match':True}))
    def test_gpu_topk_handles_ties_zero_damage_and_padding(self):
        status=probe()
        if not status['available']:self.skipTest(status['reason'])
        device=Cuda()
        try:
            masks=[]
            for i in range(127):
                mask=[0]*8;mask[i//32]=1<<(i%32);masks.append(mask)
            states=[([0]*8,0,[],0xffffffff),([1]+[0]*7,0,[],20)]
            scores=[0 if i%3 else 2**40 for i in range(127)]
            values=cpu_expand(states,masks,scores)
            expected=sorted([(i,v) for i,v in enumerate(values) if v],key=lambda pair:(-pair[1],pair[0]))[:73]
            self.assertEqual(device.expand(states,masks,scores,top=73),expected)
            self.assertEqual(device.expand([([0xffffffff]*8,0,[],0xffffffff)],masks,scores,top=5),[])
        finally:device.close()

    def test_persistent_service_reuses_context_and_preserves_results(self):
        if not probe()['available']:self.skipTest('CUDA unavailable')
        import subprocess
        root=Path(__file__).resolve().parents[1]
        candidates=[{'squad':[f'{i}:{j}' for j in range(5)],'damage':2**40+i} for i in range(7)]
        body={'action':'select','backend':'cuda','teamCount':5,'width':256,'candidates':candidates}
        requests=[{'id':'probe','body':{'action':'gpu_probe'}},{'id':'first','body':body},{'id':'second','body':body}]
        process=subprocess.run([sys.executable,str(root/'app/gpu_service.py')],input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True,timeout=30)
        self.assertEqual(process.returncode,0,process.stderr)
        replies=[json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(replies),3)
        self.assertTrue(replies[0]['result']['persistent'])
        for reply in replies[1:]:
            self.assertEqual(reply['result']['sort_backend'],'cuda')
            self.assertEqual(reply['result']['recommendation'],select_teams({**body,'backend':'cpu'})['recommendation'])

    def test_invalid_candidate_and_backend_rejected(self):
        with self.assertRaises(ValueError):select_teams({'backend':'unknown','candidates':[]})
        with self.assertRaises(ValueError):select_teams({'candidates':[{'squad':['a']*5,'damage':1}]})

if __name__=='__main__':unittest.main()
