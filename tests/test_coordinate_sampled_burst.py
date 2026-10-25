"""Both real native deferred queues keep capacity, order and numeric context."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampled_burst_cases import fixtures
from world_coordinate_sampled_burst_native import observe
from portable_coordinate_sampled_burst_contracts import verify
spec=importlib.util.spec_from_file_location('sampled_burst_tests',ROOT/'research/verify-coordinate-sampled-burst-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class BurstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers={c['name'].rsplit('/',1)[1]:observe(c)[0] for c in cls.cases}
    def test_real_contracts_and_immutable_inputs(self):
        self.assertEqual(len(self.cases),24);self.assertEqual(self.cases,self.before)
        for c in self.cases:self.assertTrue(verify(c,self.answers[c['name'].rsplit('/',1)[1]])['verified'])
    def test_no_wrapper_double_count_and_all_births_batched_once(self):
        for n in self.answers.values():self.assertEqual(len(n['sampled_burst_batches']),1)
        self.assertEqual(len(self.answers['legacy-duplicate']['sampled_burst_batches'][0]['entries']),2)
        self.assertEqual([r['index'] for r in self.answers['legacy-duplicate']['sampled_legacy_damage']],[0,1])
    def test_legacy_each_hit_draws_and_zero_coefficients_skip(self):
        self.assertEqual([r['hit'] for r in self.answers['legacy-three']['sampled_legacy_damage']],[1,2,3])
        for key in ('legacy-zero','legacy-missing-reference'):self.assertFalse(self.answers[key]['sampled_legacy_damage'])
        self.assertFalse(self.answers['legacy-zero-rate']['sampled_legacy_damage'][0]['critical']);self.assertTrue(self.answers['legacy-unit-rate']['sampled_legacy_damage'][0]['critical'])
    def test_earlier_and_entry_buffs_apply_later_cast_buff_is_excluded(self):
        self.assertEqual(self.answers['legacy-earlier-buff']['sampled_legacy_damage'][0]['atk_pct'],100)
        self.assertEqual(self.answers['legacy-entry-buff']['sampled_legacy_damage'][0]['atk_pct'],100)
        self.assertEqual(self.answers['legacy-later-buff']['sampled_legacy_damage'][0]['atk_pct'],0)
        resolved=[r for r in self.answers['optin-later-buff']['full_burst_landing_observation']['calls'] if r['resolved']]
        self.assertEqual(resolved[0]['excluded'],['later']);self.assertTrue(resolved[0]['full'])
    def test_optin_count_latched_even_when_reference_changes(self):
        n=self.answers['optin-latched-reference'];resolved=[r for r in n['full_burst_landing_observation']['calls'] if r['resolved']]
        self.assertEqual(resolved[0]['latched'],1);self.assertEqual(len([r for r in n['sampled_skill_damage'] if not r['target']]),1)
        self.assertFalse(self.answers['optin-zero-hits']['sampled_skill_damage'])
    def test_ordinary_prefix_then_legacy_and_legacy_before_optin(self):
        order=self.answers['legacy-ordinary-prefix']['sampled_burst_calculation_order'];self.assertEqual([r['name'] for r in order],['ordinary-prefix','parts-source'])
        n=self.answers['mixed-queues'];self.assertEqual([r['queue'] for r in n['sampled_burst_calculation_order']],['legacy','ordinary','ordinary','ordinary'])
        self.assertEqual(n['sampled_legacy_damage'][0]['index'],1)
    def test_full_pending_capacity_and_registered_consumers(self):
        from portable_coordinate_sampled_burst_wire import check_schema,ENTRIES,HITS,BASE,WORDS,OUTPUT_WORDS,INPUT_WORDS,SOURCE
        from portable_backend import validate_composed_stride
        self.assertEqual((ENTRIES,HITS),(512,256));self.assertEqual(BASE+((ENTRIES-1)*HITS+HITS-1)*2+2,OUTPUT_WORDS);self.assertEqual(WORDS*4,1048576)
        self.assertEqual(check_schema(ROOT)['additional_runtime_bytes'],0);validate_composed_stride(SOURCE,INPUT_WORDS,OUTPUT_WORDS)
        for source,i,o in [('gpu/world_coordinate_sampling_skill_entry.slang',INPUT_WORDS,OUTPUT_WORDS),(SOURCE,INPUT_WORDS,1507328),(SOURCE,INPUT_WORDS-1,OUTPUT_WORDS)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,i,o)
    def test_old62_inputs_domains_and_names_unchanged(self):
        rows,data=a.prepare();old,_=a.parent.prepare();self.assertEqual(rows[:62],old)
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(89,83));self.assertEqual(len(data),4+89*a.INPUT_WORDS*4)
    def test_source_inverse_rejects_unknown_shader_and_consumer(self):
        from portable_coordinate_sampled_burst_source_contract import project_sources,project_backend_source
        from portable_coordinate_sampled_vital_source_contract import project_sources as vital_sources,project_backend_source as vital_backend
        project_sources(ROOT,vital_sources(ROOT));project_backend_source(ROOT,vital_backend(ROOT))
        for name in ('gpu/portable_schema.slang','gpu/pending_burst_runtime.slang','gpu/coordinate_sampled_burst_runtime.slang','scripts/run-metal-probe.swift'):
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// changed\n'})
    def test_persistent_header_is_explicitly_separate_from_shot_scratch(self):
        from portable_sampled_damage_totals import exact_damage,BASE as TOTAL,MAGIC
        from portable_coordinate_sampled_burst_wire import HEAD,ENTRIES
        from portable_coordinate_physical_specs import LAYOUT as CF
        from portable_coordinate_sampling_bank import LAYOUT as BANK
        self.assertGreaterEqual(HEAD,BANK['RNG']+BANK['RNG_WORDS']);self.assertLess(HEAD,CF['END'])
        block=[0]*CF['END'];block[TOTAL:TOTAL+4]=[MAGIC,1,5,0];block[HEAD]=1
        with self.assertRaises(AssertionError):exact_damage(block,[0]*5,[],{})
        self.assertEqual(exact_damage(block,[0]*5,[],{},sampled_burst=True),[0]*5)
        for at,value in [(HEAD,ENTRIES+1),(HEAD+4,1)]:
            before=block[at];block[at]=value
            with self.assertRaises(AssertionError):exact_damage(block,[0]*5,[],{},sampled_burst=True)
            block[at]=before
    def test_optin_named_critical_context_is_explicit_but_legacy_emits_none(self):
        from portable_specs import LIMITS as L,FIELDS as F
        from world_enemy_attack_cases import field
        c=next(c for c in self.cases if c['name'].endswith('/optin-named-child'));words,m,_,_=a.compile_case(c)
        source=next(i for i,e in enumerate(c['effects']) if e.get('land_in_full_burst'));row=m['binding_source_indices'].index(source)
        self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']+row*8+6],2);self.assertTrue(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']]&131072)
        c=copy.deepcopy(self.cases[0]);c['effects'].append(field('atk_pct',10,'self','witness','hit_count:parts-source:1',condition=['trigger_hit_crit']));c['owners'].append(0)
        words,m,_,_=a.compile_case(c);source=next(i for i,e in enumerate(c['effects']) if e.get('type')=='damage');row=m['binding_source_indices'].index(source)
        self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']+row*8+6],1);self.assertFalse(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']]&131072)
    def test_later_buff_exclusion_mask_and_reference_marker_are_preserved(self):
        from portable_specs import LIMITS as L,FIELDS as F
        c=next(c for c in self.cases if c['name'].endswith('/legacy-later-buff'));w,m,_,_=a.compile_case(c)
        source=next(i for i,e in enumerate(c['effects']) if e.get('type')=='damage');later=next(i for i,e in enumerate(c['effects']) if e['name']=='later');row=m['binding_source_indices'].index(source);target=m['binding_source_indices'].index(later)
        self.assertTrue(w[L['PENDING_EXCLUDE_BASE']+row*L['MASK_WORDS']+target//32]&(1<<(target%32)))
        c=next(c for c in self.cases if c['name'].endswith('/optin-latched-reference'));w,m,_,_=a.compile_case(c);source=next(i for i,e in enumerate(c['effects']) if e['name']=='cast-count');row=m['binding_source_indices'].index(source)
        self.assertEqual(w[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']],4)
if __name__=='__main__':unittest.main()
