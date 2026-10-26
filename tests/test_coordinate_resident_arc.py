"""Full resident wire ownership, exact source inverse and complete comparisons."""
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_resident_arc_specs as arc
import portable_coordinate_arc_arena as common
import portable_backend
s=importlib.util.spec_from_file_location('resident_arc_test',ROOT/'research/verify-coordinate-resident-arc-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ResidentArcTests(unittest.TestCase):
 def test_all_previous_banks_remain_and_tail_has_full_capacity(self):
  plan=arc.check_layout(ROOT);self.assertTrue(plan['address_plan_verified'])
  from portable_coordinate_typed_aim_specs import regions
  prior,iw,ow=regions();current,niw,now=arc.regions()
  self.assertEqual(current[:len(prior)],prior);self.assertEqual(iw,niw)
  self.assertEqual((ow,now),(2032000,2064786));self.assertEqual(current[len(prior)].base,ow)
  self.assertEqual(sum(r.words for r in current[len(prior):]),32786)
 def test_canonical_resident_body_only_changes_read_address_and_view_offset(self):
  common.check(ROOT)
  gpu=ROOT/'gpu';old=(gpu/'coordinate_landing_arena_ops.slang').read_text()
  expected=old.replace('arcArenaView(output,CL_OUTPUT,','arcArenaView(output,CRA_SCRATCH_OFFSET,').replace('commands[','results[')
  self.assertEqual((gpu/'coordinate_landing_resident_arena_ops.slang').read_text(),expected)
 def test_only_new_entry_accepts_new_complete_stride(self):
  portable_backend.validate_composed_stride(arc.SOURCE,arc.INPUT_WORDS,arc.OUTPUT_WORDS)
  for source,iw,ow in [(arc.SOURCE,arc.INPUT_WORDS,2032000),(arc.SOURCE,arc.INPUT_WORDS-1,arc.OUTPUT_WORDS),('gpu/world_coordinate_typed_logical_owner_entry.slang',arc.INPUT_WORDS,arc.OUTPUT_WORDS)]:
   with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):portable_backend.validate_composed_stride(source,iw,ow)
 def test_whole_tail_is_checked_before_canonical_comparison(self):
  words=[0]*arc.OUTPUT_WORDS
  self.assertEqual(len(a.logical(words)),arc.PREFIX_WORDS)
  for offset in [arc.PREFIX_WORDS,arc.OUTPUT_WORDS-1]:
   words[offset]=1
   with self.assertRaisesRegex(AssertionError,'scratch leaked'):a.logical(words)
   words[offset]=0
  with self.assertRaisesRegex(AssertionError,'Complete'):a.logical(words[:-1])
 def test_exact_source_inverse_preserves_previous_snapshot(self):
  from portable_coordinate_resident_arc_source_contract import ledger,project_sources,project_backend_source
  data=ledger(ROOT);old=project_sources(ROOT)
  for name,row in data['sources'].items():
   if name.endswith('.slang'):
    self.assertEqual(old[name],row['baseline'])
    with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n// unreviewed'})
  self.assertEqual(project_backend_source(ROOT),data['sources']['app/portable_backend.py']['baseline'])
  with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n# unreviewed')
 def test_root_clears_tail_even_when_shared_execution_returns_early(self):
  text=(ROOT/'gpu/world_coordinate_area_entry.slang').read_text();needle='for(uint i=0;i<CRA_WORDS;i++)results[arcBase+i]=0;'
  self.assertEqual(text.count(needle),2)
  before,after=text.split('executeComposedCoordinateEvents(runtimeStates[id.x],id);')
  self.assertIn(needle,before);self.assertIn(needle,after)

if __name__=='__main__':unittest.main()
