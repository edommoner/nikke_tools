"""Native sensitivity and unchanged shared word layout for new-engine keys."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_new_character_cases import fixtures
from portable_specs import LIMITS as L,FIELDS as F,check_schema
from world_projectile_native import observe


def adapter():
    spec=importlib.util.spec_from_file_location('newchars_adapter',ROOT/'research/verify-world-projectile-short.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.suite


class NewCharacterTests(unittest.TestCase):
    def test_each_key_packs_without_battle_and_wire_is_unchanged(self):
        from calculator import timeline
        import portable_backend
        suite=adapter();check_schema()
        from portable_runtime_layout import runtime_initializer
        self.assertEqual((ROOT/'gpu/runtime_init.slang').read_text(),runtime_initializer())
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle during pack')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')):
            entries={c['name']:suite.compile_case(c)[0] for c in fixtures()}
        self.assertTrue(all(len(w)==104400 for w in entries.values()))
        engaged=entries['newchars-engaged']
        self.assertEqual(engaged[L['DEFINITION_BASE']+F['KIND']],4)
        self.assertEqual(engaged[L['DEFINITION_EXTRA_BASE']+3],2048)
        self.assertEqual(engaged[L['RECIPIENT_BASE']+8:L['RECIPIENT_BASE']+14],[26,0,0,0,0,0])
        width=entries['newchars-width'];self.assertEqual(width[L['DEFINITION_BASE']+F['KIND']],4)
        for label,kind,arg in [('full-charge',45,0),('down-above',46,1),('down-below',47,0)]:
            import struct
            words=entries['newchars-'+label];self.assertEqual(words[L['CONDITION_BASE']:L['CONDITION_BASE']+4],[kind,0,*struct.unpack('<II',struct.pack('<d',arg))])
        revive=entries['newchars-revive']
        self.assertEqual(revive[L['RECIPIENT_BASE']],27) # buff on down allies
        self.assertEqual(revive[L['RECIPIENT_BASE']+8],27)
        self.assertEqual(revive[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['TARGET']],1) # named success notification

    def test_native_each_active_key_changes_result_and_width_is_noop(self):
        cases=fixtures();before=copy.deepcopy(cases)
        results={c['name']:observe(c)[0] for c in cases}
        self.assertEqual(cases,before)
        for label in ('engaged','down-above','down-below','revive','full-charge'):
            with self.subTest(label=label):
                self.assertNotEqual(results['newchars-'+label]['damage'],results['newchars-'+label+'-control']['damage'])
        self.assertEqual(results['newchars-width']['damage'],results['newchars-width-control']['damage'])
        self.assertEqual(results['newchars-revive-alive']['damage'],results['newchars-revive-alive-control']['damage'])

    def test_new_descriptors_require_world_and_strict_thresholds(self):
        from portable_runtime import validate_effect,UnsupportedPortable
        from detail_gpu import compile_effects,UnsupportedDetail
        suite=adapter()
        for c in fixtures():
            for effect in c['effects']:
                if effect.get('stat')=='engaged_state' or effect.get('trigger',{}).get('condition'):
                    with self.assertRaises((ValueError,UnsupportedPortable)):validate_effect(effect,combat={})
        from world_frame_native import authored_metadata,roster_names
        c=fixtures()[0];chars=[dict(name=n,_weapon=authored_metadata(c)[n]) for n in roster_names(c)]
        for target in ('self_and_engaged_allies','allies_down_all'):
            with self.assertRaisesRegex(UnsupportedDetail,'target list exceeds 21'):
                compile_effects(chars,[(dict(c['effects'][1],target=[target]*5),chars[0]['name'])])
        for condition in ('ally_down_count_above:1.5','ally_down_count_below:2147483648'):
            with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(dict(c['effects'][1],trigger=dict(timing=['battle_start'],condition=[condition])),chars[0]['name'])])


class ProductNativeSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json,engine_worker
        cls.scenes=json.loads((ROOT/'tests/fixtures/gpu-new-characters-sensitivity-v1.json').read_text())
        cls.results={name:engine_worker.evaluate(dict(copy.deepcopy(body),compute_backend='cpu')) for name,body in cls.scenes.items()}

    def test_real_product_rows_change_canonical_results(self):
        import engine_worker
        from calculator import buff_manager as bm
        predicates=[('engaged_state','engaged',lambda e:e.get('stat')=='engaged_state'),
                    ('self_and_engaged_allies','engaged',lambda e:e.get('target')=='self_and_engaged_allies'),
                    ('allies_down_all','down',lambda e:e.get('target')=='allies_down_all'),
                    ('ally_down_count_above','down',lambda e:any(c.startswith('ally_down_count_above:') for c in e.get('trigger',{}).get('condition',[]))),
                    ('ally_down_count_below','down-two',lambda e:any(c.startswith('ally_down_count_below:') for c in e.get('trigger',{}).get('condition',[]))),
                    ('revive','down',lambda e:e.get('stat')=='revive')]
        for key,scene,predicate in predicates:
            replacement={n:[e for e in effects if not predicate(e)] for n,effects in bm._PARSED_SKILLS.items()}
            with self.subTest(key=key),patch.dict(bm._PARSED_SKILLS,replacement,clear=True):
                ablated=engine_worker.evaluate(dict(copy.deepcopy(self.scenes[scene]),compute_backend='cpu'))
                self.assertNotEqual(self.results[scene]['total_damage'],ablated['total_damage'])
        downs=self.results['down']['incoming_hits'];self.assertEqual(sum(hit['down'] for hit in downs),3)
        self.assertTrue(any(e['event']=='full_burst 시작' for e in self.results['down']['burst_timeline']))

    def test_successful_revive_event_changes_product_and_empty_revive_does_not_notify(self):
        import engine_worker
        from calculator import buff_manager as bm
        original=bm.BuffManager.notify;events=[]
        def suppress(manager,event,*args,**kwargs):
            if event=='event:나노 입자 투여':events.append(event);return
            return original(manager,event,*args,**kwargs)
        with patch.object(bm.BuffManager,'notify',suppress):
            ablated=engine_worker.evaluate(dict(copy.deepcopy(self.scenes['down']),compute_backend='cpu'))
        self.assertEqual(events,['event:나노 입자 투여'])
        self.assertNotEqual(ablated['total_damage'],self.results['down']['total_damage'])
        events.clear()
        with patch.object(bm.BuffManager,'notify',suppress):engine_worker.evaluate(dict(copy.deepcopy(self.scenes['full-charge']),compute_backend='cpu'))
        self.assertEqual(events,[])

    def test_cube_changes_incoming_hp_with_base_stats_and_common_cube_preserved(self):
        import engine_worker
        from calculator import buff_manager as bm
        original=bm.BuffManager._make_cube_effects
        def without_cube(manager,name,level):return [e for e in original(manager,name,level) if e.get('name')!='큐브:렐릭 베젤 큐브']
        with patch.object(bm.BuffManager,'_make_cube_effects',without_cube):
            ablated=engine_worker.evaluate(dict(copy.deepcopy(self.scenes['cube']),compute_backend='cpu'))
        self.assertEqual(ablated['base_stats'],self.results['cube']['base_stats'])
        self.assertNotEqual(ablated['incoming_hits'],self.results['cube']['incoming_hits'])

    def test_native_cube_uses_full_burst_start_and_caps_at_three_without_healing(self):
        import portable_detail
        from calculator.buff_manager import BuffManager
        prepared,_=portable_detail.prepare(self.scenes['cube']);name=prepared['chars'][0]['name']
        effect=next(row['effect'] for row in prepared['effects'] if row['effect'].get('name')=='큐브:렐릭 베젤 큐브')
        def register(manager):manager._effects=[(copy.deepcopy(effect),name)];manager._build_notify_index()
        base=10000.0
        with patch.object(BuffManager,'_register_all',register):
            manager=BuffManager(prepared['chars'],state=dict(base_stats={n['name']:dict(hp=base,atk=100,**{'def':0}) for n in prepared['chars']},hp={name:5000.0},hp_pct={name:50.0}))
        self.assertEqual(manager.effective_max_hp(name),base)
        expected=base*effect['fixed_value']/100
        for count in range(1,5):
            manager.notify('full_burst_start',float(count),name)
            self.assertEqual(manager.effective_max_hp(name),base+min(count,3)*expected)
            self.assertEqual(manager.state['hp'][name],5000.0)

    def test_ordinary_width_and_immunity_rows_have_no_damage_delta_in_these_scenes(self):
        import engine_worker
        from calculator import buff_manager as bm
        for scene,predicate in [('width',lambda e:e.get('stat')=='normal_atk_width_pct'),('full-charge',lambda e:'during_full_charge' in e.get('trigger',{}).get('condition',[]))]:
            replacement={n:[e for e in effects if not predicate(e)] for n,effects in bm._PARSED_SKILLS.items()}
            with patch.dict(bm._PARSED_SKILLS,replacement,clear=True):ablated=engine_worker.evaluate(dict(copy.deepcopy(self.scenes[scene]),compute_backend='cpu'))
            self.assertEqual(ablated['total_damage'],self.results[scene]['total_damage'])


class NewCharacterGeneratedTests(unittest.TestCase):
    pass

if __name__=='__main__':unittest.main()
