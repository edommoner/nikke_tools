import copy,importlib.util,math,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import validate_effect
s=importlib.util.spec_from_file_location('status_cases',R/'research/build-status-cases.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
s=importlib.util.spec_from_file_location('main_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from test_target_counter_runtime import manager,NAMES
class StatusContracts(unittest.TestCase):
 def test_missing_and_zero_cap_are_distinct_static_inputs(self):
  missing=b.immune();missing.pop('fixed_value');zero=b.immune(fixed_value=0)
  a,_=v.compile_case(b.case('missing',[missing],[b.notify(0)]));z,_=v.compile_case(b.case('zero',[zero],[b.notify(0)]))
  self.assertEqual(a[L['DEFINITION_BASE']+F['FLAGS']]&112,48);self.assertEqual(z[L['DEFINITION_BASE']+F['FLAGS']]&112,112)
 def test_status_metadata_and_charge_storage_are_buffer_owned(self):
  words,_=v.compile_case(b.case('count',[b.immune()],[b.notify(0)]));self.assertEqual(words[L['STATUS_META_BASE']],3)
  self.assertEqual(L['INPUT_WORDS'],77824);self.assertEqual(L['OUTPUT_WORDS']-94208,8192)
  self.assertLessEqual(L['IMMUNITY_USED_BASE']+13*256*2,L['IMMUNITY_SCRATCH_BASE'])
  self.assertLessEqual(L['IMMUNITY_SCRATCH_BASE']+256*4,L['OUTPUT_WORDS'])
 def test_marker_canonicalization_does_not_mutate_authored_definitions(self):
  a=b.buff(stat=None);missing=copy.deepcopy(a);missing.pop('stat');missing['source']='스킬2';z=b.buff(stat='');z['source']='스킬3';effects=[a,missing,z];before=copy.deepcopy(effects)
  words,_=v.compile_case(b.case('marker',effects,[b.notify(0,7)]));self.assertEqual(effects,before)
  self.assertEqual(words[L['DEFINITION_BASE']+F['KIND']],4)
  self.assertEqual(words[L['RECIPIENT_BASE']+6],words[L['RECIPIENT_BASE']+8+6])
  self.assertNotEqual(words[L['RECIPIENT_BASE']+6],words[L['RECIPIENT_BASE']+16+6])
 def test_invalid_cleanse_never_reaches_gpu(self):
  for update in (dict(type='buff'),dict(target=[]),dict(target='unmodeled'),dict(fixed_value=math.inf)):
   with self.subTest(update=update),self.assertRaises((ValueError,TypeError)):validate_effect(dict(b.cleanse(),**update),combat={})
 def test_huge_finite_cleanse_limit_is_not_narrowed_on_cpu(self):
  words,_=v.compile_case(b.case('huge',[b.cleanse(fixed_value=1e308)],[b.notify(0,8)]));self.assertEqual(words[L['DEFINITION_BASE']+F['KIND']],26)
 def test_cleanse_silently_retains_timer(self):
  dot=dict(name='dot',source='스킬1',type='damage',stat='dot_damage',fixed_value=1,target='boss',duration=2,tick_interval=.5,polarity='harmful',trigger=dict(timing=['event:full_reload'],condition=[]))
  bm=manager([dot,b.cleanse(target='boss')]);end=[];notify=bm.notify
  def record(event,*args,**kw):
   if event.startswith('event:state_end:'):end.append(event)
   return notify(event,*args,**kw)
  bm.notify=record;bm.notify('event:full_reload',0,NAMES[0]);timers=dict(bm._dot_timers);bm.notify('hit_count',.1,NAMES[0])
  self.assertEqual(bm._active,[]);self.assertEqual(bm._dot_timers,timers);self.assertEqual(end,[])
 def test_cleanse_publishes_changed_health_ratio_at_outer_boundary(self):
  hp=b.buff(stat='max_hp_pct',fixed_value=-10,target='self',max_stack=1);bm=manager([hp,b.cleanse(target='self')]);bm.state.update(hp={n:10000 for n in NAMES},hp_pct={n:100 for n in NAMES})
  bm.notify('on_attack',0,NAMES[0]);self.assertEqual(bm.state['hp_pct'][NAMES[0]],100);bm.notify('hit_count',.1,NAMES[0]);self.assertEqual(bm.state['hp_pct'][NAMES[0]],90)
 def test_snapshot_hp_cleanse_clips_and_publishes_health(self):
  for value,final in ((-10,9000),(10,10000)):
   with self.subTest(value=value):
    hp=b.buff(stat='max_hp_from_max_hp_pct',fixed_value=value,target='self',max_stack=1);bm=manager([hp,b.cleanse(target='self')]);bm.state.update(hp={n:10000 for n in NAMES},hp_pct={n:100 for n in NAMES})
    bm.notify('on_attack',0,NAMES[0]);self.assertEqual(bm.state['hp_pct'][NAMES[0]],100);bm.notify('hit_count',.1,NAMES[0]);self.assertEqual(bm.state['hp'][NAMES[0]],final);self.assertEqual(bm.state['hp_pct'][NAMES[0]],final/100)
if __name__=='__main__':unittest.main()
