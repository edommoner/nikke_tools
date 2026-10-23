"""Private shared value-source tag and exact source proof containment."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime
from portable_max_ammo_scaling_cases import fixtures
from portable_specs import LIMITS as L,FIELDS as F
from portable_max_ammo_scaling_specs import FLAG,MAX_AMMO_SCALE
def adapter():
    s=importlib.util.spec_from_file_location('ammo_scaling_test_adapter',ROOT/'research/verify-world-max-ammo-scaling-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class MaxAmmoScalingTests(unittest.TestCase):
    def test_shared_table_positive_cases_and_single_word_refusals(self):
        m=adapter();rows,packed=m.prepare();self.assertEqual((len(rows),sum(d is not None for _,w,d in rows)),(28,20))
        seed=rows[0][1]
        for name,w,d in rows[20:]:self.assertEqual(sum(a!=b for a,b in zip(seed,w)),1)
        for name,w,d in rows[:20]:
            c,metadata,body=d
            for i,e in enumerate(c['effects']):self.assertEqual(bool(w[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['FLAGS']]&FLAG),e.get('scaling')=='max_ammo_count')
    def test_host_rejects_incompatible_interpretations(self):
        c=fixtures()[0];eff=c['effects'][1]
        for delta in [dict(type='damage'),dict(stat='max_ammo_pct'),dict(stat='atk_pct'),dict(scaling_ref='other'),dict(tick_interval=.1)]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):portable_runtime.validate_effect(dict(eff,**delta),combat=c['combat'],world_frame=True)
    def test_canonical_quantity_is_retained_and_not_a_named_reference(self):
        m=adapter();c=fixtures()[0];w,meta,body=m.suite.compile_case(c)
        self.assertEqual(MAX_AMMO_SCALE,-4)
        at=L['REFERENCE_DEFINITION_BASE']+4
        self.assertEqual(w[at:at+4],[0]*4)
        self.assertTrue(w[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['FLAGS']]&FLAG)
        self.assertEqual(c,fixtures()[0])
    def test_source_inverse_is_exact_and_rejects_faults(self):
        from portable_max_ammo_scaling_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-max-ammo-scaling-source-delta.json').read_text());projected=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(projected[name],row['baseline'])
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
        for name in data['added_sources']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
    def test_capacity_dependency_never_publishes_or_recurses_numeric_dictionary(self):
        source=(ROOT/'gpu/max_ammo_scaling_runtime.slang').read_text()
        # Inspect calls rather than comments; a changed graph needs explicit review.
        import re
        calls=re.findall(r'\b(\w+)\s*\(',re.sub(r'//[^\n]*','',source))
        self.assertNotIn('collectStats',calls);self.assertNotIn('ensureNativeNumeric',calls);self.assertNotIn('storeNativeNumeric',calls)
        self.assertIn('rawScaledFullCapacity',calls);self.assertIn('referencedModeCapacity',calls)
        quantities=(ROOT/'gpu/quantity_runtime.slang').read_text()
        inner=quantities.split('uint rawScaledFullCapacity',1)[1].split('#endif',1)[0]
        self.assertIn('liveQuantity(',inner);self.assertNotIn('plainQuantity(',inner)
        self.assertEqual(quantities.count('return capacityFromParts('),2)
if __name__=='__main__':unittest.main()
