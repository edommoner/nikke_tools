"""Native removal membership and clock contracts; no CPU replay into GPU."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from portable_specs import LIMITS as L,FIELDS as F,ABI
from portable_removal_specs import plan
from portable_removal_oracle import observe
sp=importlib.util.spec_from_file_location('vremove',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
CASES=json.loads((ROOT/'tests/fixtures/portable-removal.json').read_text())['cases']
def case(name):return copy.deepcopy(next(c for c in CASES if c['name']==name))
class RemovalTests(unittest.TestCase):
 def test_scope_and_recipient_metadata_without_layout_growth(self):
  self.assertEqual(ABI,0x50455669);self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(86016,159744))
  for name,scope in [('removal-default-global',0),('removal-target-self',1),('removal-enemy-boss',2)]:
   c=case(name);before=copy.deepcopy(c);words,_=v.compile_case(c);at=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
   self.assertEqual(words[at+F['TARGET']],scope);self.assertEqual(c,before)
   recipient=words[L['RECIPIENT_BASE']+8:L['RECIPIENT_BASE']+16]
   if scope!=1:self.assertEqual(recipient,[0]*8)
 def test_invalid_scope_is_not_silently_ignored(self):
  base=case('removal-target-self')['effects'][1]
  for value in (None,1,False,'owner','squad'):
   e=copy.deepcopy(base);e['remove_scope']=value
   with self.subTest(value=value),self.assertRaises(ValueError):plan(e,combat={})
  e=copy.deepcopy(base);e['type']='buff'
  with self.assertRaises(ValueError):plan(e,combat={})
  e=copy.deepcopy(base);e['target']='allies_random:1'
  with self.assertRaises(ValueError):plan(e,combat={})
  e=copy.deepcopy(base);e['target']='boss'
  with self.assertRaises(ValueError):plan(e)
 def test_all_authored_native_query_expectations(self):
  for c in CASES:
   if c.get('removal_reference'):
    with self.subTest(name=c['name']):v.contains(observe(c)['queries'],[{k:v for k,v in q.items() if k!='damage'} for q in c['expected_queries']],c['name'])
 def test_partial_removal_does_not_end_surviving_instance(self):
  r=observe(case('removal-partial-does-not-end-instance'));self.assertEqual(r['endings'],[]);self.assertEqual(r['carriers'][0]['recipients'],30)
  r=observe(case('removal-last-recipient-emits-once'));self.assertEqual(r['endings'],[dict(name='State',caster=0,time=.1)])
 def test_pure_instant_timers_have_no_active_carrier_to_remove(self):
  for scope in ('target','global'):
   r=observe(case('removal-pure-instant-clock-survives-'+scope));self.assertEqual(r['carriers'],[]);self.assertEqual(r['timers'],[dict(definition=0,due=.5,expiry=2)])
 def test_enemy_instances_emit_per_removed_recipient(self):
  r=observe(case('removal-enemy-all_enemies'));self.assertEqual(len(r['endings']),3);self.assertEqual(r['queries'][0]['attack_buffs'][0],3)
 def test_existing_mode_fixture_now_checks_real_native_weapon_behavior(self):
  c=next(c for c in v.fixtures() if c['name']=='named-removal-keeps-independent-weapon-mode')
  from portable_weapon_oracle import observe as weapon
  self.assertEqual([q['damage'][0] for q in weapon(c)[0]],[2000,4000]);self.assertTrue(c['weapon_reference'])
 def test_native_weapon_implicit_reload_matches_explicit_wire_default(self):
  from portable_weapon_oracle import observe as weapon
  c=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='named-removal-last-bullet-keeps-mode-magazine'))
  explicit=copy.deepcopy(c);explicit['combat']['weapons'][0]['reload']=1
  self.assertEqual(v.compile_case(c)[0],v.compile_case(explicit)[0])
  self.assertEqual(weapon(c),weapon(explicit))
  self.assertEqual(weapon(c)[0][1]['combat']['weapons'][0]['reload_until'],1.25)
if __name__=='__main__':unittest.main()
