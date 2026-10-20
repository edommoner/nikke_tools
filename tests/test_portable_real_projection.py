import importlib.util,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
s=importlib.util.spec_from_file_location('real_projection',R/'scripts/verify-portable-real-battle.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class RealModeProjectionContracts(unittest.TestCase):
    def test_active_auto_mode_does_not_use_a_base_charge_delay(self):
        weapon=dict(reload_until=-1,charging=False,next=3,charge_until=999)
        self.assertEqual(v.action_gate(weapon,dict(post_reload_until=-1),'auto_warmup'),dict(kind='fire',time=3))
        self.assertEqual(v.action_gate(weapon,dict(post_reload_until=-1),'charge'),dict(kind='charge_delay',time=3))
    def test_reload_gate_stays_authoritative_during_a_mode(self):
        weapon=dict(reload_until=4,charging=True,next=3,charge_until=999)
        self.assertEqual(v.action_gate(weapon,dict(post_reload_until=5),'charge'),dict(kind='reload',time=4))
    def test_native_active_mode_observes_actual_firing_method(self):
        from detail_coverage import body_for
        body={**body_for(['네온 : 블루 오션','미란다','도라','N102','메어리'],duration=180),'burst_gauge_mode':'accumulate'}
        body['enemy']['code']='작열'
        cpu=v.native_reference(body);mode=next(r for r in cpu['active_weapon_modes'] if r['owner']==0)
        self.assertEqual(mode['name'],'풀 하이드로 샷');self.assertEqual(mode['fire_mode'],'auto_warmup')
        self.assertTrue(mode['physical_active']);self.assertGreater(mode['shots'],0);self.assertEqual(cpu['action_gates'][0]['kind'],'fire')
if __name__=='__main__':unittest.main()
