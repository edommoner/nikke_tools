"""Shared packing/admission boundaries and finite source fault checks."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_reference_specs import mode_capacity_reference
from portable_mode_capacity_cases import fixtures
from portable_mode_capacity_source_contract import baseline_source
from portable_definition_view_contract import verify
from portable_specs import LIMITS as L

class ModeCapacityTests(unittest.TestCase):
    def test_authoring_validation_and_sentinel_policy(self):
        effect=fixtures()[0]['effects'][-1]
        self.assertEqual(mode_capacity_reference(effect),effect['max_ammo_scaling_ref'])
        self.assertIsNone(mode_capacity_reference(dict(effect,max_ammo=-1)))
        self.assertEqual(mode_capacity_reference(dict(effect,max_ammo=2.0)),effect['max_ammo_scaling_ref'])
        for value in (True,False,'2',None,0,-2,2.9,10001,float('nan'),float('inf'),2**10000):
            with self.subTest(base_type=type(value).__name__),self.assertRaises(ValueError):mode_capacity_reference(dict(effect,max_ammo=value))
        for value in (None,False,0,'',[],{},'colon:name'):
            with self.subTest(value=value),self.assertRaises(ValueError):mode_capacity_reference(dict(effect,max_ammo_scaling_ref=value))
        bad=copy.deepcopy(effect);bad.pop('max_ammo')
        with self.assertRaisesRegex(ValueError,'explicit max_ammo'):mode_capacity_reference(bad)
    def adapter(self):
        s=importlib.util.spec_from_file_location('mode_capacity_tests','research/verify-world-mode-capacity-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def test_shared_cases_pack_and_match_reference_identity_without_mutation(self):
        m=self.adapter();cases=fixtures();before=copy.deepcopy(cases)
        for c in cases:
            words,metadata,bindings=m.suite.compile_case(c);row=len(c['effects'])-1;descriptor=words[L['REFERENCE_DEFINITION_BASE']+row*4+3]
            if c['effects'][-1]['max_ammo']==-1:
                self.assertEqual(descriptor,0);continue
            key=(descriptor&511)-1;name=descriptor>>9
            self.assertEqual(metadata['resource_names'][key],c['effects'][-1]['max_ammo_scaling_ref'])
            self.assertEqual(metadata['states'][c['effects'][-1]['max_ammo_scaling_ref']],name)
        self.assertEqual(cases,before)
        entries,data=m.prepare();self.assertEqual(len(entries),32);self.assertEqual(len(data),4+32*m.suite.INPUT*4)
    def test_source_guards_reject_capacity_math_cache_bypass_and_zero_exit_faults(self):
        result=verify(ROOT);self.assertEqual(set(result['reviewed_mode_capacity_sources']),{'gpu/reference_runtime.slang','gpu/ammo_instant_runtime.slang','gpu/weapon_runtime.slang','gpu/weapon_frame_phases.slang'})
        for name,old,new in [('gpu/reference_runtime.slang','return uint(count)*base','return uint(count)+base'),('gpu/reference_runtime.slang','if (!present) value=ONE','if (!present) value=0'),('gpu/ammo_instant_runtime.slang','referencedModeCapacity(s,who,uint(mode),when)','fullCapacity(s,who,commands[at+1],true,when)'),('gpu/weapon_runtime.slang','s.modeCapacityEpoch[who]=0;w.capacity','s.modeCapacityEpoch[who]=s.modeEpoch[who];w.capacity'),('gpu/weapon_frame_phases.slang','w.shotLimit == 0','w.capacity == 0')]:
            text=(ROOT/name).read_text();self.assertIn(old,text);changed=text.replace(old,new,1)
            with self.subTest(name=name,old=old),self.assertRaises(AssertionError):baseline_source(ROOT,name,changed)
            with self.subTest(whole_contract=name,old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:changed})
    def test_raw_rejections_are_single_word_changes(self):
        entries,_=self.adapter().prepare();seed=entries[0][1]
        for name,words,domain in entries[-6:]:
            self.assertTrue(name.startswith('reject/'));self.assertIsNone(domain);self.assertEqual(sum(a!=b for a,b in zip(seed,words)),1)

if __name__=='__main__':unittest.main()
