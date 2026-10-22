"""Host identity lowering and exact shared hook source guards."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_pellet_shot_cases import fixtures
from portable_pellet_shot_specs import parse,bindings,compiler_effect
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L
from portable_definition_view_contract import verify


class PelletShotTests(unittest.TestCase):
    def adapter(self):
        spec=importlib.util.spec_from_file_location('pellet_shot_tests',ROOT/'research/verify-world-pellet-shot-short.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def test_signed_domain_and_raw_spelling(self):
        for raw,value in [('5',5),('05',5),('+5',5),(' 5',5),('５',5),('-2147483648',-2147483648),('2147483647',2147483647),('-0',0),('1_0',10)]:
            self.assertEqual(parse('pellet_hit_in_shot:'+raw),(value,raw))
        self.assertIsNone(parse('pellet_hit_count:5'))
        effect=fixtures()[0]['effects'][1]
        for raw in ('','5.0','nan','inf','2147483648','-2147483649','5:1'):
            changed=copy.deepcopy(effect);changed['trigger']['timing']=['pellet_hit_in_shot:'+raw]
            with self.subTest(raw=raw),self.assertRaises(UnsupportedPortable) as caught:validate_effect(changed,combat={})
            self.assertEqual(caught.exception.reason,'trigger');self.assertEqual(caught.exception.operator,dict(domain='timing',descriptor='pellet_hit_in_shot:'+raw))
        with self.assertRaises(UnsupportedPortable):validate_effect(effect)

    def test_compiler_surrogate_is_static_and_signed_value_is_restored(self):
        m=self.adapter()
        for label,expected in [('zero',0),('negative',-1),('signed-minimum',-2147483648),('large',2147483647)]:
            case=next(c for c in fixtures() if c['name']=='pellet-shot-'+label);before=copy.deepcopy(case)
            lowered=compiler_effect(case['effects'][1]);self.assertEqual(parse(lowered['trigger']['timing'][0])[0],max(1,expected))
            words,_,_=m.suite.compile_case(case);at=L['EVENT_BASE']+L['EVENT_WORDS']
            value=struct.unpack('<d',struct.pack('<II',*words[at+1:at+3]))[0]
            self.assertEqual(value,expected);self.assertEqual(words[at+3:at+8],[0,1,0,0,0]);self.assertEqual(case,before)

    def test_aliases_sorted_by_value_then_literal_and_duplicates_share_ids(self):
        m=self.adapter();case=next(c for c in fixtures() if c['name'].endswith('raw-aliases'))
        expected={' 5':1,'+5':2,'05':3,'5':4,'５':5}
        self.assertEqual(bindings([(case['effects'][1],'owner')],['owner'])['owner'],expected)
        words,_,_=m.suite.compile_case(case);at=L['EVENT_BASE']+L['EVENT_WORDS']
        self.assertEqual([words[at+8*i+4] for i in range(5)],[4,3,2,1,5])
        case=next(c for c in fixtures() if c['name'].endswith('duplicate-descriptor'));words,_,_=m.suite.compile_case(case)
        self.assertEqual([words[at+4],words[at+12]],[1,1])
        before=copy.deepcopy(fixtures());entries,packed=m.prepare()
        self.assertEqual(len(entries),36);self.assertEqual(sum(e[2] is not None for e in entries),21)
        self.assertEqual(len(packed),4+36*m.suite.INPUT*4);self.assertEqual(fixtures(),before)

    def test_reviewed_hooks_reject_removed_reordered_broadened_or_numeric_changes(self):
        from portable_pellet_shot_source_contract import ledger
        data=ledger(ROOT);self.assertEqual(set(verify(ROOT)['reviewed_pellet_shot_sources']),set(data['sources'])|set(data['new_sources']))
        for name,row in data['sources'].items():
            source=(ROOT/name).read_text()
            for mutated in (source+'\n// unreviewed\n',source.replace(row['changes'][0]['current'],row['changes'][0]['baseline'],1)):
                with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:mutated})
        name='gpu/pellet_shot_runtime.slang';source=(ROOT/name).read_text()
        for old,new in [('tag==0','false'),('od.owner!=d.owner','false'),('f64Less(threshold,value)','false'),('f64FromI64(count)','f64FromI64(count+1)'),('next=tag','next=tag+1')]:
            self.assertIn(old,source)
            with self.subTest(old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})


if __name__=='__main__':unittest.main()
