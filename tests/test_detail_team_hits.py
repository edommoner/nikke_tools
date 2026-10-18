"""Global team notifications must retain source and attacker identities."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('team_hits_tests',ROOT/'scripts/verify-team-hits-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects,UnsupportedDetail
from detail_world import packed_enemy,EN
from gpu_selector import Cuda,probe

class TeamHitCompilerTests(unittest.TestCase):
    def test_b3_deferral_binding_survives_team_definition_expansion(self):
        body=next(body for name,body,world,extra in v.bodies() if name=='D : 킬러 와이프-none' and body['shooting_policy']=='character')
        compiled=v.a.evaluate({**body,'_compile_gpu_detail':True})
        flagged=[r for r in compiled['program']['effects'] if r[51]>0]
        self.assertTrue(flagged)
        self.assertTrue(all(r[0]==body['squad'].index('베스티') for r in flagged))

    def test_attacker_levels_source_owner_and_shared_activation_budget(self):
        _,chars,effects,_,_=next(v.primitives())
        rows=compile_effects(copy.deepcopy(chars),effects)['effects']
        self.assertEqual(len(rows),5)
        self.assertEqual([r[0] for r in rows],list(range(5)))
        self.assertEqual([r[268] for r in rows],[1]*5)
        self.assertEqual([r[6] for r in rows],[100,10,20,30,40])
        self.assertEqual(len({r[58] for r in rows}),5)
        self.assertEqual(len({r[269] for r in rows}),1)
        program=compile_effects(copy.deepcopy(chars),effects)
        program['effects'][0][268]=6
        with self.assertRaises(ValueError):v.run(None,[program],[[0,2,0,0,-1,0,0,0]],[[31784,0]],[{}])

    def test_unimplemented_mixed_periodic_and_nonliteral_thresholds_fail_closed(self):
        _,chars,effects,_,_=next(v.primitives())
        for timings,extra in [(['part_hit_count:1','battle_start'],{}),(['part_hit_count:{0}'],{}),(['part_hit_count:0'],{}),(['body_hit_count:2'],{'tick_interval':1})]:
            effect=copy.deepcopy(effects[0][0]);effect.update(extra);effect['trigger']['timing']=timings
            with self.assertRaises(UnsupportedDetail):compile_effects(copy.deepcopy(chars),[(effect,effects[0][1])])

    def test_static_part_presence_survives_enemy_packing(self):
        enemy={'def':31784,'core_px':5,'has_parts':True}
        packed=packed_enemy(enemy,[])
        self.assertEqual(len(packed),EN);self.assertEqual(packed[2],0);self.assertEqual(packed[67],1)
        enemy['has_parts']=False
        self.assertEqual(packed_enemy(enemy,[]),[31784,5])

class TeamHitGPUTests(unittest.TestCase):
    def test_global_counters_attacker_targets_and_source_conditions_match_cpu(self):
        status=probe()
        if not status['available']:self.skipTest(status['reason'])
        device=Cuda()
        try:rows=v.verify_primitives(device,'native')
        finally:device.close()
        self.assertEqual(len(rows),25)
        self.assertTrue(all(r['passed'] for r in rows),json.dumps([r for r in rows if not r['passed']],ensure_ascii=True))

if __name__=='__main__':unittest.main()
