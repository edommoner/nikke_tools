"""Independent lifecycle witnesses for the existing clock / typed-target bridge."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from destructible_world_runtime import DestructibleWorld,compile_bindings
from destructible_world_cases import fixtures,binding
from impact_specs import ActorHandle as H,ActorKind as K,Impact,HitFamily as F,HitOutcome as O
s=importlib.util.spec_from_file_location('dw_test_adapter',ROOT/'research/verify-destructible-world-short.py')
adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
def world(name):
 c=next(c for c in fixtures() if c['name']=='destructible-world/'+name)
 return DestructibleWorld(c['nodes'],c['bindings'])
def hit(w,slot=0,generation=1,amount=100.,credit=1.):
 b=w.bindings[slot]
 return w.hit(slot,Impact('owner0',H(b.handle.kind,b.handle.identity,generation),F.SKILL,O.DAMAGING,amount,credit))
class WorldTests(unittest.TestCase):
 def test_all_native_cases_and_static_only_packing(self):
  rows,packed=adapter.prepare();self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(33,21))
  self.assertEqual(len(packed),4*(1+33*5120))
  for name,_,c in rows:
   if c is not None:
    with self.subTest(name=name):adapter.native_reference(c)
  with patch.object(DestructibleWorld,'advance',side_effect=AssertionError('CPU schedule must not be packed')):
   self.assertEqual(adapter.prepare()[1],packed)
 def test_same_time_reentry_defers_clear_and_rejects_old_generation(self):
  w=world('same-time-reentry-defers-clear');w.advance(0.)
  receipt=hit(w);self.assertTrue(receipt['broken']);self.assertEqual(receipt['notice']['handle'],[2,10,1])
  self.assertFalse(w.advance(0.));self.assertEqual(w.targets.rows[0].handle.generation,1)
  w.advance(.01);self.assertEqual(w.targets.rows[0].handle.generation,2)
  self.assertFalse(hit(w)['delivered']);self.assertEqual(w.targets.rows[0].remaining,100.)
  self.assertEqual(receipt['notice']['handle'],[2,10,1])
 def test_all_bound_targets_required_and_hit_credit_is_separate(self):
  w=world('all-targets-cleared');w.advance(0.);hit(w);w.advance(.1)
  self.assertTrue(w.clock._runs[0].active);self.assertIsNone(w.targets.rows[2])
  hit(w,slot=1);w.advance(.2)
  self.assertFalse(w.clock._runs[0].active);self.assertTrue(w.targets.rows[2].alive)
  self.assertEqual(hit(w,slot=2,amount=99999.,credit=.5)['took'],.5)
  self.assertEqual(w.targets.rows[2].remaining,1.5)
 def test_priority_cleared_before_followed_before_expired(self):
  from portable_world_schedule_specs import OUTCOMES
  for clear in (False,True):
   for reverse in (False,True):
    name=f'priority-{clear}-{reverse}';c=next(c for c in fixtures() if c['name'].endswith('/'+name))
    result=adapter.native_reference(c);index=next(i for i,n in enumerate(c['nodes']) if n['id']=='a')
    a=[r[1] for r in result['history'] if r[0]==index]
    self.assertEqual(a,[OUTCOMES['cleared' if clear else 'followed']])
 def test_finish_does_not_spawn_future_nodes_and_is_terminal(self):
  w=world('finish-does-not-open-new-node');w.advance(0.);w.finish(1.)
  self.assertIsNone(w.targets.rows[0])
  with self.assertRaises(ValueError):w.advance(2.)
  with self.assertRaises(ValueError):w.finish(2.)
 def test_registry_unspawned_and_generation_changes(self):
  w=world('repeat-retires-live');b=w.bindings[0]
  with self.assertRaisesRegex(ValueError,'not spawned'):w.registry.view(b.handle.kind,b.label)
  w.advance(0.);old=w.registry.view(b.handle.kind,b.label).handle;w.advance(.2)
  with self.assertRaisesRegex(ValueError,'Stale'):w.registry.exact(old)
  self.assertEqual(w.registry.view(b.handle.kind,b.label).handle.generation,2)
 def test_high_slot_and_epsilon_use_existing_clock(self):
  w=world('high-slot128');w.advance(0.);self.assertEqual(len(w.targets.select([K.PROJECTILE])),128)
  hit(w,slot=127);self.assertFalse(w.targets.rows[127].alive)
  w=world('expiry-epsilon');w.advance(0.);w.advance(1-2e-9);self.assertTrue(w.targets.rows[0].alive)
  w.advance(1-.5e-9);self.assertFalse(w.targets.rows[0].alive)
 def test_authored_values_not_mutated_or_unmodelled_fields_admitted(self):
  c=copy.deepcopy(fixtures()[3]);before=copy.deepcopy(c);compile_bindings(c['nodes'],c['bindings']);self.assertEqual(c,before)
  c['nodes'][0]['attack']=100
  with self.assertRaisesRegex(ValueError,'unmodelled'):compile_bindings(c['nodes'],c['bindings'])
 def test_saved_gpu_reader_rejects_clock_target_and_notice_corruption(self):
  from portable_backend import source_hashes
  fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-world-raw.json').read_text())
  self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_world_probe.slang'))
  rows,_=adapter.prepare()
  for r in fixture['records']:
   w=array.array('I',[0])*786432
   for i,v in r['nonzero']:w[i]=v
   self.assertEqual(hashlib.sha256(w.tobytes()).hexdigest(),r['output_sha256'])
   name,_,c=rows[r['index']];self.assertEqual(name,r['name'])
   if c is None:
    adapter.validate_rejection(w,name);w[2]=0
    with self.assertRaises(AssertionError):adapter.validate_rejection(w,name)
    continue
   adapter.compare(w,c)
   # Mutate observed generation, graph generation and history count separately.
   for at in (20000+32+2,20000+1824+1,20000+21):
    corrupt=array.array('I',w);corrupt[at]^=1
    with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):adapter.compare(corrupt,c)
   for i,op in enumerate(c['ops']):
    at=20000+i*2640
    if op[0]==1 and w[at+4]:
     corrupt=array.array('I',w);corrupt[at+12]^=1
     with self.assertRaises(AssertionError):adapter.compare(corrupt,c)
     break
if __name__=='__main__':unittest.main()
