"""Original normalized selectors/flags feed one common typed skill Frame."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('skill_gpu_tests',ROOT/'research/verify-destructible-skill-retention-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_specs import LIMITS as L,FIELDS as F
from portable_destructible_roster_input import compile_weapon_shield_roster

class SkillShieldGPUTests(unittest.TestCase):
 def test_all157_inputs_pack_without_native_events(self):
  from calculator import timeline
  with patch.object(timeline,'simulate',side_effect=AssertionError('No native battle during packing')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,raw=a.prepare()
  self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(157,102));self.assertEqual(len(raw),4+157*110112*4)
  from portable_readiness_semantics import reference_readiness
  r=reference_readiness(dict(phase='effect',category='effect',kind='buff',stat='shield_dmg_pct',target='self'));v=r['typed_roster_skill_battle_validation']
  self.assertEqual((v['inputs'],v['native_cases'],v['new_original_roster_cases']),(157,102,4));self.assertTrue(v['metal_verified'])
  self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified']);self.assertFalse(v['cuda_device_verified']);self.assertFalse(v['original_full_profile_verified'])
 def test_original_normalized_selector_and_damage_flags_are_untouched(self):
  rows,_=a.new.prepare()
  for name,w,domain in rows[:4]:
   c,m,p,_=domain;before=copy.deepcopy(p)
   legacy,_=compile_weapon_shield_roster(p,c['typed_bindings'],max_attacks=c['max_attacks']);self.assertEqual(p,before)
   self.assertEqual(w[:109824],legacy[:109824]);self.assertEqual(w[110080],0x48534934);self.assertEqual(w[110081:],legacy[110081:])
   routes=[]
   for row,index in enumerate(m['binding_source_indices']):
    e=p['effects'][index]['effect'];self.assertEqual(w[109824+row],4 if e['type']=='damage' else 0)
    if e['type']=='damage':
     at=L['DAMAGE_DEFINITION_BASE']+row*8;routes.append((w[at],w[at+1],w[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']]&12289))
   self.assertEqual(routes,[(6,1,0),(2,128,0),(7,1,8193)])
 def test_old141_order_and_input_words_still_exact(self):
  rows,_=a.prepare();old=a.old.prepare()[0]
  for (name,w,d),(oname,ow,od) in zip(rows[:141],old,strict=True):self.assertEqual((name,w),(oname,ow))
 def test_reviewed_inverse_is_exact_and_numeric_core_is_reused(self):
  from portable_destructible_roster_skill_source_contract import project_sources
  f=json.loads((ROOT/'tests/fixtures/portable-destructible-roster-skill-source-delta.json').read_text());self.assertEqual(len(f['sources']),4);project_sources(ROOT)
  for name,row in f['sources'].items():
   with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})
  source=(ROOT/'gpu/destructible_roster_skill_runtime.slang').read_text()
  for call in ('actorSetCapture(','sampleDamageFactorsForReach(','damageFromFactors('):self.assertEqual(source.count(call),1)
  self.assertNotIn('f64Mul(',source);self.assertNotIn('dispatch(',source)
 def test_opt_in_rejects_add_world_and_untyped_boolean(self):
  c=a.new.fixtures()[0];p=a.new.roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
  with self.assertRaisesRegex(ValueError,'boolean'):compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=1)
  for kind in ('parts','interrupt','summon'):
   bad=copy.deepcopy(p);bad['enemy']['patterns'].append(dict(id='unsupported',kind=kind))
   with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'single boss'):compile_weapon_shield_roster(bad,c['typed_bindings'],skill_shields=True)

class SavedSkillReadbackTests(unittest.TestCase):
 def test_actual_original_skill_readback_rejects_metadata_and_landing_corruption(self):
  from portable_backend import source_hashes
  f=json.loads((ROOT/'tests/fixtures/portable-destructible-skill-rosters-raw.json').read_text());rows,_=a.prepare()
  from portable_destructible_lifesteal_source_contract import verify_retained_sources
  verify_retained_sources(ROOT,'gpu/destructible_roster_skill_entry.slang',f['source_sha256'])
  checked=0
  for record in f['records']:
   name,w,domain=rows[record['index']];self.assertEqual(name,record['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),record['input_sha256'])
   block=array.array('I',[0])*f['output_words']
   for at,value in record['nonzero']:block[at]=value
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
   if domain is None:
    a.validate_rejection(block,name);block[0]=0
    with self.assertRaises(AssertionError):a.validate_rejection(block,name)
    checked+=1;continue
   a.compare(block,domain)
   for at in (0,L['HEALTH_QUERY_BASE'],L['COMBAT_QUERY_BASE'],787460,790004,790008,790020,790022):
    bad=array.array('I',block);bad[at]^=1
    with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(bad,domain)
    checked+=1
   if record['index'] in (142,143):
    # Dola's original rank1 burst is packet20, Rei's original B3 is packet30.
    for packet in (20,30):
     for word in (1,6,11,12,13,14,15):
      bad=array.array('I',block);bad[790000+packet*1040+word]^=1
      with self.subTest(name=name,packet=packet,word=word),self.assertRaises(AssertionError):a.compare(bad,domain)
      checked+=1
  self.assertEqual(checked,61)

if __name__=='__main__':unittest.main()
