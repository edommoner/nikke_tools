"""Real skill packets and target counters share the HP/hit shield Frame."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('hit_shield_tests',ROOT/'research/verify-destructible-hit-shield-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from world_destructible_shield_battle_native import observe
from portable_destructible_hit_shield_contracts import verify

class HitShieldTests(unittest.TestCase):
 def test_eighteen_literal_battles_separate_credit_from_damage(self):
  self.assertEqual(len(a.fixtures()),18)
  for c in a.fixtures():
   with self.subTest(name=c['name']):self.assertTrue(verify(c,observe(c)[0])['reference_model_gap'])

 def test_prior88_input_and_native_fingerprints_unchanged(self):
  rows,_=a.prepare();old=json.loads((ROOT/'research/portable-destructible-shield-battle-short-expected.json').read_text())
  self.assertEqual(len(old['entries']),88)
  for (name,w,c),r in zip(rows[:88],old['entries'],strict=True):
   with self.subTest(name=name):
    self.assertEqual(name,r['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),r['input_sha256'])
    self.assertEqual(a.cross.digest(dict(status=64) if c is None else a.native_reference(c)),r['native_sha256'])

 def test_pack_never_uses_a_cpu_attack_list(self):
  with patch.object(a.base.battle,'observe',side_effect=AssertionError('No oracle')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,data=a.prepare()
  self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(111,76));self.assertEqual(len(data),4+111*110112*4)

 def test_hit_policy_requires_explicit_boolean_and_owner(self):
  from destructible_battle_runtime import typed_battle
  from destructible_shield_policy import BOSS,select
  for kw in (dict(hit_shields=1,shield_owner=BOSS),dict(hit_shields=True),dict(hit_shields='yes',shield_owner=BOSS)):
   with self.subTest(kw=kw),self.assertRaises(ValueError):
    with typed_battle(a.fixtures()[0]['typed_bindings'],modifier_model=True,**kw):pass
  with self.assertRaisesRegex(ValueError,'boolean'):select(None,BOSS,hit_shields=1)

 def test_exact_source_inverse_rejects_unreviewed_changes(self):
  from portable_destructible_hit_shield_source_contract import project_sources
  d=json.loads((ROOT/'tests/fixtures/portable-destructible-hit-shield-source-delta.json').read_text());project_sources(ROOT)
  for name,row in d['sources'].items():
   with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})

 def test_actual_metal_credit_owner_generation_and_counter_receipts(self):
  from portable_backend import source_hashes
  f=json.loads((ROOT/'tests/fixtures/portable-destructible-hit-shield-raw.json').read_text());rows,_=a.prepare()
  self.assertEqual(f['source_sha256'],source_hashes('gpu/destructible_shield_battle_entry.slang'))
  for record in f['records']:
   name,words,domain=rows[record['index']];self.assertEqual(name,record['name'])
   self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
   block=array.array('I',[0])*f['output_words']
   for at,value in record['nonzero']:block[at]=value
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
   if domain is None:
    a.validate_rejection(block,name);block[0]=0
    with self.assertRaises(AssertionError):a.validate_rejection(block,name)
    continue
   a.compare(block,domain)
   for at in (0,787458,787460,787466,790001,790006,790020,790022):
    changed=array.array('I',block);changed[at]^=1
    with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(changed,domain)

if __name__=='__main__':unittest.main()
