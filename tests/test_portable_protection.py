import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_specs import LIMITS as L,FIELDS as F
from portable_protection_specs import policy
from portable_protection_oracle import observe
s=importlib.util.spec_from_file_location('protection_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-protection.json').read_text())['cases']
class ProtectionContracts(unittest.TestCase):
 def test_static_policy_is_shared_and_original_definition_is_preserved(self):
  c=copy.deepcopy(CASES[0]);original=copy.deepcopy(c);words,meta=v.compile_case(c);self.assertEqual(c,original)
  self.assertEqual(words[L['PROTECTION_META_BASE']],1);self.assertEqual(words[L['PROTECTION_DEFINITION_BASE']],1)
  for case in CASES:
   packed,_=v.compile_case(case);kinds=[policy(e)&255 for e in case['effects']]
   self.assertEqual(packed[L['PROTECTION_META_BASE']],(1 if any(kinds) else 0)|(2 if 4 in kinds else 0)|(4 if 7 in kinds else 0)|(8 if 3 in kinds else 0)|(16 if 8 in kinds else 0))
  self.assertTrue(meta['protection_enabled']);self.assertEqual(L['PROTECTION_OBJECTS'],2*L['CARRIERS'])
  source=(R/'gpu/event_runtime.slang').read_text();body=source.split('struct Runtime\n{',1)[1].split('};',1)[0];self.assertNotIn('protection',body.lower())
 def test_layered_stimulus_is_authored_not_a_cpu_damage_or_target_trace(self):
  c=copy.deepcopy(CASES[0]);words,_=v.compile_case(c);index=next(i for i,x in enumerate(c['script']) if x[1]==31);at=L['COMMAND_BASE']+index*8
  self.assertEqual(words[at],31);self.assertEqual(words[at+5],1);self.assertEqual(words[at+6:at+8],[0,0])
  for field,bad in ((2,2),(3,32),(4,0),(5,0),(6,-1),(7,-1)):
   changed=copy.deepcopy(c);changed['script'][index][field]=bad
   with self.subTest(field=field),self.assertRaises(ValueError):v.compile_case(changed)
 def test_new_descriptors_are_accepted_but_unported_lifetimes_and_targets_fail(self):
  from portable_trigger_specs import validate_input
  validate_input(dict(trigger=dict(timing=['event:shield_applied','event:shield_consumed'],condition=['during_shield'])))
  for changes in (dict(duration_scaling='stack_count'),dict(target='boss'),dict(end_on_shield_consumed=1)):
   c=copy.deepcopy(CASES[0]);c['effects'][0].update(changes)
   with self.subTest(changes=changes),self.assertRaises(ValueError):v.compile_case(c)
 def test_native_nonpiercing_hit_stops_at_broken_shield(self):
  c=next(c for c in CASES if c['name']=='protection-shield_from_max_hp_pct-pierce-False-cover-0');r=observe(c)
  self.assertEqual(r['hits'][0]['hp'],0);self.assertEqual(r['hits'][0]['shield'],100);self.assertEqual(r['hits'][0]['hp_after'],1000)
  self.assertEqual(r['hits'][1]['hp'],150)
 def test_native_snapshot_and_amplification_are_per_recipient(self):
  c=next(c for c in CASES if c['name']=='protection-amp-partial-maps');r=observe(c);self.assertEqual(r['queries'][0]['protection'][0]['shield_capacity'],250)
  self.assertEqual([x['shield_capacity'] for x in r['queries'][0]['protection'][1:]],[150]*4)
  self.assertFalse(any(e['event']=='event:state_end:amp' for e in r['events']))
 def test_native_captured_object_is_not_replaced_by_new_carrier(self):
  c=next(c for c in CASES if c['name']=='protection-captured-object-survives-carrier-reuse');r=observe(c)
  self.assertEqual(r['hits'][0]['shield'],300);self.assertEqual(r['hits'][0]['hp'],250)
  self.assertEqual(r['protection'][0]['shield'],100)
  self.assertEqual(sum(e['event']=='event:shield_consumed' for e in r['events']),2)
 def test_native_conditional_max_hp_is_inactive_until_shield_exists(self):
  c=next(c for c in CASES if c['name']=='protection-refresh-observes-old-shield-when-snapshotting');r=observe(c)
  self.assertEqual(r['queries'][0]['allies'][0]['max_hp'],1000)
  self.assertFalse(r['queries'][0]['protection'][0]['has_shield'])
  self.assertEqual(r['queries'][1]['protection'][0]['shield'],100)
  self.assertEqual(r['queries'][2]['protection'][0]['shield'],200)
 def test_native_alias_refresh_rebuilds_first_definition_and_notifies(self):
  for maximum,capacity in ((1,100),(2,200)):
   c=next(c for c in CASES if c['name']=='protection-alias-refresh-keeps-first-definition-'+str(maximum));r=observe(c)
   self.assertEqual(r['protection'][0]['shield_capacity'],capacity)
   self.assertEqual(sum(e['event']=='event:shield_applied' for e in r['events']),2)
 def test_protection_quantities_reject_boolean_string_nonfinite_and_huge_int(self):
  for value in (True,'1',float('inf'),float('nan'),1<<4096):
   c=copy.deepcopy(CASES[0]);c['effects'][0]['fixed_value']=value
   with self.subTest(value=type(value).__name__),self.assertRaises(ValueError):v.compile_case(c)
if __name__=='__main__':unittest.main()
