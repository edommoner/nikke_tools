"""Live core descriptors, actual native geometry and strict complete-wire guards."""
import importlib.util,sys,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('coordinate_core_adapter',ROOT/'research/verify-coordinate-core-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_coordinate_core_specs import INPUT_WORDS,OUTPUT_WORDS,BASE_INPUT,HEADER,check_schema

class CoreTests(unittest.TestCase):
    def test_packing_keeps_authored_prefix_and_never_runs_native_or_probability(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle during packing')),patch('coordinate_landing_reference.landing',side_effect=AssertionError('No probability IR')):rows,raw=a.prepare()
        self.assertEqual(len(rows),120);self.assertEqual(sum(d is not None for _,_,d in rows),106)
        self.assertEqual(len(raw),4+120*INPUT_WORDS*4)
        old,_=a.parent.prepare()
        for actual,prior in zip(rows,old):self.assertEqual(actual[0],prior[0]);self.assertEqual(actual[1][:BASE_INPUT],prior[1]);self.assertEqual(actual[2],prior[2])
        import array,hashlib
        prior=json.loads((ROOT/'research/portable-coordinate-accum-emission-short-expected.json').read_text())
        for (name,words,_),gold in zip(rows,prior['entries']):
            raw_prefix=array.array('I',words[:BASE_INPUT])
            if sys.byteorder!='little':raw_prefix.byteswap()
            self.assertEqual(name,gold['name']);self.assertEqual(hashlib.sha256(raw_prefix.tobytes()).hexdigest(),gold['input_sha256'])
        self.assertTrue(all(len(w)==INPUT_WORDS for _,w,_ in rows))

    def test_real_largest_and_newest_live_core_and_default_aim(self):
        cases={c['name'].split('/')[-1]:c for c in a.fixtures()}
        def observe(name):return a.native_reference((cases[name],None,None,None))
        values={name:observe(name) for name in ['off-center-explicit','off-center-default-auto','largest-wins','equal-newest-start','equal-declaration-order','older-declaration-newest-start','winner-expires-restores-core','base-equal-node','base-larger-than-node','expiry','delayed-open','part-occlusion','pierce-under-part','core-fraction-child']}
        aims=lambda name:[r['aim'] for r in values[name]['physical_pellets']]
        self.assertEqual(aims('off-center-explicit'),[[0.,0.]]*3)
        self.assertEqual(aims('off-center-default-auto'),[[3.,-1.]]*3)
        self.assertEqual(aims('largest-wins'),[[4.,0.]]*3)
        self.assertEqual(aims('equal-newest-start'),[[4.,0.],[-5.,2.],[-5.,2.]])
        self.assertEqual(aims('equal-declaration-order'),[[-5.,2.]]*3)
        self.assertEqual(aims('older-declaration-newest-start'),[[-5.,2.],[4.,0.],[4.,0.]])
        self.assertEqual(aims('winner-expires-restores-core'),[[4.,0.],[-5.,2.],[-5.,2.]])
        self.assertEqual(aims('base-equal-node'),[[4.,0.]]*3)
        self.assertEqual(aims('base-larger-than-node'),[[0.,0.]]*3)
        self.assertEqual(aims('delayed-open'),[[0.,0.],[7.,0.],[7.,0.]])
        self.assertTrue(all(r['core_fraction']==0 for r in values['part-occlusion']['physical_pellets']))
        self.assertTrue(all(r['core_fraction']>0 for r in values['pierce-under-part']['physical_pellets']))
        self.assertEqual([r['core_fraction'] for r in values['expiry']['physical_pellets']][1:],[0.,0.])
        # Fraction notices are actual canonical counter callbacks; full battle
        # comparison, rather than an invented GPU-only diagnostic, checks them.
        first=values['core-fraction-child'];self.assertGreater(first['physical_pellets'][-1]['packets'][0]['damage'],first['physical_pellets'][0]['packets'][0]['damage'])

    def test_scene_core_is_explicit_and_target_capacity_is_unchanged(self):
        from portable_coordinate_scene_specs import compile_scene
        case=next(c for c in a.fixtures() if c['name'].endswith('/127-targets'))
        with self.assertRaises(ValueError):compile_scene(dict(patterns=case['patterns'],commands=[('capture',case['duration'],0,0)]))
        w,_,_,d=a.compile_case(case);self.assertEqual(len(d['rows']),127)
        case=next(c for c in a.fixtures() if c['name'].endswith('/32-nodes'))
        w,_,_,d=a.compile_case(case);self.assertEqual(len(d['patterns']),32)
        self.assertEqual(w[BASE_INPUT+2],32)

    def test_weapon_metadata_disagreement_stops_before_compiling_and_area_trace_is_real(self):
        import copy
        from world_frame_native import authored_metadata,roster_names
        cases={c['name'].split('/')[-1]:c for c in a.fixtures()}
        case=cases['explosion-under-part'];name=roster_names(case)[0]
        self.assertEqual(case['combat']['weapons'][0]['base_weapon_type'],'RL')
        self.assertEqual(authored_metadata(case)[name]['weapon_type'],'RL')
        self.assertEqual(case['post_fire_delays'][0],.215)
        bad=copy.deepcopy(cases['centered-core']);bad['weapon_metadata']['weapon_type']='RL'
        with self.assertRaisesRegex(ValueError,'metadata and static combat type disagree'):a.compile_case(bad)
        case=cases['area-skill-default-core-aim'];v=a.native_reference((case,None,None,None))
        self.assertEqual([r['amount'] for r in v['skill_trace']],[2000,3000])
        self.assertTrue(any(p['skill_name']=='core-area-skill' and p['target']=='behind' for p in v['landed_packets']))

    def test_backend_rejects_other_stride_and_entry_names(self):
        from portable_backend import validate_composed_stride
        check_schema(ROOT);validate_composed_stride(a.SOURCE,INPUT_WORDS,OUTPUT_WORDS)
        for source,words in [(a.SOURCE,INPUT_WORDS-1),('gpu/world_coordinate_physical_entry.slang',INPUT_WORDS),('gpu/unknown_core.slang',INPUT_WORDS)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,words,OUTPUT_WORDS)

    def test_source_inverse_and_transport_refuse_every_unreviewed_edit(self):
        from portable_coordinate_core_source_contract import project_sources,project_backend_source
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-core-source-delta.json').read_text());projected=project_sources(ROOT)
        for name,row in data['sources'].items():self.assertEqual(projected[name],row['baseline'])
        for name in [*data['sources'],*data['added_sources']]:
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        self.assertEqual(project_backend_source(ROOT),data['transport']['baseline'])
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/data['transport']['path']).read_text()+'\n// unreviewed\n')

if __name__=='__main__':unittest.main()
