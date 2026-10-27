"""Real original inputs and reused diagnostic banks; no fake effect witnesses."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('original_health_parts_test',ROOT/'research/verify-original-lock-health-parts.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
from portable_heavyarms_original_composition import prepare_case
class HealthParts(unittest.TestCase):
    def test_original_effects_and_growth_survive_real_world_and_formation_changes(self):
        from calculator import timeline
        from portable_heavyarms_lock_cases import source_definitions
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle allowed during static packing')):
            base,plain=prepare_case(3,0)
            c,prepared=prepare_case(3,3,parts=True,injury=True,mary_first=True,mary_low=True)
            before=copy.deepcopy(c);w,meta,bindings=suite.compile_case(c)
        self.assertEqual(c,before);self.assertEqual(c['effects'][:25],source_definitions());self.assertEqual(len(c['effects']),91)
        rows=lambda p:Counter((json.dumps(x['effect'],sort_keys=True),x['owner']) for x in p['effects'])
        self.assertEqual(rows(prepared),rows(plain));self.assertEqual(c['original_run']['body']['profile'],base['original_run']['body']['profile'])
        self.assertEqual(prepared['policies']['config'],plain['policies']['config'])
        self.assertEqual(set(meta['binding_source_indices']),set(range(91)));self.assertEqual(len(w),109536)
        self.assertEqual(c['names'][1],'메어리');self.assertEqual(c['names'][0],base['names'][0])
        self.assertEqual(sum(int(b.kind)==1 for b in bindings),2)
        self.assertEqual(next(p for p in c['patterns'] if p['id']=='lock-wave')['delay'],3.)
        self.assertFalse(c['enemy']['has_parts']) # Presence must come from live nodes.
    def test_existing_original_input_and_native_baseline_remain_exact(self):
        c,_=prepare_case(3,0);w,meta,bindings=suite.compile_case(c)
        baseline=json.loads((ROOT/'research/portable-original-lock-composition-v1-expected.json').read_text())['entries'][0]
        packed=array.array('I',w)
        if sys.byteorder!='little':packed.byteswap()
        self.assertEqual(hashlib.sha256(packed.tobytes()).hexdigest(),baseline['input_sha256'])
        self.assertEqual(suite.cross.digest(suite.parent.native_reference((c,meta,bindings))),baseline['native_sha256'])
    def test_scenario_literals_reject_ambiguous_combinations_before_preparation(self):
        for kwargs in (dict(parts=1),dict(injury='yes'),dict(break_parts=True),dict(mary_low=True),dict(mary_low=True,injury=True)):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):prepare_case(3,0,**kwargs)
    def test_existing_healing_trace_fits_the_unchanged_composed_wire(self):
        from portable_heal_share_trace import BASE,COUNT,WORDS
        from portable_parts_skill_specs import BASE as parts
        self.assertLessEqual(BASE+8+COUNT*WORDS,parts)
        self.assertEqual(suite.suite.INPUT,109536);self.assertEqual(suite.suite.OUTPUT,1310720)
        self.assertEqual((ROOT/suite.SOURCE).read_text(),'// Reuse the existing healing diagnostic and the same complete shared executor.\n#define PORTABLE_HEAL_SHARE_DIAGNOSTIC\n#include "world_original_lock_composition_entry.slang"\n')
    def test_exact_source_inverse_retains_legacy_backend_and_refuses_unreviewed_changes(self):
        from portable_original_health_parts_source_contract import project_sources
        d=json.loads((ROOT/'tests/fixtures/portable-original-health-parts-source-delta.json').read_text());out=project_sources(ROOT)
        self.assertEqual(out['app/portable_backend.py'],d['sources']['app/portable_backend.py']['baseline'])
        with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{'app/portable_backend.py':d['sources']['app/portable_backend.py']['current']+'\n# mutation'})
        from portable_original_lock_source_contract import project_sources as complete
        previous=json.loads((ROOT/'tests/fixtures/portable-original-lock-source-delta.json').read_text())
        self.assertEqual(complete(ROOT)['app/portable_backend.py'],previous['sources']['app/portable_backend.py']['baseline'])
    def test_shared_cache_profile_requires_the_same_calculation_and_paired_generation(self):
        import nikke_gpu as cli
        normal=cli.SUITES['original-lock-health-parts'];cached=cli.SUITES['original-lock-health-parts-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words','development_only'):self.assertEqual(normal[key],cached[key])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1');self.assertIs(cached['require_paired_generation'],True)
if __name__=='__main__':unittest.main()
