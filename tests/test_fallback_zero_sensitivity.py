"""Public witnesses use ordinary fields and remove only the authored stat row."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker,portable_backend
from calculator.buff_manager import BuffManager

class PublicSensitivityTests(unittest.TestCase):
    def test_ordinary_intercept_and_lock_ablation_change_public_fields(self):
        requests=json.loads((ROOT/'tests/fixtures/fallback-zero-sensitivity-v1.json').read_text())
        original=BuffManager.char_effects
        for request in requests:
            key=request['key'][0].split('|')[1];removed=[];body=dict(copy.deepcopy(request['body']),compute_backend='cpu')
            before=copy.deepcopy(body)
            def rows(manager,owner):
                effects=original(manager,owner)
                removed.extend((owner,copy.deepcopy(e)) for e in effects if e.get('stat')==key)
                return [e for e in effects if e.get('stat')!=key]
            with self.subTest(key=key),patch.object(portable_backend,'execute',side_effect=AssertionError('CPU only')):
                baseline=engine_worker.evaluate(body)
                with patch.object(BuffManager,'char_effects',rows):ablated=engine_worker.evaluate(body)
                self.assertEqual(body,before);self.assertNotIn('reference_models',body)
                self.assertEqual(len(removed),1);self.assertEqual(removed[0][1]['stat'],key)
                if key=='intercept_dmg_pct':
                    self.assertEqual(removed[0][0],'헬름')
                    self.assertEqual(baseline['total_damage'],ablated['total_damage'])
                    self.assertEqual(baseline['boss_timeline'][1]['time'],1.533333)
                    self.assertEqual(ablated['boss_timeline'][1]['time'],3.433333)
                else:
                    self.assertEqual((removed[0][0],removed[0][1]['name']),('스노우 화이트 : 헤비암즈','록 온'))
                    self.assertEqual(baseline['total_damage'],84035348)
                    self.assertEqual(ablated['total_damage'],86645042)

    def test_focus_reader_has_no_divergent_ordinary_product_aim(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare
        from portable_declared_manual_sequences import apply
        from runner import spec
        body=copy.deepcopy(selected_profile_bodies(['리틀 머메이드'],0)[0][2])
        # Put the focus owner in the default camera slot. Merely activating the
        # row cannot make camera/non-camera targets differ in layer1 auto.
        names=body['squad'];body['squad']=[names[1],names[2],names[0],names[3],names[4]]
        _,run=prepare(body)
        self.assertIs(run.config['aim_interrupt'],False)
        self.assertTrue(all(not c.get('control',{}).get('aim') for c in run.squad))
        self.assertNotIn('control',spec.GROWTH_KEYS)
        with self.assertRaisesRegex(ValueError,'Only explicit cover'):
            apply(run.squad,{body['squad'][0]:[dict(action='aim',t=0,duration=1)]})
        # The fixed control data contains no manual aim rows for any character.
        for path in (ROOT/'research/upstream/nikke-calc-master/data').rglob('*.json'):
            if path.name in ('char_defaults.json','tactics.json'):
                self.assertNotIn('"aim"',path.read_text())

if __name__=='__main__':unittest.main()
