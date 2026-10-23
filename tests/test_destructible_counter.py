"""Typed landing admission, synchronous child ordering and exact generations."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('dc_unit','research/verify-destructible-counter-short.py');adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
from destructible_world_runtime import DestructibleWorld
from destructible_impact_runtime import deliver
from effect_runtime import state
from impact_specs import ActorHandle as H,Impact,HitFamily as F,HitOutcome as O
from test_target_counter_runtime import manager,NAMES
class CounterTests(unittest.TestCase):
 def test_literal_completion_and_child_witnesses(self):
  answers={c['name'].split('/')[-1]:adapter.native_reference(c) for c in adapter.fixtures()}
  self.assertEqual(len(answers),13)
  def reasons(name):return [r['reason'] for r in answers[name]['trace']]
  self.assertEqual(reasons('threshold-refresh-before-dead-retirement'),['threshold','death'])
  self.assertEqual(reasons('live-refresh-survives-parent'),['threshold','threshold'])
  self.assertEqual(reasons('death-without-reward'),[])
  self.assertEqual(reasons('miss-no-credit'),[])
  self.assertEqual(answers['threshold-refresh-before-dead-retirement']['counters'][-1]['atk'],adapter.bits(22.))
  self.assertEqual(answers['break-projectile-death']['trace'][0]['actor'],dict(kind=2,identity=10,generation=1))
  self.assertIsNone(answers['break-projectile-death']['trace'][0]['impact'])
  self.assertEqual(answers['old-generation-does-not-credit']['trace'][0]['name'],'next')
  self.assertEqual([(r['name'],r['reason'],r['epoch']) for r in answers['siblings-latched-before-refresh-and-break']['trace']],[('first','threshold',1),('second','threshold',2),('second','death',3)])
  self.assertEqual(answers['siblings-latched-before-refresh-and-break']['counters'][-1]['atk'],adapter.bits(33.))
 def test_packing_runs_no_native_or_gpu_and_input_layout_is_explicit(self):
  import portable_backend
  from portable_specs import LIMITS as L
  with patch.object(adapter,'native_reference',side_effect=AssertionError('No oracle in input construction')),patch.object(portable_backend,'build',side_effect=AssertionError('No GPU build')):
   rows,packed=adapter.prepare()
  self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(18,13))
  self.assertEqual(L['TARGET_COUNTER_INPUT_WORDS'],97464)
  self.assertEqual(rows[0][1][0],L['COUNTER_LANDING_ABI'])
  self.assertEqual(len(packed),4+18*102584*4)
  self.assertLess(L['COUNTER_LANDING_EXTRA_BASE']+128*4,599980)
  self.assertLess(600000+104480,786432)
 def test_threshold_child_cannot_rebind_break_retirement_to_new_generation(self):
  c=next(c for c in adapter.fixtures() if c['name'].endswith('/threshold-projectile-live'))
  c['nodes']=[dict(id='a',after=['start','a'],repeat=2,until=dict(targets_cleared=True))]
  c['effects'][0]['target_counter']['threshold']=1
  w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects']);bm.notify('battle_start',0,NAMES[0]);w.advance(0.)
  original=bm.notify
  def child(event,t,caster,**context):
   result=original(event,t,caster,**context)
   if event=='event:target_counter_complete:marker':w.advance(.1)
   return result
  bm.notify=child
  receipt=deliver(w,bm,0,Impact(NAMES[2],H(2,10,1),F.SKILL,O.DAMAGING,1000.,1.))
  self.assertEqual(receipt['notice']['handle'],[2,10,1]);self.assertEqual(w.targets.rows[0].handle,H(2,10,2))
  self.assertEqual(state(bm).dead_actors,{H(2,10,1)})
  self.assertEqual(state(bm).counter_trace[0][0],0.)
  self.assertEqual(state(bm).event_stack,[]);self.assertEqual(state(bm).impact_stack,[])
 def test_node_expiry_and_stale_delivery_do_not_invent_counter_death(self):
  c=next(c for c in adapter.fixtures() if c['name'].endswith('/old-generation-does-not-credit'))
  answer=adapter.native_reference(c)
  self.assertTrue(all(r['dead']==0 for r in answer['counters']))
  self.assertEqual(answer['counters'][2]['credit'],adapter.bits(0.))
 def test_wrong_kind_or_unbound_attacker_rejects_before_consuming_target(self):
  c=adapter.fixtures()[0];w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects']);w.advance(0.)
  for packet in [Impact(NAMES[0],H(0,10,1),F.SKILL,O.DAMAGING,1000.),Impact('unbound',H(2,10,1),F.SKILL,O.DAMAGING,1000.)]:
   with self.assertRaisesRegex(ValueError,'explicit destructible'):deliver(w,bm,0,packet)
   self.assertTrue(w.targets.rows[0].alive);self.assertEqual(w.targets.rows[0].remaining,1000.)
   self.assertFalse(state(bm).dead_actors)
 def test_saved_gpu_reader_detects_epoch_actor_and_child_value_corruption(self):
  from portable_backend import source_hashes
  from portable_specs import LIMITS as L
  fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-counter-raw.json').read_text())
  from portable_destructible_frame_source_contract import verify_retained_sources
  verify_retained_sources(ROOT,'gpu/destructible_counter_probe.slang',fixture['source_sha256'])
  rows,_=adapter.prepare()
  for r in fixture['records']:
   block=array.array('I',[0])*786432
   for i,v in r['nonzero']:block[i]=v
   self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),r['output_sha256'])
   name,_,c=rows[r['index']];self.assertEqual(name,r['name'])
   if c is None:
    adapter.validate_rejection(block,name);block[0]=0
    with self.assertRaises(AssertionError):adapter.validate_rejection(block,name)
    continue
   adapter.compare(block,c)
   for offset in [L['TARGET_COUNTER_QUERY_BASE']+4,620000+24,620000+32+2,L['TARGET_COUNTER_TRACE_BASE']+6]:
    corrupt=array.array('I',block);corrupt[offset]^=1
    with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):adapter.compare(corrupt,c)
if __name__=='__main__':unittest.main()
