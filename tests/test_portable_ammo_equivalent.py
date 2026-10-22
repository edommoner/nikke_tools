"""Shared literal count domain and finite source/admission fault guards."""
import copy,importlib.util,re,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_ammo_equivalent_cases import fixtures
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
from portable_definition_view_contract import verify


class AmmoEquivalentTests(unittest.TestCase):
    def test_diagnostic_rows_have_distinct_stages_and_owned_call_sites_without_control_stubs(self):
        source=(ROOT/'gpu/event_runtime.slang').read_text()
        sites={'PROJECTILE_ADMIT_ROW':('gpu/admission_runtime.slang',4),'PROJECTILE_POOL_ROW':('gpu/world_actor_pools.slang',8000),'PROJECTILE_COUNTER_ROW':('gpu/target_counter_runtime.slang',11)}
        stages=[]
        for macro,(expected,stage) in sites.items():
            found=re.findall(r'#define '+macro+r'\(s,row,d\) PROJECTILE_DIAGNOSTIC_FIELDS\(s,row,d,([0-9]+)\)',source)
            self.assertEqual(found,[str(stage)]);stages.append(stage)
            users=[p.relative_to(ROOT).as_posix() for p in (ROOT/'gpu').glob('*.slang') if p.name!='event_runtime.slang' and re.search(r'\b'+macro+r'\(',p.read_text())]
            self.assertEqual(users,[expected])
        self.assertEqual(len(stages),len(set(stages)))
        for path in ('gpu/admission_runtime.slang','gpu/program_phases.slang'):
            self.assertNotRegex((ROOT/path).read_text(),r's\.error\s*=\s*6399[5-9]|results\[output\]\s*=\s*63999')

    def adapter(self):
        spec=importlib.util.spec_from_file_location('ammo_equivalent_tests',ROOT/'research/verify-world-ammo-equivalent-short.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def test_literal_finite_domain_and_structured_policy_rejections(self):
        effect=fixtures()[0]['effects'][1]
        for value in (-4096,-3.9,0,1,4.999999999999999,40,4096):validate_effect(dict(effect,fixed_value=value),combat={},world_frame=True)
        for changed,reason in [(dict(fixed_value=4096.1),'effect'),(dict(fixed_value=-4096.1),'effect'),(dict(fixed_value=float('nan')),'effect'),(dict(fixed_value=float('inf')),'effect'),(dict(fixed_value=True),'effect'),(dict(values=[]),'effect'),(dict(scaling='stack_count'),'scaling'),(dict(target='all_allies'),'recipient')]:
            with self.subTest(changed=changed),self.assertRaises(UnsupportedPortable) as caught:validate_effect(dict(effect,**changed),combat={},world_frame=True)
            self.assertEqual(caught.exception.reason,reason)
        for combat,world in ((None,True),({},False)):
            with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat=combat,world_frame=world)

    def test_packing_retains_literal_fraction_and_emits_no_cpu_count(self):
        cases=fixtures();before=copy.deepcopy(cases);m=self.adapter()
        for case in cases:
            words,_,_=m.suite.compile_case(case)
            for i,effect in enumerate(case['effects']):
                if effect.get('stat')!='squad_ammo_consume_as':continue
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];self.assertEqual(words[at+F['KIND']],37)
                value=struct.unpack('<d',struct.pack('<II',*words[at+F['VALUE']:at+F['VALUE']+2]))[0]
                self.assertEqual(value,effect.get('fixed_value',effect.get('values',{}).get('10')))
        self.assertEqual(cases,before);entries,data=m.prepare();self.assertEqual(len(entries),46);self.assertEqual(sum(e[2] is not None for e in entries),29);self.assertEqual(len(data),4+46*m.suite.INPUT*4)

    def test_exact_delta_rejects_removed_hooks_broader_bounds_bulk_counts_and_wrong_log(self):
        from portable_ammo_equivalent_source_contract import ledger
        data=ledger(ROOT);self.assertEqual(set(verify(ROOT)['reviewed_ammo_equivalent_sources']),set(data['sources']))
        for name,row in data['sources'].items():
            source=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(change['current'],change['baseline'],1)})
        for name,old,new in [('gpu/admission_runtime.slang','f64FromI64(4096)','f64FromI64(8192)'),('gpu/dispatch_phases.slang','uint(count-1)','uint(count)'),('gpu/event_runtime.slang','if(f.mode==15) logResourceNotification','if(true) logResourceNotification')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})


if __name__=='__main__':unittest.main()
