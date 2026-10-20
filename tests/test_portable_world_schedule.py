import copy,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker
from calculator.boss_pattern import BossScript
from portable_world_schedule_specs import compile_schedule

class WorldScheduleInput(unittest.TestCase):
 def base(self):return dict(patterns=[dict(id='a',kind='attack',spec=dict(coeff=100,target='all',hits=3,interval=.1),until=dict(time=1))],frames=[[0,0],[1,0]])
 def test_packing_never_runs_cpu_scheduler_and_preserves_authored_input(self):
  case=self.base();before=copy.deepcopy(case)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('CPU schedule must not become GPU input')):
   words,patterns=compile_schedule(case)
  self.assertEqual(case,before);self.assertEqual(len(words),2320);self.assertEqual(patterns[0].shots.hits,3)
  self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[24:26]))[0],.1)
 def test_unused_node_edge_and_frame_words_remain_zero(self):
  words,_=compile_schedule(self.base())
  self.assertEqual(words[80:2064],[0]*(2064-80));self.assertEqual(words[34:48],[0]*14);self.assertEqual(words[2072:],[0]*(2320-2072))
 def test_unconnected_summon_attacks_fail_instead_of_becoming_empty_schedule(self):
  c=dict(patterns=[dict(kind='summon',spec=dict(hp=10,atk=100,attack=dict(coeff=100,target='all')))],frames=[[0,0]])
  with self.assertRaisesRegex(ValueError,'Summon attack lifecycle'):compile_schedule(c)
 def test_host_capacity_and_clock_stimuli_fail_closed(self):
  cases=[]
  c=self.base();c['patterns']=[{**copy.deepcopy(c['patterns'][0]),'id':str(i)} for i in range(33)];cases.append(c)
  c=self.base();c['patterns'][0]['after']=['start']*9;cases.append(c)
  c=self.base();c['frames']=[[1,0],[0,0]];c['duration']=2;cases.append(c)
  c=self.base();c['frames'][0][1]=1;cases.append(c)
  c=self.base();c.update(clock='accumulated',frames=[],duration=181);cases.append(c)
  c=self.base();c['finish']=1;cases.append(c)
  for case in cases:
   with self.subTest(case=case),self.assertRaises(ValueError):compile_schedule(case)
if __name__=='__main__':unittest.main()
