"""Private body/independent cover carriers, literal wire and source ownership."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_weighted_battle_wire as wire
from portable_specs import LIMITS as L,FIELDS as F
s=importlib.util.spec_from_file_location('weighted_wire_adapter',ROOT/'research/verify-weighted-battle.py');adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
class WeightedBattleWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows,cls.data=adapter.prepare()
    def test_all_seven_original_battles_and_only_literal_weights_are_packed(self):
        self.assertEqual(len(self.rows),21);self.assertEqual(len(self.data),4+21*wire.INPUT*4)
        for _,words,domain in self.rows[:8]:
            c,meta=domain[:2];case=c['weighted_case'];spec=case['allocation']
            binding=c['typed_bindings'][0];audit=next(p for p in c['patterns'] if p['id']==binding['node'])
            self.assertGreater(audit['delay'],c['duration'],'Audit target must remain unspawned; distance alone does not exclude automatic aim')
            self.assertEqual(words[wire.LAYOUT['BASE']:],wire.pack(spec,c['names'],meta['weighted_incoming']['source_rows']))
            self.assertFalse(meta['weighted_incoming']['CPU_state_or_schedule_as_input'])
            for i in meta['weighted_incoming']['definition_indices']:
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];e=c['effects'][i]
                self.assertEqual((words[at+F['KIND']],words[at+F['STAT']]),(4,0))
                self.assertEqual(e,c['original_run']['prepared']['effects'][i]['effect'])
    def test_private_lowering_restores_default_rejection_and_functions(self):
        import portable_runtime,portable_element_specs
        functions=(portable_runtime.validate_effect,portable_element_specs.legacy_effect)
        effect=copy.deepcopy(self.rows[0][2][0]['weighted_case']['contract']['original_markers'][1]['effect'])
        with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(effect,combat={},world_frame=True)
        with wire.compiler_policy():
            portable_runtime.validate_effect(effect,combat={},world_frame=True)
            lowered=portable_element_specs.legacy_effect(effect)
            self.assertEqual((lowered['stat'],lowered['target']),('','self'))
            for override in [dict(scaling='max_hp'),dict(target='all_enemies'),dict(duration_bullets=1)]:
                with self.assertRaises(ValueError):portable_runtime.validate_effect(dict(effect,**override),combat={},world_frame=True)
        self.assertEqual(functions,(portable_runtime.validate_effect,portable_element_specs.legacy_effect))

if __name__=='__main__':unittest.main()
