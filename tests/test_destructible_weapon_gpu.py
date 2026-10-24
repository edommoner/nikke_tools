"""Original per-shot factors feed typed pellets and unchanged body continuations."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('weapon_gpu_tests',ROOT/'research/verify-destructible-weapon-shield-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class WeaponGPUTests(unittest.TestCase):
 def test_exact_clock_matches_static_native_weapon_metadata_without_a_battle(self):
  from calculator import timeline
  from world_frame_native import authored_metadata,roster_names
  from portable_charge_clock_specs import normalize_static_clock
  with patch.object(timeline,'simulate',side_effect=AssertionError('No battle times')):
   for c in a.fixtures():
    with self.subTest(name=c['name']),patch.dict(timeline._NIKKE,authored_metadata(c)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
     self.assertEqual(normalize_static_clock([dict(name=n) for n in roster_names(c)],c['base_atk'],c['enemy']),c['post_fire_delays'])

 def test_141_definition_inputs_need_no_cpu_shot_list_or_fake_skill(self):
  with patch.object(a.battle,'observe',side_effect=AssertionError('No oracle')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,raw=a.prepare()
  self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(141,98));self.assertEqual(len(raw),4+141*110112*4)
  self.assertEqual(rows[111][1][109520],0xffffffff)
  self.assertEqual(len(rows[111][2][0]['effects']),len(a.fixtures()[0]['effects']))
  self.assertFalse(any(rows[111][1][109824:110080]))
  bad=dict(a.fixtures()[0],enemy=dict(a.fixtures()[0]['enemy'],coord={}))
  with self.assertRaisesRegex(ValueError,'coordinate policy'):a.compile_case(bad)

 def test_all111_prior_input_and_native_fingerprints_retained(self):
  rows,_=a.prepare();old=json.loads((ROOT/'research/portable-destructible-hit-shield-short-expected.json').read_text())
  for (name,w,domain),r in zip(rows[:111],old['entries'],strict=True):
   with self.subTest(name=name):
    self.assertEqual(name,r['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),r['input_sha256'])
    self.assertEqual(a.cross.digest(dict(status=64) if domain is None else a.native_reference(domain)),r['native_sha256'])

 def test_hooks_share_unchanged_factors_receipts_and_exact_historical_projection(self):
  from portable_destructible_weapon_source_contract import project_sources
  d=json.loads((ROOT/'tests/fixtures/portable-destructible-weapon-source-delta.json').read_text());self.assertEqual(len(d['sources']),4);project_sources(ROOT)
  for name,row in d['sources'].items():
   with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})
  source=(ROOT/'gpu/destructible_weapon_runtime.slang').read_text()
  self.assertEqual(source.count('sampleDamageFactorsForReach('),1)
  self.assertIn('damageFromFactors(',source);self.assertIn('dwLand(',source);self.assertIn('collectTargetCounters(',source)
  self.assertNotIn('f64Mul(',source)

class WeaponSavedReadbackTests(unittest.TestCase):
 def test_actual_metal_pellet_receipts_and_charge_times_reject_corruption(self):
  from portable_backend import source_hashes
  f=json.loads((ROOT/'tests/fixtures/portable-destructible-weapon-raw.json').read_text());rows,_=a.prepare()
  self.assertEqual(source_hashes(ROOT/'gpu/destructible_weapon_shield_entry.slang'),f['source_sha256'])
  checked=0
  for record in f['records']:
   name,words,domain=rows[record['index']];self.assertEqual(name,record['name'])
   self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
   block=array.array('I',[0])*f['output_words']
   for at,value in record['nonzero']:block[at]=value
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
   if domain is None:
    a.validate_rejection(block,name);block[0]=0
    with self.assertRaises(AssertionError):a.validate_rejection(block,name)
    checked+=1;continue
   a.compare(block,domain)
   for at in (0,787460,790001,790006,790008,790020,790022,790012,790013,790004):
    changed=array.array('I',block);changed[at]^=1
    with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(changed,domain)
    checked+=1
  self.assertEqual(checked,91)

if __name__=='__main__':unittest.main()
