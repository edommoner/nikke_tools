"""Preserve the exact shared wire while avoiding gigantic struct format caches."""
import copy,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
import portable_runtime as runtime
from portable_specs import LIMITS as L
class WireArrayTests(unittest.TestCase):
 def test_bit_exact_legacy_wire_for_all_integer_boundary_patterns(self):
  patterns=[0,1,255,256,0x7fffffff,0x80000000,0xffffffff,0x7ff00000,0xfff00000,0x7ff80001]
  programs=[]
  for shift in (0,3):programs.append(([patterns[(i+shift)%len(patterns)] for i in range(L['INPUT_WORDS'])],{}))
  before=copy.deepcopy(programs);words=[2]+programs[0][0]+programs[1][0]
  self.assertEqual(runtime.pack_programs(programs),struct.pack('<'+str(len(words))+'I',*words));self.assertEqual(programs,before)
 def test_malformed_wire_is_rejected(self):
  for programs in ([],[([], {})],[([0]*L['INPUT_WORDS'],{})]*(L['BATCH']+1)):
   with self.assertRaises(ValueError):runtime.pack_programs(programs)
  for value in (-1,2**32):
   words=[0]*L['INPUT_WORDS'];words[-1]=value
   with self.assertRaises(OverflowError):runtime.pack_programs([(words,{})])
 def test_array_readback_preserves_old_decoded_shape_and_numeric_bits(self):
  import array,json
  from timer_registry_cases import NAMES
  chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
  effect=dict(name='State',source='스킬1',type='buff',stat='atk_pct',fixed_value=10,target='self',trigger=dict(timing=['battle_start'],condition=[]))
  _,meta=runtime.compile_program(chars,[(effect,NAMES[0])],[[0,2,0,0,-1,0,0,0]],[1000]*5)
  words=array.array('I',[0])*L['OUTPUT_WORDS'];words[1]=1
  for at,value in [(L['QUERY_BASE'],1.25),(L['QUERY_BASE']+2,1e16)]:
   words[at:at+2]=array.array('I',struct.unpack('<2I',struct.pack('<d',value)))
  words[L['QUERY_BASE']+12]=0x80000000
  actual=runtime.decode(words,meta);self.assertEqual(actual,runtime.decode(tuple(words),meta));json.dumps(actual)
  self.assertEqual(actual['queries'][0]['time'],1.25);self.assertEqual(actual['queries'][0]['damage'][0],1e16);self.assertEqual(actual['queries'][0]['active_timer_mask'],0x80000000)
 def test_wrong_output_length_is_rejected_before_decode(self):
  program=([0]*L['INPUT_WORDS'],{})
  with patch.object(runtime,'execute',return_value=(bytes(4),{})):
   with self.assertRaisesRegex(RuntimeError,'output stride'):runtime.run_programs([program])
if __name__=='__main__':unittest.main()
