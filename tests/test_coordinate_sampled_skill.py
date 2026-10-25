"""Real random skill contracts: per-hit RNG, snapshot lifetime and children."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampled_skill_cases import fixtures
from world_coordinate_sampled_skill_native import observe
spec=importlib.util.spec_from_file_location('sampled_skill_adapter',ROOT/'research/verify-coordinate-sampled-skill-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class SkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers={c['name'].rsplit('/',1)[1]:observe(c)[0] for c in cls.cases}
    def test_immutable_actual_native_contracts(self):
        self.assertEqual(len(self.cases),22);self.assertEqual(self.cases,self.before)
        for key,n in self.answers.items():self.assertTrue(n['physical_pellets']);self.assertTrue(n['landed_packets'])
    def test_each_body_draws_once_and_parts_reuse_without_draws(self):
        for n in self.answers.values():
            bodies=[r for r in n['sampled_skill_damage'] if not r['target']]
            uniforms=[r for r in n['sampled_draws'] if r['kind']=='native-uniform']
            self.assertEqual(len(uniforms),len(n['physical_pellets'])+len(bodies))
            parent=None
            for row in n['sampled_skill_damage']:
                if not row['target']:parent=row
                else:self.assertEqual((row['critical'],row['name'],row['time'],row['owner']),(parent['critical'],parent['name'],parent['time'],parent['owner']))
        self.assertTrue(any(r['target'] for r in self.answers['parts-reuse-critical']['sampled_skill_damage']))
    def test_zero_rate_and_unit_rate_still_draw_and_zero_coefficient_does_not(self):
        for key,value in [('rate--100',False),('rate-85',True),('rate-200',True)]:
            rows=self.answers[key]['sampled_skill_damage'];self.assertTrue(rows);self.assertTrue(all(r['critical']==value for r in rows))
        self.assertFalse(self.answers['zero-coefficient']['sampled_skill_damage'])
    def test_cast_factors_frozen_across_per_hit_callbacks(self):
        rows=[r for r in self.answers['multi-hit-frozen-buffs']['sampled_skill_damage'] if not r['target']]
        self.assertEqual(len({(r['skill_rate'],r['atk_pct']) for r in rows[:5]}),1)
        self.assertNotEqual((rows[0]['skill_rate'],rows[0]['atk_pct']),(rows[5]['skill_rate'],rows[5]['atk_pct']))
    def test_nested_children_interleave_and_two_casters(self):
        rows=self.answers['nested-critical-children']['sampled_skill_damage'];names=[r['name'] for r in rows]
        self.assertIn(['source','child','child'],[names[i:i+3] for i in range(len(names)-2)])
        self.assertEqual({r['owner'] for r in self.answers['two-casters']['sampled_skill_damage']},{0,1})
    def test_inherited_inputs_only_one_explicit_domain_migration(self):
        rows,raw=a.prepare();old,_=a.parent.prepare();self.assertEqual([r[1] for r in rows[:39]],[r[1] for r in old])
        changed=[i for i,(x,y) in enumerate(zip(rows[:39],old)) if x!=y];self.assertEqual(len(changed),1);self.assertEqual(rows[changed[0]][0],a.MIGRATED);self.assertIsNone(old[changed[0]][2]);self.assertIsNotNone(rows[changed[0]][2])
        self.assertEqual((len(rows),sum(r[2] is not None for r in rows)),(62,59))
    def test_all_depth_slots_fit_and_exact_source_inverse_rejects_changes(self):
        from portable_coordinate_sampling_bank import LAYOUT as bank
        self.assertEqual(914352,bank['ROWS']+bank['PELLETS']*bank['ROW_WORDS']);self.assertLessEqual(914352+32*48,bank['META'])
        from portable_coordinate_sampled_skill_source_contract import project_sources
        from portable_coordinate_sampled_burst_source_contract import project_sources as burst_sources
        from portable_coordinate_sampled_vital_source_contract import project_sources as vital_sources
        project_sources(ROOT,burst_sources(ROOT,vital_sources(ROOT)))
        for name in ('gpu/damage_runtime.slang','gpu/dispatch_phases.slang','gpu/coordinate_sampled_skill_runtime.slang'):
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
    def test_reference_contract_rejects_missing_calculations_and_target_reroll(self):
        from portable_coordinate_sampled_skill_contracts import verify
        for c in self.cases:verify(c,self.answers[c['name'].rsplit('/',1)[1]])
        c=next(c for c in self.cases if c['name'].endswith('/parts-reuse-critical'));n=self.answers['parts-reuse-critical']
        bad=copy.deepcopy(n);bad['sampled_skill_damage'].pop(0)
        with self.assertRaises(AssertionError):verify(c,bad)
        bad=copy.deepcopy(n);row=next(r for r in bad['sampled_skill_damage'] if r['target']);row['critical']=not row['critical'];row['crit_fraction']=float(row['critical'])
        with self.assertRaises(AssertionError):verify(c,bad)
    def test_creation_indices_distinguish_targets_from_parent_hits(self):
        from world_coordinate_sampled_skill_native import creation_indices,trace_view
        c=next(c for c in self.cases if c['name'].endswith('/parts-reuse-critical'))
        with creation_indices(c) as indices:n,t=observe(c)
        view=trace_view(n['skill_trace'],indices)
        self.assertEqual([r['hit'] for r in view[:9]],[1,1,1,2,2,2,3,3,3])
        self.assertNotEqual(view,n['skill_trace'])
        for field,value in [('amount',-1),('row',999),('hit',1025)]:
            bad=copy.deepcopy(indices);bad[0][field]=value
            with self.assertRaises(AssertionError):trace_view(n['skill_trace'],bad)
        with self.assertRaises(AssertionError):trace_view(n['skill_trace'],indices[:-1])
if __name__=='__main__':unittest.main()
