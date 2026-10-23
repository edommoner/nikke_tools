"""Real target worlds preserve all profile definitions and default policy bytes."""
import array,copy,hashlib,importlib.util,json,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_real_aim_policy import configured
from portable_projectile_roster_input import compile_projectile_battle
from portable_aimed_roster_cases import fixtures
from portable_aimed_roster_contracts import verify
from portable_state_focus_roster_cases import fixtures as originals
from world_real_aim_native import observe


def adapter():
    s=importlib.util.spec_from_file_location('real_aim_test_adapter',ROOT/'research/verify-world-aimed-rosters-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class AimedRosterTests(unittest.TestCase):
    def test_all12_packing_keeps_full_profiles_and_forbids_battle(self):
        def forbidden(*a,**k):raise AssertionError('Static packing ran a battle/GPU')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):entries,data=adapter().prepare()
        self.assertEqual(len(entries),12);self.assertEqual(len(data),4+sum(len(w)*4 for _,w,_ in entries))
        self.assertEqual([len(d[1]['effects']) for _,_,d in entries],[70]*4+[79]*4+[68]*4)
        for _,_,(case,p,w,m) in entries:
            plain=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
            self.assertEqual(p['chars'],plain['chars']);self.assertEqual(p['effects'],plain['effects']);self.assertEqual(p['allies'],plain['allies']);self.assertEqual(p['base_atk'],plain['base_atk'])
            self.assertEqual(len(m['effects']),len(p['effects']));self.assertTrue(m['real_prepared_input']['physical_interrupt_opt_in'])
            with self.assertRaisesRegex(ValueError,'interrupt aiming'):compile_projectile_battle(p)
            for invalid in (1,'yes',None):
                with self.assertRaisesRegex(ValueError,'literal boolean'):compile_projectile_battle(p,allow_physical_interrupt=invalid)

    def test_old6_default_input_hashes_are_unchanged(self):
        golden=json.loads((ROOT/'research/portable-world-aimed-area-retention-short-expected.json').read_text())
        for case in originals():
            p=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True));w,m=compile_projectile_battle(p)
            rows=[x for x in golden['entries'] if x['name'].endswith(case['name'])];self.assertEqual(len(rows),1)
            data=array.array('I',w)
            if sys.byteorder!='little':data.byteswap()
            self.assertEqual(hashlib.sha256(data.tobytes()).hexdigest(),rows[0]['input_sha256'])
            self.assertNotIn('physical_interrupt_opt_in',m['real_prepared_input'])

    def test_six3s_native_observer_equivalence_and_semantic_reads(self):
        for case in [x for x in fixtures() if x['duration']==3]:
            def measured(packets):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=observe(case,packets=packets);return result,[get.call_count,live.call_count,sample.call_count]
            with self.subTest(case=case['name']):
                actual,reads=measured(True);plain,other=measured(False);verify(case,actual)
                for key in ('physical_shots','physical_packet_sets'):actual.pop(key);plain.pop(key)
                self.assertEqual(actual,plain);self.assertEqual(reads,other)

    def test_policy_validation_restores_canonical_prepare(self):
        case=fixtures()[0];original=engine_worker.sim.prepare
        for policy in [dict(case['aim_policy'],aim_interrupt=1),dict(case['aim_policy'],camera=['unknown']),dict(case['aim_policy'],camera=case['body']['squad'][:2]),dict(case['aim_policy'],extra=True)]:
            with self.assertRaises(ValueError),configured(case['body'],policy):pass
            self.assertIs(engine_worker.sim.prepare,original)
        with self.assertRaisesRegex(RuntimeError,'injected'),configured(case['body'],case['aim_policy']):raise RuntimeError('injected')
        self.assertIs(engine_worker.sim.prepare,original)

    def test_contract_rejects_packet_pool_rng_and_damage_faults(self):
        case=fixtures()[0];native=observe(case)
        for fault in ('packet','pool','rng','damage'):
            bad=copy.deepcopy(native)
            if fault=='packet':bad['physical_packet_sets'][0]['packets'][0]['damage']+=1
            elif fault=='pool':bad['target_world']['actor_pools']['pools'][1][3]+=1
            elif fault=='rng':bad['friendly_samples'].append({'fake':True})
            else:bad['battle']['query']['body_damage'][0]+=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
