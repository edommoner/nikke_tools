import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import ABI,LIMITS as L
from portable_enemy_target_specs import normalize_seed,target_rule,META_BASE,COMMAND_BASE,RNG_BASE,QUERY_BASE,STATS
from effect_spec import DETAIL_STAT,EXTRA_STAT
class EnemyTargets(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=importlib.util.spec_from_file_location('target_test_core',ROOT/'scripts/verify-portable-combat.py');cls.core=importlib.util.module_from_spec(s);s.loader.exec_module(cls.core)
  cls.cases=json.loads((ROOT/'tests/fixtures/portable-enemy-targets.json').read_text())['cases']
 def test_layout_and_canonical_presence_identities(self):
  self.assertEqual((ABI,L['INPUT_WORDS'],L['OUTPUT_WORDS']),(0x50455673,86016,159744))
  self.assertEqual(STATS,{n:{**DETAIL_STAT,**EXTRA_STAT}[n] for n in ('stealth','taunt')})
  self.assertGreaterEqual(RNG_BASE,L['PROTECTION_BUILD_BASE']+10);self.assertLessEqual(QUERY_BASE+64*8,L['SPLIT_HIT_BASE']);self.assertLessEqual(COMMAND_BASE+64*4,L['INPUT_WORDS'])
 def test_uint64_decimal_wire_encoding_and_invalid_seeds(self):
  for seed in (0,1,2**32,2**64-1):
   self.assertEqual(normalize_seed(seed),seed);self.assertEqual(normalize_seed(str(seed)),seed)
   a=copy.deepcopy(self.cases[0]);a['enemy_targeting']['seed']=seed;b=copy.deepcopy(a);b['enemy_targeting']['seed']=str(seed)
   wa,_=self.core.compile_case(a);wb,_=self.core.compile_case(b);self.assertEqual(wa,wb);self.assertEqual(wa[META_BASE+1:META_BASE+3],[seed&0xffffffff,seed>>32])
  for seed in (-1,2**64,True,1.0,float('nan'),float('inf'),'01','+1','-1',' 1','1.0','١'):
   with self.subTest(seed=seed),self.assertRaises(ValueError):normalize_seed(seed)
 def test_rules_follow_native_parser_and_large_population_normalization(self):
  from calculator.boss_pattern import _target_rule
  for target in ('all','random:1','random:0002','random:999','top_atk:6','slot:5,1,3,1','slot: 2, 4'):
   for ignore in (False,True):
    spec=dict(target=target,ignore_taunt=ignore)
    if target=='all' and ignore:
     with self.assertRaises(ValueError):target_rule(spec)
     continue
    n=_target_rule(spec,'shared-target-test',5);rule={'all':0,'slot':1,'random':2,'top_atk':3}[n['rule']]
    expected=[rule,len(n['slots']) if rule==1 else min(n['n'],5),sum((who+1)<<(3*i) for i,who in enumerate(n['slots'])),int(ignore)]
    self.assertEqual(target_rule(spec),expected)
 def test_rule_coverage_masks_and_command_reservations_fail_closed(self):
  base=self.cases[0]
  variants=[]
  c=copy.deepcopy(base);c['enemy_targeting']['attacks']={};variants.append(c)
  c=copy.deepcopy(base);c['enemy_targeting']['attacks']['0']=dict(target='all');variants.append(c)
  c=copy.deepcopy(base);c['enemy_targeting']['attacks']['01']=c['enemy_targeting']['attacks'].pop('1');variants.append(c)
  for word in (3,4):
   c=copy.deepcopy(base);c['script'][1][word]=1;variants.append(c)
  for c in variants:
   with self.subTest(case=c['name']),self.assertRaises(ValueError):self.core.compile_case(c)
  words,meta=self.core.compile_case(base);at=L['COMMAND_BASE']+8
  self.assertEqual(words[at+3:at+8],[1,0,0,0,0]);self.assertTrue(meta['enemy_targeting']['enabled']);self.assertTrue(meta['protection_enabled'])
 def test_native_long_sequences_cross_mt_boundary_and_integer_seed_matches_text(self):
  from portable_enemy_target_oracle import observe
  for name in ('enemy-long-rng-190','enemy-long-rng-765'):
   c=next(c for c in self.cases if c['name']==name);n=observe(c)
   self.assertEqual(len(c['script']),64);self.assertEqual((n['rng']['draws'],n['rng']['index']),(627,3));self.assertEqual(len(n['hits']),315)
  a=next(c for c in self.cases if c['name']=='enemy-random-sequence-18446744073709551615');b=next(c for c in self.cases if c['name']=='enemy-decimal-seed-18446744073709551615');self.assertEqual(observe(a),observe(b))
 def test_native_source_reference_uses_the_between_frame_attack_time(self):
  from portable_enemy_target_oracle import observe
  c=next(c for c in self.cases if c['name']=='enemy-source-time-between-frames');n=observe(c)
  self.assertEqual([r['targets'] for r in n['selection']],[[0],[1]])
 def test_legacy_program_keeps_unused_regions_zero_and_new_fields_absent(self):
  from portable_runtime import decode
  case=self.core.fixtures()[0];words,meta=self.core.compile_case(case)
  self.assertFalse(meta['enemy_targeting']['enabled']);self.assertEqual(words[META_BASE:COMMAND_BASE+64*4],[0]*(8+64*4))
  result=decode([0]*L['OUTPUT_WORDS'],meta);self.assertNotIn('enemy_rng',result);self.assertNotIn('enemy_selection',result)
if __name__=='__main__':unittest.main()
