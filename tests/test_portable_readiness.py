"""Diagnostics cannot promote packing to certification or relax sealed proofs."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_readiness import issue, summarize, inspect_effects, diagnostic_sources
from portable_runtime import validate_effect, UnsupportedPortable
from portable_readiness_cases import fixtures
from world_projectile_native import observe
spec=importlib.util.spec_from_file_location('readiness_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

class ReadinessTests(unittest.TestCase):
    def test_bounds_and_audience_are_not_missing_trigger_operators(self):
        base=dict(type='buff',stat='atk_pct',target='self',fixed_value=1,
                  trigger=dict(timing=['battle_start'],condition=[]))
        for changes,category in [(dict(max_trigger=1.5),'bounds'),
                                 (dict(event_scope='unknown'),'event_scope'),
                                 (dict(scaling='stack_count',scaling_ref=[]),'scaling')]:
            with self.assertRaises(UnsupportedPortable) as caught:
                validate_effect(dict(base,**changes),combat={},world_frame=True)
            diagnostic=issue(caught.exception,base)
            self.assertEqual(diagnostic['category'],category)
            self.assertEqual(diagnostic['diagnostic_source'],'structured_reason')
        structured=issue(UnsupportedPortable('trigger in wording',reason='bounds'))
        fallback=issue(ValueError('Unported trigger timing: future'))
        rows=[dict(effect_blockers=[dict(issue=structured),dict(issue=fallback)],program_issue=fallback)]
        self.assertEqual(diagnostic_sources(rows),dict(
            effect=dict(structured_reason=1,message_fallback=1),
            program=dict(structured_reason=0,message_fallback=1)))
        self.assertEqual(diagnostic_sources([])['effect']['message_fallback'],0)

    def test_stat_and_recipient_failures_have_independent_structured_reasons(self):
        for effect,category in [
            (dict(type='buff',stat='missing',target='all_allies'),'effect'),
            (dict(type='buff',stat='atk_pct',target='not-a-selector'),'recipient'),
            (dict(type='instant',stat='missing',target='self'),'effect'),
            (dict(type='instant',stat='burst_reentry',target='all_allies_excl_self'),'recipient')]:
            effect.update(trigger=dict(timing=['battle_start'],condition=[]),fixed_value=1)
            with self.assertRaises(UnsupportedPortable) as caught:validate_effect(effect,combat={})
            self.assertEqual(issue(caught.exception,effect)['category'],category)
        self.assertEqual(issue(UnsupportedPortable('wording may contain recipient',reason='effect'))['category'],'effect')

    def test_each_definition_is_inspected_without_mutation(self):
        effects=[dict(type='buff',stat='not-a-stat',target='self'),
                 dict(type='instant',stat='another-missing-op',target='self')]
        p=dict(effects=[dict(effect=e,owner=0) for e in effects]);before=copy.deepcopy(p)
        rows=inspect_effects(p)
        self.assertEqual([r['index'] for r in rows],[0,1]);self.assertEqual(p,before)
        profiles=[dict(character='a',favorite_stage=0,effect_blockers=rows),
                  dict(character='b',favorite_stage=0,effect_blockers=rows[:1])]
        ranked=summarize(profiles)
        self.assertEqual(ranked[0]['affected_profiles'],2)
        self.assertEqual(ranked[0]['single_observed_category_profiles'],1)

    def test_scaling_operators_are_not_conflated(self):
        a=issue(ValueError('Unported effect fields: scaling'),dict(type='buff',stat='def_pct',scaling='lost_hp_pct'))
        b=issue(ValueError('Unported effect fields: scaling'),dict(type='buff',stat='def_pct',scaling='other'))
        self.assertNotEqual(a['code'],b['code']);self.assertEqual(a['fields'],['scaling'])

    def test_missing_trigger_operator_survives_application_adapter(self):
        codes=[]
        for domain,descriptor in [('timing','multi_hit:2'),('timing','multi_hit:4'),
                                  ('condition','self_undying'),('timing','squad_burst_cast:2')]:
            effect=dict(type='buff',stat='atk_pct',target='self',fixed_value=1,
                        trigger=dict(timing=['battle_start'],condition=[]))
            effect['trigger'][domain if domain=='timing' else 'condition']=[descriptor]
            with self.assertRaises(UnsupportedPortable) as caught:
                validate_effect(effect,combat={},world_frame=True)
            diagnostic=issue(caught.exception,effect)
            self.assertEqual(diagnostic['category'],'trigger')
            self.assertEqual(diagnostic['operator'],dict(domain=domain,descriptor=descriptor))
            codes.append(diagnostic['code'])
        self.assertEqual(len(set(codes)),4)

    def test_trigger_grouping_ignores_wording_and_unrelated_valid_descriptors(self):
        from portable_trigger_specs import UnsupportedTrigger
        effect=dict(type='buff',stat='atk_pct',target='self')
        rows=[]
        for text in ('old diagnostic','new wording with recipient'):
            error=UnsupportedTrigger(text,domain='condition',descriptor='self_undying')
            rows.append(dict(issue=issue(error,effect)))
        self.assertEqual(rows[0]['issue']['code'],rows[1]['issue']['code'])
        profiles=[dict(character='a',favorite_stage=0,effect_blockers=rows)]
        ranked=summarize(profiles)
        self.assertEqual(ranked[0]['messages'],['new wording with recipient','old diagnostic'])
        self.assertEqual(ranked[0]['single_observed_category_profiles'],1)
        other=UnsupportedTrigger('other',domain='timing',descriptor='squad_burst_cast:2')
        rows.append(dict(issue=issue(other,effect)))
        self.assertTrue(all(r['single_observed_category_profiles']==0 for r in summarize(profiles)))
        # Validators without structured diagnostics also fail separately, rather
        # than collapsing all missing predicates into one speculative unlock.
        a=issue(ValueError('Unported predicate: a'),effect)
        b=issue(ValueError('Unported predicate: b'),effect)
        self.assertNotEqual(a['code'],b['code'])

    def test_development_selection_is_explicit_and_repacked(self):
        class Adapter:
            def prepare(self):return [('a',[1,2],None)],b'original'
            def development_entries(self):return [('new',[3,4],None)]
        entries,data=cli.prepare_entries(Adapter(),dict(purpose='development',selected_cases=['new']))
        self.assertEqual([r[0] for r in entries],['new'])
        self.assertEqual(data,bytes.fromhex('010000000300000004000000'))
        entries,data=cli.prepare_entries(Adapter(),dict(purpose='sealed'))
        self.assertEqual(data,b'original');self.assertEqual(len(entries),1)
        with self.assertRaises(ValueError):cli.prepare_entries(Adapter(),dict(purpose='development',selected_cases=['typo']))

    def test_development_cannot_run_on_cuda(self):
        with patch.object(cli,'verify_package',return_value=dict(purpose='development')):
            with self.assertRaisesRegex(ValueError,'requires Metal'):
                cli.run_capture(Path('/nonexistent'), 'cuda',180)

    def test_lost_hp_reads_live_hp_and_ignores_stack_multiplier(self):
        a,b,negative,expired=fixtures()[:4]
        native=observe(a)[0];self.assertGreater(native['allies'][0]['defense'],100)
        self.assertLess(observe(negative)[0]['allies'][0]['defense'],100)
        self.assertEqual(observe(expired)[0]['allies'][0]['defense'],100)
        stacked=copy.deepcopy(b);stacked['effects'][0]['max_stack']=1
        actual=observe(b)[0];single=observe(stacked)[0]
        for key in ('allies','damage','hits','projectile_shots'):
            self.assertEqual(actual[key],single[key])
        effect=a['effects'][0]
        validate_effect(effect,combat={})
        for changed in (dict(target='all_allies'),dict(stat='max_hp_pct')):
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,**changed),combat={})
        with self.assertRaises(UnsupportedPortable):validate_effect(effect)


class DevelopmentProofTests(unittest.TestCase):
    def test_native_mismatch_is_never_accepted_as_a_new_golden(self):
        import array, json, tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=bytes.fromhex('0100000007000000');raw=bytes(786432*4)
            native={'answer':1}
            adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1),
                prepare=lambda:([('case',[7],('domain',))],data),compare=lambda block,domain:native,
                cross=SimpleNamespace(digest=lambda v:cli.sha(json.dumps(v,sort_keys=True).encode()),normalized=cli.sha))
            entry=dict(name='case',input_sha256=cli.sha(data[4:]),native_sha256=adapter.cross.digest(native))
            golden=dict(input_sha256=cli.sha(data),source_sha256={},entries=[entry])
            (root/'input.bin').write_bytes(data);(root/'readback.bin').write_bytes(raw)
            cli.write(root/'evidence.json',dict(input_sha256=cli.sha(data),output_sha256=cli.sha(raw),source_sha256={},gpu_execution_verified=True,backend='metal'))
            for suffix in ('cu','metal'):(root/('generated.'+suffix)).write_bytes(b'generated')
            m=dict(purpose='development',suite='projectile',golden=golden)
            self.assertTrue(cli.compare_readback(m,root,adapter)['calculation_verified'])
            entry['native_sha256']='wrong'
            self.assertFalse(cli.compare_readback(m,root,adapter)['calculation_verified'])
            entry['native_sha256']=adapter.cross.digest(native)
            m['purpose']='sealed';golden.update(output_sha256='wrong',generated_normalized={'cuda':'wrong','metal':'wrong'})
            result=cli.compare_readback(m,root,adapter)
            self.assertFalse(result['calculation_verified'])
            self.assertIn('full readback fingerprint mismatch',[r['reason'] for r in result['mismatches']])

    def test_direct_health_predicates_are_explicit_not_general_stat_bypasses(self):
        from portable_specs import LIMITS as L,FIELDS as F
        adapter=cli.module(ROOT/'research/verify-world-projectile-short.py')
        for c in fixtures()[4:6]:
            words,_,_=adapter.suite.compile_case(c)
            self.assertTrue(words[L['DEFINITION_BASE']+F['FLAGS']] & 256)
            native=observe(c)[0]
            if c['effects'][0]['stat']=='def_pct':self.assertEqual(native['allies'][0]['defense'],130)
            else:self.assertEqual(native['allies'][0]['max_hp'],13000)
            self.assertLess(native['allies'][0]['hp_pct'],99)


class RealWorldCoverPolicyTests(unittest.TestCase):
    def test_cover_sync_matches_presence_of_authored_boss_patterns(self):
        import engine_worker
        from detail_coverage import body_for
        from portable_projectile_roster_input import compile_projectile_battle
        body=dict(body_for(['목단','도라','드레이크','N102','메어리'],3),burst_gauge_mode='accumulate')
        for patterns in ([],[dict(id='attack',kind='attack',delay=1,spec=dict(atk=100,coeff=100,target='all'))]):
            case=copy.deepcopy(body);case['enemy']['patterns']=patterns
            prepared=engine_worker.evaluate(dict(case,_portable_static_inputs=True))
            words,_=compile_projectile_battle(prepared)
            self.assertEqual(words[7],int(bool(patterns)))


class TypedTauntTests(unittest.TestCase):
    def test_ranked_enemy_marker_routes_victims_and_ignore_taunt_bypasses_it(self):
        ranked,ignored=fixtures()[-2:]
        a=observe(ranked)[0]['allies'];b=observe(ignored)[0]['allies']
        self.assertLess(a[0]['hp'],10000);self.assertEqual(a[4]['hp'],10000)
        self.assertEqual(b[0]['hp'],10000);self.assertLess(b[4]['hp'],10000)

if __name__=='__main__':unittest.main()
