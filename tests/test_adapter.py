import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import engine_worker as w

class ImportAndEvaluationTests(unittest.TestCase):
    def test_missing_fields_do_not_get_strong_defaults(self):
        name=next(iter(w.META))
        result=w.import_data({'base':'default','chars':{name:{'skill_levels':7}}})
        self.assertIn('cube',result['missing'][name])
        self.assertNotIn('cube',result['profile']['chars'][name])
        self.assertEqual(result['profile']['base'],'ungrown')

    def test_raw_import_preserves_slots_and_observed_cube(self):
        code=next(k for k,v in w.MAPPINGS['id_map'].items() if w.RESOURCE_NAMES.get(v)=='앨리스')
        cube=next((k,v) for k,v in w.importer._load_cube_name_map().items() if v in w.spec.CUBES)
        detail={'name_code':int(code),'attractive_lv':30,'skill1_lv':7,'skill2_lv':8,'ulti_skill_lv':9,'harmony_cube_tid':cube[0],'harmony_cube_lv':7}
        for p,_ in w.importer.PARTS:
            detail.update({f'{p}_equip_tier':10,f'{p}_equip_lv':5})
            for i in (1,2,3):detail[f'{p}_equip_option{i}_id']=0
        detail['head_equip_option1_id']=101
        detail['arm_equip_option1_id']=101
        percent=w.importer._load_equip_skill_table()['max_ammo_pct'][9]*100
        raw={'characters':[{'name_code':int(code),'grade':3,'core':0,'lv':1,'combat_power':123456}], 'details':[detail],
             'state_effects':[{'id':101,'function_details':[{'function_type':'StatAmmoLoad','function_value':round(percent*100)}]}],
             'outpost':{'recycle_room_researches':[{'tid':1001,'lv':150},{'tid':1101,'lv':100},{'tid':1102,'lv':100},{'tid':1103,'lv':100},{'tid':1201,'lv':100},{'tid':1202,'lv':100},{'tid':1203,'lv':100},{'tid':1204,'lv':100},{'tid':1205,'lv':100}]}}
        result=w.import_data(raw)
        entry=result['profile']['chars']['앨리스']
        self.assertEqual(entry['equip_skills']['max_ammo_pct'],[percent,percent])
        self.assertEqual(entry['cube'],{'name':cube[1],'level':7})
        self.assertTrue(entry['_unsynced'])
        self.assertEqual(entry['_observed_combat_power'],123456)
        self.assertNotIn('앨리스',result['missing'])

    def test_unknown_options_block_instead_of_disappearing(self):
        code=next(k for k,v in w.MAPPINGS['id_map'].items() if w.RESOURCE_NAMES.get(v)=='앨리스')
        detail={'name_code':int(code),'attractive_lv':1,'skill1_lv':1,'skill2_lv':1,'ulti_skill_lv':1}
        for p,_ in w.importer.PARTS:
            detail.update({f'{p}_equip_tier':0,f'{p}_equip_lv':0})
            for i in (1,2,3):detail[f'{p}_equip_option{i}_id']=0
        detail['head_equip_option1_id']=99999999
        result=w.import_data({'characters':[{'name_code':int(code),'grade':0,'core':0,'lv':1}],'details':[detail],'state_effects':[]})
        self.assertTrue(any('未知' in k for k in result['missing']['앨리스']))

    def test_scenario_isolation_and_stat_injection(self):
        demo=w.demo()
        body={'profile':demo['profile'],'squad':demo['squad'],'duration':8,'level':400,'enemy':{'def':31784,'code':'풍압'}}
        original=copy.deepcopy(body)
        baseline=w.evaluate(body)
        changed=copy.deepcopy(body);changed['stat_deltas']={'앨리스':{'atk':5000,'hp':1000,'def':100}}
        altered=w.evaluate(changed)
        repeated=w.evaluate(body)
        self.assertEqual(body,original)
        self.assertEqual(baseline['total_damage'],repeated['total_damage'])
        self.assertEqual(altered['base_stats']['앨리스']['atk']-baseline['base_stats']['앨리스']['atk'],5000)
        self.assertEqual(altered['base_stats']['앨리스']['hp']-baseline['base_stats']['앨리스']['hp'],1000)
        self.assertTrue(altered['hypothetical'])
        self.assertFalse(baseline['hypothetical'])
        self.assertGreater(altered['total_damage'],baseline['total_damage'])

    def test_duplicate_and_unowned_are_rejected(self):
        d=w.demo();body={'profile':d['profile'],'squad':[d['squad'][0]]*5}
        with self.assertRaisesRegex(ValueError,'異なる'):w.evaluate(body)
        body['squad']=d['squad'][:4]+['not owned']
        with self.assertRaisesRegex(ValueError,'所持'):w.evaluate(body)

    def test_no_cube_has_no_stats_or_effects(self):
        d=w.demo();body={'profile':d['profile'],'squad':d['squad'],'duration':8,'level':400}
        baseline=w.evaluate(body)
        changed=copy.deepcopy(body)
        for entry in changed['profile']['chars'].values():entry['cube']={'name':'__none__','level':0}
        without=w.evaluate(changed)
        name=d['squad'][0]
        expected=w.base_stat._CUBE['_stats']['15']['atk']
        self.assertEqual(baseline['base_stats'][name]['atk']-without['base_stats'][name]['atk'],expected)
        self.assertLess(without['total_damage'],baseline['total_damage'])

    def test_partial_console_and_empty_gear_are_missing(self):
        d=w.demo();name=d['squad'][0]
        entry=d['profile']['chars'][name];entry.pop('console',None);entry['equipment']['머리']={}
        d['profile']['_account']['console']={'common_level':0}
        missing=w.missing_fields(d['profile'])[name]
        self.assertIn('console.class_level',missing)
        self.assertIn('equipment.머리.level',missing)


    def test_burst_rules_and_position_are_applied_without_manual_shooting(self):
        d=w.demo(True)
        mast='마스트 : 로망틱 메이드'
        squad=['리타','크라운',mast,'앨리스','모더니아']
        profile=d['profile']
        right=w.burst_controls(squad,profile,'rules')
        self.assertEqual(right[mast]['control']['burst']['pattern'],'3의 배수')
        left=w.burst_controls([mast,'리타','크라운','앨리스','모더니아'],profile,'rules')
        self.assertEqual(left[mast]['control']['burst']['pattern'],'1,3,5,9,11,14')
        self.assertEqual(w.burst_controls(squad,profile,'auto'),{})
        for entry in right.values():
            self.assertEqual(set(entry['control']),{'burst'})
        body={'profile':profile,'squad':squad,'duration':90,'level':400,'burst_policy':'mast3'}
        result=w.evaluate(body)
        self.assertEqual(result['burst_patterns'][mast],'every:3')
        cycle=1; casts=[]
        for row in result['burst_timeline']:
            if row['event']=='full_burst 종료': cycle+=1
            if row['character']==mast: casts.append(cycle)
        self.assertIn(3,casts)
        self.assertNotIn(1,casts)
        self.assertNotIn(2,casts)
        self.assertEqual(w.burst_controls(['리타',mast,'앵커 : 이노센트 메이드','앨리스','모더니아'],profile,'rules').get(mast),None)
        with self.assertRaisesRegex(ValueError,'運用'):
            w.burst_controls(squad,profile,'bogus')

    def test_adjacent_and_right_targets_follow_actual_squad_order(self):
        from calculator.buff_manager import BuffManager
        manager=object.__new__(BuffManager)
        manager.squad_names=['a','b','c','d','e']
        manager.state={}
        self.assertEqual(manager._resolve_target('allies_right:2','b'),['c','d'])
        self.assertEqual(manager._resolve_target('allies_adjacent:2','b'),['b','a','c'])
        self.assertEqual(manager._resolve_target('allies_right:2','e'),[])


    def test_demo_has_visible_growth_variation_and_historical_presets_have_sources(self):
        chars=list(w.demo(True)['profile']['chars'].values())
        for field in ('breakthrough','core_enhancement','affinity','favorite_stage','_observed_combat_power','_observed_level'):
            self.assertGreater(len({c[field] for c in chars}),3,field)
        presets=w.enemy_presets()
        self.assertEqual(len([p for p in presets if p.get('mode','solo')=='solo']),42)
        self.assertEqual(len([p for p in presets if p.get('mode')=='union']),300)
        self.assertEqual({p['season'] for p in presets if p.get('mode','solo')=='solo'},set(range(1,43)))
        for p in presets:
            self.assertIn('enikk.app',p['source'])
            self.assertEqual(p['settings']['enemy-def'],p['source_defense']*p['defense_ratio']/10000)

    def test_mast_policy_without_mast_explicitly_reports_auto(self):
        d=w.demo();body={'profile':d['profile'],'squad':d['squad'],'duration':8,'level':400}
        auto=w.evaluate(body);fallback=w.evaluate({**body,'burst_policy':'mast3'})
        self.assertEqual(auto['total_damage'],fallback['total_damage'])
        self.assertEqual(fallback['burst_policy'],'auto')
        self.assertEqual(fallback['requested_burst_policy'],'mast3')
        self.assertTrue(any('マスト' in v for v in fallback['app_warnings']))

if __name__=='__main__':unittest.main()


