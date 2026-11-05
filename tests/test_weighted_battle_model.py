"""Real original carrier lifetime and checked native landing extension."""
import ast,copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from weighted_incoming_battle_model import WeightedIncoming,weighted_incoming
from portable_original_identity_inventory import selected_prepared_profiles

SPEC=dict(policy='declared-weighted-incoming-v1',caster_weight=8.,other_weight=3.,cover_weight=262.)
class WeightedBattleModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.prepared=next(selected_prepared_profiles(['베이'],0))[2]
    def manager(self):
        p=copy.deepcopy(self.prepared);names=[c['name'] for c in p['chars']]
        state=dict(base_stats={n:dict(atk=a,hp=1e6,**{'def':1000.}) for n,a in zip(names,p['base_atk'])},hp_pct={n:100. for n in names},down=set())
        return BuffManager(p['chars'],state),names
    def test_original_carriers_expire_and_cover_stays_an_independent_receiver(self):
        bm,names=self.manager();model=WeightedIncoming(SPEC,names);hp={n:1000. for n in names}
        self.assertIsNone(model.snapshot(bm,names[4],100.,0.,hp))
        effects=[(e,c) for e,c in bm._effects if e.get('stat')=='received_dmg_split'];before=copy.deepcopy(effects)
        for e,c in effects:bm._activate(e,c,1.)
        active=[a for a in bm._by_stat('received_dmg_split')];self.assertEqual(len(active),2)
        cover=next(a for a in active if a.effect['target']=='self_cover')
        self.assertEqual(cover.target_chars,[],'Do not turn a cover carrier into a body target')
        plan=model.snapshot(bm,names[4],282.,1.,hp)
        self.assertEqual(len(plan['bodies']),5);self.assertEqual(plan['cover'],(names[0],282.*(262./282.)))
        self.assertEqual(effects,before)
        hp[names[0]]=0.;self.assertIsNone(model.snapshot(bm,names[4],100.,2.,hp)['cover'])
        hp[names[0]]=1000.;self.assertIsNotNone(model.snapshot(bm,names[4],100.,3.,hp)['cover'])
        for a in active:a.expires_at=4.
        self.assertIsNone(model.snapshot(bm,names[4],100.,4.,hp))
    def test_frozen_snapshot_survives_later_death_and_new_snapshots_remove_owner_cover(self):
        bm,names=self.manager();model=WeightedIncoming(SPEC,names);hp={n:1000. for n in names}
        for e,c in bm._effects:
            if e.get('stat')=='received_dmg_split':bm._activate(e,c,1.)
        frozen=model.snapshot(bm,names[4],100.,1.,hp);saved=copy.deepcopy(frozen)
        bm.state['down'].add(names[0]);current=model.snapshot(bm,names[4],100.,2.,hp)
        self.assertEqual(frozen,saved);self.assertEqual(len(current['bodies']),4);self.assertIsNone(current['cover'])
        self.assertEqual([q for _,q in current['bodies']],[25.]*4)
    def test_checked_extension_restores_original_alias_and_namespace(self):
        from calculator import timeline
        from runner import sim
        original=timeline.simulate
        with weighted_incoming(SPEC,[c['name'] for c in self.prepared['chars']]):
            self.assertIs(timeline.simulate,sim.simulate);self.assertIsNot(timeline.simulate,original)
        self.assertIs(timeline.simulate,original);self.assertIs(sim.simulate,original)
        self.assertNotIn('_nikke_weighted_snapshot',original.__globals__)

    def test_changed_original_cover_mutation_anchor_fails_before_installation(self):
        from calculator import timeline
        original=timeline.simulate;tree=copy.deepcopy(original._nikke_reference_tree)
        landing=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_land_squad')
        target=next(n for n in ast.walk(landing) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='min' and ast.unparse(n.args[0])=="state['cover_hp'][name]")
        target.func.id='max'
        with patch.object(original,'_nikke_reference_tree',tree):
            with self.assertRaises((AssertionError,ValueError)):
                with weighted_incoming(SPEC,[c['name'] for c in self.prepared['chars']]):self.fail('Changed source must not install')
        self.assertIs(timeline.simulate,original);self.assertNotIn('_nikke_weighted_snapshot',original.__globals__)

    def test_unsupported_overlap_is_rejected_before_a_packet_is_recorded(self):
        bm,names=self.manager();model=WeightedIncoming(SPEC,names);hp={n:1000. for n in names}
        effect=next(e for e,c in bm._effects if e.get('stat')=='received_dmg_split' and e['target']=='all_allies')
        bm._activate(effect,names[0],1.)
        even=dict(type='buff',name='fault-injected-even-overlap',stat='received_dmg_split_even',target='all_allies',duration=10.,trigger=dict(timing=['battle_start'],condition=[]))
        bm._activate(even,names[1],1.)
        with self.assertRaisesRegex(ValueError,'Even and weighted overlap'):model.snapshot(bm,names[4],100.,1.,hp)
        self.assertEqual(model.data['snapshots'],[]);self.assertEqual(hp,{n:1000. for n in names})

if __name__=='__main__':unittest.main()
