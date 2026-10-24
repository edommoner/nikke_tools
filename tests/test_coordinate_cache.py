"""Real cache lifetimes, collision witnesses and every saved table/value field."""
import importlib.util,sys,json,unittest,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('geometry_cache_adapter',ROOT/'research/verify-coordinate-cache-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_coordinate_cache_specs import LAYOUT as G,capacity,check_schema

class CacheTests(unittest.TestCase):
    def observe(self,case):
        _,meta,bindings,descriptors=a.compile_case(case)
        return a.native_reference((case,meta,bindings,descriptors))
    def test_packing_contains_no_cache_result_or_native_schedule(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle packing')),patch('coordinate_landing_reference.landing',side_effect=AssertionError('No probability packing')):rows,raw=a.prepare()
        self.assertEqual(len(rows),133);self.assertEqual(sum(d is not None for _,_,d in rows),118)
        self.assertEqual(len(raw),4+133*a.INPUT_WORDS*4)
        old,_=a.parent.prepare();self.assertEqual(rows[:120],old)
        check_schema(ROOT);self.assertEqual(capacity(0),4096);self.assertEqual(capacity(127),231)
    def test_real_rounded_collisions_reuse_first_values_across_shooters_and_grow_branch(self):
        cases={c['name'].split('/')[-1]:c for c in a.fixtures()}
        def observe(label):return self.observe(cases[label])
        for label in ['cache-radius-collision','cache-cross-owner-first-value','cache-zero-to-positive-grow']:
            g=observe(label)['geometry_cache'];collisions=[]
            for q in g['queries']:
                first=next(p for p in g['queries'] if p['geometry']==q['geometry'] and p['key']==q['key'])
                if q['hit'] and q['request_bits']!=first['request_bits']:
                    collisions.append(q);self.assertEqual(q['value'],first['value'])
            self.assertTrue(collisions,label)
        value=observe('cache-zero-to-positive-grow')
        self.assertEqual([len(p['packets']) for p in value['physical_pellets']],[2,1,1,1,1])
    def test_geometry_identity_not_graph_generation_controls_lifetime(self):
        cases={c['name'].split('/')[-1]:c for c in a.fixtures()}
        values={name:self.observe(c)['geometry_cache'] for name,c in cases.items()}
        self.assertEqual(values['cache-equal-core-no-new-geometry']['geometries'],1)
        self.assertEqual(values['cache-same-target-new-generation']['geometries'],1)
        self.assertGreater(values['cache-core-motion-same-rounded-key']['geometries'],1)
        self.assertGreater(values['cache-same-target-set-new-order']['geometries'],1)
        self.assertGreater(values['cache-cache-empty-geometry-gap']['geometries'],len(values['cache-cache-empty-geometry-gap']['queries']))
    def test_true_127_target_capacity_is_exceeded_without_eviction_or_reducing_queries(self):
        c=a.overflow_case();_,m,b,d=a.compile_case(c);v=a.native_reference((c,m,b,d))
        self.assertEqual(v['geometry_cache']['final_target_count'],127)
        self.assertGreater(len(v['geometry_cache']['final_entries']),capacity(127))
    def test_literal_spread_mismatch_is_rejected_before_gpu(self):
        case=copy.deepcopy(a.fixtures()[0]);case['literal_weapon_geometry'][0]['spread_end']=8.
        with self.assertRaisesRegex(ValueError,'literal spread disagrees'):a.compile_case(case)
        case=copy.deepcopy(a.fixtures()[0]);target=copy.deepcopy(case['patterns'][0]['targets'][0])
        case['patterns'].append(dict(id='duplicate-label-node',kind='parts',targets=[target]))
        with self.assertRaisesRegex(ValueError,'Duplicate native actor labels'):a.compile_case(case)
        case=copy.deepcopy(a.fixtures()[0]);target=copy.deepcopy(case['patterns'][0]['targets'][0]);case['patterns'].append(dict(id='cross-kind-label',kind='interrupt',targets=[target]))
        with self.assertRaises(ValueError):a.compile_case(case)

    def test_passive_observer_restores_hooks_on_native_failure(self):
        from calculator.boss_pattern import Geometry
        before=(Geometry.__init__,Geometry.landing)
        with patch.object(a.parent,'native_reference',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):a.native_reference((a.fixtures()[0],None,None,None))
        self.assertEqual(before,(Geometry.__init__,Geometry.landing))
    def test_full_cache_decoder_rejects_hash_alias_wrong_values_and_unused_tail(self):
        # One native-derived0-target cache entry; all real battle/packet checks
        # remain in the parent's comparator, independently of this decoder test.
        c=next(c for c in a.fixtures() if 'equal-core-no-new' in c['name']);v=self.observe(c);obs=v['geometry_cache'];n=obs['final_target_count'];self.assertEqual(n,0)
        block=[0]*a.OUTPUT_WORDS;h=G['BASE'];count=len(obs['final_entries']);stride=12
        block[h:h+15]=[G['MAGIC'],1,1,n,stride,count,capacity(n),obs['geometries'],obs['hits'],obs['misses'],obs['geometries'],0,obs['peak_entries'],0,0]
        sig=G['SIG'];block[sig]=n
        for i,value in enumerate(obs['final_geometry']['core_bits']+obs['final_geometry']['auto_bits']):block[sig+4+i*2:sig+6+i*2]=[value&0xffffffff,value>>32]
        block[sig+16:sig+16+n]=obs['final_slots']
        for i,entry in enumerate(obs['final_entries']):
            at=G['DATA']+i*stride;words=[]
            for x in entry['key']+entry['value']:words.extend([x&0xffffffff,x>>32])
            block[at:at+stride]=words;hashed=2166136261
            for x in entry['key']:hashed=((hashed^(x&0xffffffff))*16777619)&0xffffffff;hashed=((hashed^(x>>32))*16777619)&0xffffffff
            bucket=hashed&(G['SLOTS']-1)
            while block[G['TABLE']+bucket]:bucket=(bucket+1)&(G['SLOTS']-1)
            block[G['TABLE']+bucket]=i+1
        a.compare_cache(block,obs)
        for at in [h+9,G['SIG']+10,G['TABLE'],G['DATA']+8,G['DATA']+count*stride]:
            changed=list(block);changed[at]^=1
            with self.assertRaises(AssertionError):a.compare_cache(changed,obs)
    def test_exact_source_inverse_and_transport_guards(self):
        from portable_coordinate_cache_source_contract import project_sources,project_backend_source
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-cache-source-delta.json').read_text());project_sources(ROOT);project_backend_source(ROOT)
        for name in [*data['sources'],*data['added_sources']]:
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n// unreviewed\n')
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
