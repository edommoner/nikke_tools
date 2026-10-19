"""Owned source admission/capacity and common transport address boundaries."""
import copy,importlib.util,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import validate_effect
from portable_specs import LIMITS as L
from portable_backend import execute
spec=importlib.util.spec_from_file_location('source_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
CASES=json.loads((ROOT/'tests/fixtures/portable-sources.json').read_text())['cases']
class SourceTests(unittest.TestCase):
    def source(self):return copy.deepcopy(CASES[0]['effects'][0])
    def case(self,effects):return dict(name='source packing',effects=effects,owners=[0]*len(effects),script=[[0,0,0,0,0,-1,0,0]],expected_queries=[])
    def test_explicit_lifetimes_not_cpu_populations_are_packed(self):
        c=CASES[0];before=copy.deepcopy(c);words,meta=v.compile_case(c);at=L['SOURCE_DEFINITION_BASE']
        self.assertEqual(c,before);self.assertEqual(words[at+1:at+4],[3,0,0]);self.assertEqual(struct.unpack('<3d',struct.pack('<6I',*words[at+8:at+14])),(.5,1,-1))
        self.assertEqual(meta['source_definitions'][0]['name'],'bird');self.assertEqual(words[at+14:at+72],[0]*58)
    def test_bad_forms_and_numeric_slots_fail_before_gpu(self):
        for value in ([],[True],[-2],[float('nan')],[86401],[-1]*33):
            e=self.source();e['periodic_source']['slots']=value
            with self.subTest(value=value),self.assertRaises(ValueError):validate_effect(e)
        for fields in (dict(fixed_value=1),dict(duration=1),dict(type='buff'),dict(target='all_allies'),dict(feather_slots=[-1])):
            e=self.source();e.update(fields)
            with self.subTest(fields=fields),self.assertRaises(ValueError):validate_effect(e)
    def test_64_unique_keys_and_256_refresh_variants_remain_distinct(self):
        effects=[self.source() for _ in range(65)]
        for i,e in enumerate(effects):e['name']='refresh';e['periodic_source']['name']='source'+str(i)
        v.compile_case(self.case(effects[:64]))
        with self.assertRaisesRegex(ValueError,'capacity'):v.compile_case(self.case(effects))
        effects=[self.source() for _ in range(256)]
        for i,e in enumerate(effects):e['name']='refresh';e['periodic_source']['slots']=[i]*32;e['periodic_source']['population_reduction_pct']=0
        words,_=v.compile_case(self.case(effects));at=L['SOURCE_DEFINITION_BASE']+255*72
        self.assertEqual(words[at+1],32);self.assertEqual(struct.unpack('<d',struct.pack('<2I',*words[at+70:at+72]))[0],255)
    def test_query_rejects_duplicate_indices_and_invalid_payload(self):
        for query in ([0,29,0,True,'bird',0,0,0],[0,29,0,5,'bird',0,0,0],[0,29,0,0,'',0,0,0],[0,29,0,0,'bird',64,0,0],[0,29,0,0,'bird',0,1,0]):
            c=self.case([self.source()]);c['script'].append(query)
            with self.subTest(query=query),self.assertRaises(ValueError):v.compile_case(c)
        c=self.case([self.source()]);c['script'] += [[0,29,0,0,'bird',0,0,0]]*2
        with self.assertRaises(ValueError):v.compile_case(c)
    def test_startup_precedes_first_periodic_phase_even_when_interval_underflows(self):
        from portable_source_oracle import observe
        c=next(c for c in CASES if c['name']=='source-first-frame-underflowed-interval')
        result=observe(c);self.assertEqual([q['attack_buffs'][0] for q in result['queries']],[1,2])
        self.assertEqual(result['periodic_sources'][0]['next_at'],0)
    def test_refresh_invalidates_same_time_native_scalar_cache(self):
        from portable_source_oracle import observe
        c=next(c for c in CASES if c['name']=='source-same-time-population-refresh')
        actual=observe(c)
        self.assertEqual([q['attack_buffs'][0] for q in actual['queries']],[30,10])
        self.assertEqual(actual['source_queries'][0]['count'],1)
    def test_transport_checks_word_strides_and_uint32_addresses_before_build(self):
        with patch('portable_backend.build') as build:
            for count,iw,ow in [(1,0,4),(1,4,True),(65536,131072,4),(65536,4,131072)]:
                with self.subTest(count=count,iw=iw,ow=ow),self.assertRaises(ValueError):execute('unused','unused',struct.pack('<I',count),iw,ow)
            build.assert_not_called()
        packed=struct.pack('<I',1)+bytes(L['INPUT_WORDS']*4)
        with patch('portable_backend.build',side_effect=RuntimeError('accepted layout')) as build:
            with self.assertRaisesRegex(RuntimeError,'accepted layout'):execute('unused','unused',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'])
            build.assert_called_once()
if __name__=='__main__':unittest.main()
