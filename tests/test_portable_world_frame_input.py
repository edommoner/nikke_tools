import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('world_frame_input',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from calculator.boss_pattern import BossScript
from portable_specs import ABI,LIMITS
from portable_backend import source_hashes

class WorldFrameInput(unittest.TestCase):
 def test_512_attacks_use_three_gpu_clock_commands_without_cpu_scheduler(self):
  case=copy.deepcopy(f.fixtures()[0]);case['patterns'][0]['spec'].update(hits=512,interval=0,target='random:3');before=copy.deepcopy(case)
  with patch.object(BossScript,'begin_frame',side_effect=AssertionError('CPU scheduling is not a GPU input builder')):words,_=f.compile_case(case)
  self.assertEqual(case,before);self.assertEqual(words[2],3);self.assertEqual([words[LIMITS['COMMAND_BASE']+8*i] for i in range(3)],[24,30,2]);self.assertEqual(words[86016+16+6],512)
  self.assertEqual(words[f.WF_PAYLOAD+4:f.WF_PAYLOAD+8],[0]*4)
 def test_unconnected_world_payloads_are_rejected_explicitly(self):
  variants=[]
  for kind,payload in [('core',dict(core_px=10)),('parts',dict(targets=[dict(name='part',hp=10)])),('summon',dict(spec=dict(hp=10))),('move',dict(weapons=['AR'])),('buff',dict(enemy=dict(def_mult=2))),('debuff',dict(spec=dict(target='all',debuffs=[dict(stat='atk_pct',value=-10)])))]:
   c=copy.deepcopy(f.fixtures()[0]);c['patterns']=[dict(id='a',kind=kind,**payload)];variants.append(c)
  c=copy.deepcopy(f.fixtures()[0]);c['patterns'][0]['spec']['debuffs']=[dict(stat='atk_pct',value=-10)];variants.append(c)
  for case in variants:
   with self.subTest(case=case['patterns']),self.assertRaisesRegex(ValueError,'World payload is not connected'):f.compile_case(case)
 def test_candidate_layout_does_not_mutate_canonical_abi_or_limits(self):
  before=copy.deepcopy(LIMITS);words,_=f.compile_case(f.fixtures()[0]);self.assertEqual(LIMITS,before);self.assertEqual((ABI,LIMITS['INPUT_WORDS'],LIMITS['OUTPUT_WORDS']),(0x50455673,86016,159744));self.assertEqual((words[0],len(words)),(0x50455674,88848))
 def test_world_notices_keep_standard_trigger_admission_closed(self):
  from portable_runtime import validate_effect,UnsupportedPortable
  for timing in ('event:part_destroy','event:projectile_destroy','enemy_death'):
   eff=f.effect('def_pct',10,trigger=dict(timing=[timing],condition=[]))
   with self.subTest(timing=timing),self.assertRaises(UnsupportedPortable):validate_effect(eff)
   validate_effect(eff,world_frame=True)
 def test_world_notice_namespace_and_capacity_are_explicit(self):
  c=copy.deepcopy(f.fixtures()[0]);c['patterns'][0]['emit']=['event:target_spawn']*8
  words,meta=f.compile_case(c);self.assertEqual(words[f.WF_INPUT+8],meta['states']['target_spawn']+1)
  c['patterns'][0]['emit'].append('event:target_spawn')
  with self.assertRaisesRegex(ValueError,'World notice capacity exceeded'):f.compile_case(c)
 def test_world_entry_uses_identical_canonical_dependency_files(self):
  standard=source_hashes('gpu/event_runtime.slang');world=source_hashes('gpu/world_frame_entry.slang')
  self.assertEqual({k:v for k,v in world.items() if k!='gpu/world_frame_entry.slang'},standard)
  self.assertEqual([line for line in (ROOT/'gpu/world_frame_entry.slang').read_text().splitlines() if line.strip() and not line.startswith('//')],['#define PORTABLE_WORLD_FRAME','#include "event_runtime.slang"'])
if __name__=='__main__':unittest.main()
