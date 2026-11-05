"""Original carriers plus an explicitly separated declared projectile attack."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('original_modifier_probe_test',ROOT/'research/verify-original-modifier-probe-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalModifierProbeTests(unittest.TestCase):
    def test_originals_preserved_and_only_declared_source_is_routed(self):
        from calculator import timeline
        from portable_specs import LIMITS as L,FIELDS as F
        from destructible_damage_policy import modifier_axis
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in probe input')):rows,_=a.prepare()
        self.assertEqual(len(rows),19)
        for _,words,(c,m,p,_) in rows:
            self.assertEqual(p['effects'][:-1],c['original_effects']);self.assertEqual(c['probe_source'],len(c['original_effects']));self.assertEqual(len(m['effects']),len(p['effects']))
            source=m['binding_source_indices'].index(c['probe_source']);self.assertEqual(words[109520],source)
            self.assertEqual(words[109824:110080],[c.get('probe_kind',2) if row==source else 0 for row in range(256)])
            self.assertEqual([words[109568+row] for row in range(len(m['effects']))],[modifier_axis(p['effects'][i]['effect']) for i in m['binding_source_indices']])
    def test_original_shield_predicate_uses_existing_common_consumer(self):
        text=(ROOT/'gpu/destructible_original_modifier_entry.slang').read_text()
        self.assertIn('#define PORTABLE_COORDINATE_ORIGINAL_SHIELD_HEAL',text)
        self.assertIn('#include "destructible_shield_battle_entry.slang"',text)
        self.assertIn('kind == C_SHIELD && !hasProtection(s,owner,1)',(ROOT/'gpu/event_runtime.slang').read_text())
        _,_,(c,m,p,_)=next(row for row in a.prepare()[0] if row[2][0].get('probe_kind')==3 and row[2][0]['character']=='아스카')
        self.assertTrue(any('during_shield' in row['effect'].get('trigger',{}).get('condition',[]) for row in p['effects']))
    def test_typed_kind_owner_and_unrouted_boss_damage_are_rejected(self):
        from portable_original_modifier_probe_input import compile_probe
        rows,_=a.prepare();_,_,(c,m,p,_)=next(r for r in rows if r[2][0].get('probe_kind')==3)
        for changed in ('kind','owner','generation','other-damage'):
            bad=copy.deepcopy(p);bindings=copy.deepcopy(c['typed_bindings'])
            if changed=='kind':bindings[0]['kind']=2
            elif changed=='owner':bindings[0]['owner']=[0,1,1]
            elif changed=='generation':bindings[0]['owner']=[0,0,2]
            else:bad['effects'].append(dict(owner=bad['effects'][c['probe_source']]['owner'],effect=dict(c['declared_effects'][0],name='unrouted-boss-probe')))
            with self.subTest(changed=changed),self.assertRaises(ValueError):compile_probe(bad,bindings,c['probe_source'],probe_kind=3)
        for kind in (True,0,1,4):
            with self.subTest(kind=kind),self.assertRaises(ValueError):compile_probe(p,c['typed_bindings'],c['probe_source'],probe_kind=kind)
    def test_nearby_specialization_requires_closed_single_enemy_world(self):
        from portable_original_modifier_probe_input import compile_probe
        from portable_enemy_specs import damage_plan
        rows,_=a.prepare();_,_,(c,m,p,_)=next(r for r in rows if r[2][0]['character']=='일레그')
        selected=[i for i,e in enumerate(p['effects']) if e['effect'].get('target')=='target_and_nearby:2']
        self.assertTrue(selected);self.assertEqual(m['declared_original_modifier_probe']['single_boss_nearby_rows'],selected)
        for i in selected:
            with self.assertRaises(ValueError):damage_plan(p['effects'][i]['effect'])
        for changed in ('flag','part','coord'):
            bad=copy.deepcopy(p)
            if changed=='flag':bad['enemy']['has_parts']=True
            elif changed=='part':bad['enemy']['patterns'].append(dict(id='new-part',kind='parts',targets=[dict(name='arm',hp=1000.)]))
            else:bad['enemy']['coord']=dict(auto_aim=[0.,0.])
            with self.subTest(changed=changed),self.assertRaises(ValueError):compile_probe(bad,c['typed_bindings'],c['probe_source'])
if __name__=='__main__':unittest.main()
