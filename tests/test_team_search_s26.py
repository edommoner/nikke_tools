"""Seal isolation and final-once guarantees for fresh shortlist truth."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]/'research/team-search'
sys.path.insert(0,str(HERE))
import truth_s26 as truth
import evaluate_s26 as evaluation
import build_s26


class S26SealTests(unittest.TestCase):
    def test_excluded_subset_never_enters_either_half(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);dest=out/'truth';dest.mkdir()
            rows=[dict(id=i,members=[str(i)],order=[str(i)],total=i+1,
                       backend='native_detail',status='ok') for i in range(3)]
            truth.save(out/'selection.json',dict(rows=[dict(id=r['id'],members=r['order']) for r in rows],
                groups=[dict(split=split,best=i) for i,split in enumerate(('dev','sealed','excluded'))]))
            (out/'s21-detailed.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            truth.save(out/'prepared.json',{})
            truth.save(out/'collection.json',{})
            with patch.object(truth,'HERE',dest):truth.seal(out)
            dev=[json.loads(l) for l in (dest/'s26-dev.jsonl').read_text().splitlines()]
            sealed=[json.loads(l) for l in (dest/'s26-sealed.jsonl').read_text().splitlines()]
            self.assertEqual([r['id'] for r in dev],[0])
            self.assertEqual([r['id'] for r in sealed],[1])
            record=json.loads((out/'seal.json').read_text())
            self.assertEqual(record['files']['sealed']['sha256'],truth.old.digest(dest/'s26-sealed.jsonl'))

    def test_failed_final_consumes_guard_before_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'s26';out.mkdir()
            (root/'s22').mkdir();truth.save(root/'s22/final-profiles.json',{})
            profile=out/'profile.json';truth.save(profile,{})
            truth.save(out/'seal.json',{})
            truth.save(out/'model-frozen.json',dict(profiles_sha256=truth.old.digest(profile),required_evidence={}))
            def fail(*args):
                self.assertTrue((out/'final-once.json').exists())
                raise RuntimeError('simulated scoring failure')
            with patch.object(truth.old.previous,'profiles',return_value={}),patch.object(evaluation,'score_split',side_effect=fail) as score:
                with self.assertRaisesRegex(RuntimeError,'simulated'):evaluation.final(out,profile)
                self.assertEqual(score.call_count,1)
                with self.assertRaises(FileExistsError):evaluation.final(out,profile)
                self.assertEqual(score.call_count,1)


class S26MechanicsTests(unittest.TestCase):
    def test_legacy_oracles_keep_original_types(self):
        import l2_score
        import l2_score_s20
        import l2_score_s22
        import l2_score_s26
        p=dict(settings=dict(duration=180),characters={})
        self.assertIs(type(l2_score_s26.Score(p)),l2_score.Score)
        p['s20']=dict(switches=0)
        self.assertIs(type(l2_score_s26.Score(p)),l2_score_s20.Score)
        p['s22']=dict(switches=0)
        self.assertIs(type(l2_score_s26.Score(p)),l2_score_s22.Score)

    def test_shield_prerequisite_does_not_gate_alternative_trigger(self):
        self.assertTrue(build_s26.needs_shield(dict(trigger=dict(timing=['event:shield_applied']))))
        self.assertTrue(build_s26.needs_shield(dict(trigger=dict(condition=['during_shield']))))
        self.assertFalse(build_s26.needs_shield(dict(trigger=dict(timing=['event:shield_applied','burst_cast']))))

    def test_enemy_code_lowering_requires_matching_plain_scenario(self):
        effect=dict(stat='received_dmg_pct',target='enemies_code:풍압',
                    trigger=dict(condition=['target_code:풍압']))
        p=dict(settings=dict(enemy=dict(code='풍압')),characters=dict(a=dict(metadata=dict(burst_stage='3'),effects=[],buffs=[dict(effect=effect)])))
        def lowered(profile):return 'target_s26' in build_s26.build(profile,2)['characters']['a']['buffs'][0]
        self.assertTrue(lowered(p))
        self.assertNotIn('target_s26',p['characters']['a']['buffs'][0])
        p['settings']['enemy']['code']='전격'
        self.assertFalse(lowered(p))
        p['settings']['enemy']['code']='풍압';p['settings']['enemy']['patterns']=[dict(kind='summon')]
        self.assertFalse(lowered(p))

    def test_negated_state_requires_complementary_removal(self):
        marker=dict(type='buff',name='state',target='self',duration=-1,
                    trigger=dict(timing=['battle_start','full_burst_end'],condition=['no_burst1_ally']))
        effect=dict(trigger=dict(condition=['not_self_state:state']))
        self.assertEqual(build_s26.prerequisite(effect,[marker]),0)
        remove=dict(stat='remove_named_buff',target='self',target_effect='state',
                    trigger=dict(timing=['battle_start','full_burst_end'],condition=['has_burst1_ally']))
        self.assertEqual(build_s26.prerequisite(effect,[marker,remove]),2)


if __name__=='__main__':unittest.main()
