import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from protection_runtime import ProtectionPolicy,activate
from effect_runtime import state

class ProtectionRuntimeTests(unittest.TestCase):
    def test_snapshot_amplification_and_applied_event_follow_initialization(self):
        effect={'stat':'shield'};carrier=NS(uid=1,effect=effect,caster='a',target_chars=['a','b'])
        log=[]
        manager=NS(_active=[carrier],_get_value=lambda *args:20,effective_max_hp=lambda name:1000)
        manager.take_next_shield_amp=lambda name,t:50 if name=='a' else 0
        manager.notify=lambda event,t,name:log.append((name,dict(carrier.current),dict(carrier.capacity)))
        policy=ProtectionPolicy('shield',frozenset({'shield'}),'current','capacity',True,'event:shield_applied')
        state(manager).activation_stack.append(carrier)
        activate(manager,effect,'a',0,['a','b'],policy)
        self.assertEqual(carrier.current,{'a':300,'b':200})
        self.assertEqual([name for name,_,_ in log],['a','b'])
        self.assertTrue(all(current==capacity=={'a':300,'b':200} for _,current,capacity in log))
        manager.effective_max_hp=lambda name:5000
        self.assertEqual(carrier.capacity['a'],300)
    def test_decoy_has_no_shield_amplification_or_notification(self):
        effect={'stat':'decoy'};carrier=NS(uid=1,effect=effect,caster='a',target_chars=['a'])
        def forbidden(*args):raise AssertionError('shield behavior must not leak into decoy')
        manager=NS(_active=[carrier],_get_value=lambda *args:30,effective_max_hp=lambda name:1000,
                   notify=forbidden,take_next_shield_amp=forbidden)
        state(manager).activation_stack.append(carrier)
        activate(manager,effect,'a',0,['a'],ProtectionPolicy('decoy',frozenset({'decoy'}),'current','capacity'))
        self.assertEqual(carrier.current,{'a':300})

if __name__=='__main__':unittest.main()
