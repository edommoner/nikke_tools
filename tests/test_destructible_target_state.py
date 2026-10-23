"""Typed target state invariants before wiring absent world-model consumers."""
import importlib.util,sys,unittest,array,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_target_state import DestructibleTargets
from impact_specs import ActorHandle as H,ActorKind as K,Impact,HitFamily as F,HitOutcome as O
from destructible_target_cases import fixtures
s=importlib.util.spec_from_file_location('dt_state_test',ROOT/'research/verify-destructible-target-core-short.py');adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
class StateTests(unittest.TestCase):
 def test_literal_contracts_and_invalid_operations(self):
  cases=fixtures();self.assertEqual(len(cases),42);self.assertEqual(sum(not c['reject'] for c in cases),24)
  for c in cases:
   with self.subTest(case=c['name']):
    if c['reject']:
     with self.assertRaises(ValueError):adapter.native_reference(c)
    else:adapter.native_reference(c)
 def test_generation_and_expiry_prevent_recycled_target_delivery(self):
  w=DestructibleTargets(1);w.spawn(0,H(K.PROJECTILE,0),100.,1.);w.advance(1.)
  self.assertEqual(w.select([K.PROJECTILE]),());w.spawn(0,H(K.PROJECTILE,0,2),50.)
  stale=Impact('A',H(K.PROJECTILE,0),F.SKILL,O.DAMAGING,1000.)
  self.assertFalse(w.hit(0,stale)['delivered']);self.assertEqual(w.rows[0].remaining,50.)
 def test_hit_and_hp_quantity_axes_are_separate(self):
  w=DestructibleTargets(2);w.spawn(0,H(K.HP_SHIELD,0),100.);w.spawn(1,H(K.HIT_SHIELD,0),2.)
  self.assertEqual(w.hit(0,Impact('A',H(K.HP_SHIELD,0),F.SKILL,O.DAMAGING,40.,.25))['took'],40.)
  self.assertEqual(w.hit(1,Impact('A',H(K.HIT_SHIELD,0),F.SKILL,O.DAMAGING,40000.,.25))['took'],.25)
  self.assertEqual([r.remaining for r in w.rows],[60.,1.75])
 def test_all_projectiles_does_not_select_owner_or_shields(self):
  w=DestructibleTargets(3)
  for slot,kind in enumerate((K.HP_SHIELD,K.PROJECTILE,K.HIT_SHIELD)):w.spawn(slot,H(kind,0),3.,owner=H(K.BODY,0))
  self.assertEqual(w.select([K.PROJECTILE]),(1,));self.assertEqual(w.select([K.HP_SHIELD,K.HIT_SHIELD]),(0,2))
 def test_existing_actor_registry_tracks_live_owner_and_respawn(self):
  from world_actor_runtime import ActorRegistry
  registry=ActorRegistry();body=H(K.BODY,0);registry.bind(K.BODY,'body',lambda:(1,True,None),identity=0)
  w=DestructibleTargets(1);w.spawn(0,H(K.PROJECTILE,17),10.,1.,owner=body);w.bind_registry(0,'projectile',registry)
  old=registry.view(K.PROJECTILE,'projectile').handle;self.assertEqual(registry.root(old).handle,body)
  w.advance(1.);self.assertFalse(registry.exact(old).alive);w.spawn(0,H(K.PROJECTILE,17,2),20.,owner=body)
  with self.assertRaisesRegex(ValueError,'Stale'):registry.exact(old)
  self.assertEqual(registry.view(K.PROJECTILE,'projectile').handle,H(K.PROJECTILE,17,2))
 def test_existing_battle_sources_and_numeric_core_remain_identical(self):
  from portable_backend import source_hashes
  golden=json.loads((ROOT/'research/portable-world-projectile-chain-short-expected.json').read_text())
  self.assertEqual(source_hashes('gpu/world_projectile_chain_entry.slang'),golden['source_sha256'])
 def test_saved_GPU_states_reject_identity_quantity_and_selection_corruption(self):
  from portable_backend import source_hashes
  fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-target-core-raw.json').read_text());self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_target_probe.slang'))
  rows,_=adapter.prepare()
  for record in fixture['records']:
   block=array.array('I',[0])*786432
   for i,v in record['nonzero']:block[i]=v
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
   name,_,domain=rows[record['index']];self.assertEqual(name,record['name'])
   if domain is None:
    adapter.validate_rejection(block,name);block[2]=0
    with self.assertRaises(AssertionError):adapter.validate_rejection(block,name)
    continue
   adapter.compare(block,domain)
   # Alter actual snapshots/returns, not unrelated zero padding.
   op=next(i for i,o in enumerate(domain['ops']) if o[0]==1 or o[0]==3)
   at=2048+op*1824
   for offset in [at+32+2,at+32+4,at+2 if domain['ops'][op][0]==1 else at+8]:
    corrupt=array.array('I',block);corrupt[offset]^=1
    with self.subTest(case=name,offset=offset),self.assertRaises(AssertionError):adapter.compare(corrupt,domain)
 def test_no_battle_feature_is_silently_admitted(self):
  from portable_runtime import validate_effect
  for effect in [dict(type='damage',stat='damage',target='all_projectiles',fixed_value=100),dict(type='buff',stat='shield_dmg_pct',target='self',fixed_value=50)]:
   with self.assertRaises(ValueError):validate_effect(effect,combat={},world_frame=True)
if __name__=='__main__':unittest.main()
