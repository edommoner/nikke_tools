"""Grouping/ordering/cleanup contracts; no duplicate damage-formula assertions."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import detail_gpu as g

class FullBatchPlanningTests(unittest.TestCase):
 def helpers(self,closed,calls):
  def evaluation(device,item):
   try:
    result=yield dict(program={'id':item['id']},script=[[0,item['schedule']]],enemy=[item['id']],base_stats={'id':item['id']},seed=item['seed'])
    return dict(value=result['totals'][0][0],compute={'elapsed_ms':result['elapsed_ms'],'workspace_bytes':result['workspace_bytes']})
   finally:closed.append(item['id'])
  def run(device,programs,script,enemies,base_stats,**kwargs):
   ids=[p['id'] for p in programs];calls.append((ids,kwargs['seeds']))
   self.assertEqual(enemies,[[i] for i in ids]);self.assertEqual(base_stats,[{'id':i} for i in ids])
   return dict(queries=[[i] for i in ids],totals=[[i] for i in ids],workspace_bytes=111*len(ids),elapsed_ms=20)
  return evaluation,run
 def test_different_schedules_group_exactly_and_restore_original_order(self):
  closed=[];calls=[];evaluation,run=self.helpers(closed,calls)
  items=[dict(id=i,schedule=s,seed=10+i) for i,s in enumerate((1,2,1,1))]
  with patch.object(g,'_full_evaluation',evaluation),patch.object(g,'run',run):outputs=g.evaluate_full_many(None,items,batch_size=2)
  self.assertEqual(calls,[([0,2],[10,12]),([3],[13]),([1],[11])])
  self.assertEqual([r['value'] for r in outputs],[0,1,2,3]);self.assertEqual(sorted(closed),[0,1,2,3])
  self.assertEqual(outputs[0]['compute']['batch_workspace_bytes'],222)
  self.assertTrue(all(r['compute']['workspace_bytes']==111 for r in outputs))
  self.assertNotIn('batch_size',outputs[1]['compute'])
 def test_single_path_uses_same_preparation_and_decoder(self):
  closed=[];calls=[];evaluation,run=self.helpers(closed,calls)
  with patch.object(g,'_full_evaluation',evaluation),patch.object(g,'run',run):result=g.evaluate_full(None,dict(id=7,schedule=1,seed=42))
  self.assertEqual(result['value'],7);self.assertEqual(calls,[([7],[42])]);self.assertEqual(closed,[7])
 def test_failure_closes_every_pending_decoder_and_preserves_original_error(self):
  closed=[];calls=[];evaluation,_=self.helpers(closed,calls)
  items=[dict(id=i,schedule=1,seed=i) for i in range(3)]
  with patch.object(g,'_full_evaluation',evaluation),patch.object(g,'run',side_effect=RuntimeError('execution failed')),self.assertRaisesRegex(RuntimeError,'execution failed'):g.evaluate_full_many(None,items)
  self.assertEqual(sorted(closed),[0,1,2])
 def test_malformed_result_is_rejected_before_publishing_any_payload(self):
  closed=[];calls=[];evaluation,_=self.helpers(closed,calls)
  items=[dict(id=i,schedule=1,seed=i) for i in range(2)]
  with patch.object(g,'_full_evaluation',evaluation),patch.object(g,'run',return_value={'queries':[],'totals':[],'workspace_bytes':222}),self.assertRaisesRegex(RuntimeError,'batch result layout'):g.evaluate_full_many(None,items)
  self.assertEqual(sorted(closed),[0,1])
 def test_empty_input_and_invalid_batch_sizes_do_not_launch(self):
  with patch.object(g,'run') as run:
   self.assertEqual(g.evaluate_full_many(None,[]),[])
   for size in (True,0,33,1.5):
    with self.subTest(size=size),self.assertRaises(ValueError):g.evaluate_full_many(None,[],batch_size=size)
   run.assert_not_called()

if __name__=='__main__':unittest.main()
