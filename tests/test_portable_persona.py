"""Persona uses native presence and immutable innate-B3 masks, not numeric values."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_persona_cases import fixtures
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import validate_effect,UnsupportedPortable
from world_projectile_native import observe


class PersonaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('persona_test_adapter',ROOT/'research/verify-world-persona-short.py')
        cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)

    def test_policy_requires_allied_private_marker_and_state_selector(self):
        effect=fixtures()[1]['effects'][0]
        for changes,world,combat in [({},False,{}),({},True,None),({'target':'boss'},True,{}),({'type':'instant'},True,{})]:
            with self.subTest(changes=changes),self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,**changes),world_frame=world,combat=combat)
        validate_effect(effect,world_frame=True,combat={})
        with self.assertRaises(UnsupportedPortable):validate_effect(fixtures()[0]['effects'][0],combat={})

    def test_canonical_marker_and_selector_lower_without_cpu_or_gpu_execution(self):
        from calculator import timeline
        import portable_backend
        def forbidden(*a,**k):raise AssertionError('Battle during persona preparation')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,raw=self.adapter.prepare()
        self.assertEqual(len(entries),41);self.assertEqual(sum(e[2] is not None for e in entries),25)
        words=entries[1][1]
        self.assertEqual(words[L['DEFINITION_BASE']+F['KIND']],4)
        self.assertEqual(words[L['DEFINITION_BASE']+F['STAT']],0)
        self.assertEqual(words[L['DEFINITION_EXTRA_BASE']+3],1)
        at=L['RECIPIENT_BASE']+8
        self.assertEqual(words[at:at+6],[18,0,6,0,0,0])
        self.assertEqual(words[at+7]>>4,0) # eager, not a deferred rank snapshot

    def test_native_witness_exercises_presence_value_independence_and_innate_stage(self):
        cases=fixtures();before=copy.deepcopy(cases);battles={c['name']:observe(c)[0] for c in cases}
        self.assertEqual(cases,before)
        baseline=battles['persona-no-marker']['damage']
        marked=battles['persona-value-0']['damage']
        self.assertGreater(marked[1],baseline[1]);self.assertEqual(marked[0],baseline[0])
        for name in ('persona-value-1','persona-value--5','persona-runtime-false-still-presence','persona-innate-stage-ignores-override','persona-gear-source-presence'):
            self.assertEqual(battles[name]['damage'],marked)
        for name in ('persona-exclude-self','persona-marker-after-selection','persona-finite-false-not-active','persona-marked-non-b3-not-promoted','persona-marker-end-child'):
            self.assertEqual(battles[name]['damage'],baseline)
        self.assertEqual(battles['persona-zero-stack-still-presence']['damage'],marked)
        carriers=battles['persona-zero-stack-still-presence']['named_state']['allied_carriers']
        self.assertTrue(any(c['name']=='persona' and c['stack']==0 for c in carriers))
        self.assertGreater(battles['persona-target-code-persona-code']['damage'][0],battles['persona-target-code-different-code']['damage'][0])
        all_b3=battles['persona-innate-b3-only']['damage']
        self.assertGreater(all_b3[1],baseline[1]);self.assertGreater(all_b3[2],baseline[2]);self.assertEqual(all_b3[3:],baseline[3:])

    def test_private_counter_view_keeps_exact_enemy_code_namespace(self):
        from portable_target_counter_program import patch_program
        from world_frame_native import roster_names,authored_metadata
        case=fixtures()[-1];words,metadata,_=self.adapter.suite.compile_case(case)
        names=roster_names(case);literal=authored_metadata(case)
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=literal[n]) for n in names]
        effects=[(e,names[o]) for e,o in zip(case['effects'],case['owners'])]
        before=list(words);patch_program(words,metadata,chars,effects);self.assertEqual(words,before)
        forged=copy.deepcopy(metadata);forged['states']['unrelated-symbol']=len(forged['states'])
        with self.assertRaisesRegex(ValueError,'name symbols'):patch_program(list(words),forged,chars,effects)
        bad=list(words);bad[L['WORLD_META_BASE']+1]=L['DEFINITIONS']+1
        with self.assertRaisesRegex(ValueError,'code descriptor'):patch_program(bad,metadata,chars,effects)


if __name__=='__main__':unittest.main()
