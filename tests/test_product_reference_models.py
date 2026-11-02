"""Product requests must execute declared consumers and fail before omitted GPU work."""
import array,copy,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from runner import sim
from product_reference_models import normalize,execution,WARNING

class ProductReferenceModels(unittest.TestCase):
    def test_body_only_named_range_routes_frozen_empty_casts_through_native_landing(self):
        from portable_product_programs import body_for_program
        from named_range_battle import NamedRangeBattle
        body=body_for_program(ROOT,'named-range-fixed');body['duration']=15
        body['enemy']['patterns']=[dict(id='declared-static-boss',kind='idle')]
        spec=body['reference_models']['named_range'];spec['logical_geometry']=[]
        for rule in spec['rules']:rule['body_shape']['x']=1000.
        original=NamedRangeBattle.route;native=[]
        def checked(runtime,boss,event,fallback,*args,**kwargs):
            own=id(event) in runtime.pending;answer=original(runtime,boss,event,fallback,*args,**kwargs)
            if own and fallback.__name__=='route':native.append(answer)
            return answer
        aliases=(timeline.simulate,sim.simulate)
        with patch.object(NamedRangeBattle,'route',checked):result=engine_worker.evaluate(body)
        self.assertTrue(native,'Native landing must honor frozen selection even without ADDs')
        self.assertTrue(all(row==[] for row in native))
        self.assertTrue(result['reference_models']['named_range']['casts'])
        self.assertTrue(all(row['body_position']==row['add_count']==0 for row in result['reference_models']['named_range']['casts']))
        self.assertEqual(aliases,(timeline.simulate,sim.simulate))

    def test_explicit_body_only_named_range_and_movement_keep_original_effects(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from named_range_battle import normalize as private_range
        from detail_coverage import body_for
        for mode in ('fixed','accumulate'):
            for combined in (False,True):
                body=body_for_program(ROOT,'named-range-'+mode)
                spec=body['reference_models']['named_range'];spec['logical_geometry']=[]
                body['enemy']['patterns']=[dict(id='declared-static-boss',kind='idle')]
                with self.assertRaises(ValueError):private_range(spec['rules'],[])
                if combined:
                    roster=body['squad'][:3]+['유니','얀'];body['squad']=roster;body['profile']=body_for(roster,30)['profile']
                    body['reference_models']['enemy_movement']=dict(coord=copy.deepcopy(spec['coord']),logical_geometry=[],motion=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',actors=[]))
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle supplied to GPU')):
                    prepared,_=prepare(body);before=copy.deepcopy(prepared);source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(prepared,before)
                self.assertEqual(words[109968+2],0)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                self.assertIn('product_named_range',meta)
                self.assertEqual(source,'gpu/product_'+('movement_range_' if combined else 'named_range_')+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
                if combined:
                    self.assertEqual(words[115680+2],0)
                    self.assertIn('product_enemy_movement',meta)
                bad=copy.deepcopy(body);bad['duration']=1
                bad['enemy']['patterns']=[dict(id='future-add',kind='summon',delay=10,spec=dict(count=1,hp=1e30))]
                # Reject even before a delayed ADD or a named cast can exist.
                with patch.object(sim,'execute',side_effect=AssertionError('Invalid world must not run a CPU battle')):
                    with self.assertRaisesRegex(ValueError,'Every configured ADD'):compile_product(prepare(bad)[0])
                    with self.assertRaisesRegex(ValueError,'Every configured ADD'):engine_worker.evaluate(bad)

    def test_explicit_empty_movement_preserves_duration_carriers_and_rejects_future_add(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare,compile_product
        from portable_enemy_movement_wire import BASE,MAP
        from portable_specs import LIMITS as L,FIELDS as F
        from product_movement_model import normalize as product_motion
        from enemy_movement_model import normalize as private_motion
        from portable_runtime import UnsupportedPortable
        from calculator import timeline
        spec=dict(coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=[],motion=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',actors=[]))
        self.assertEqual(product_motion(spec)['motion']['actors'],[])
        with self.assertRaises(ValueError):private_motion(spec['motion'])
        for name in ('유니','얀'):
            for mode in ('fixed','accumulate'):
                body=selected_profile_bodies([name],0)[0][2];body.update(burst_gauge_mode=mode,reference_models={'enemy_movement':copy.deepcopy(spec)})
                body['enemy']['patterns']=[dict(id='declared-static-boss',kind='idle')]
                missing=copy.deepcopy(body);missing['enemy'].pop('patterns')
                with self.assertRaisesRegex(ValueError,'enemy.coord'):prepare(missing)
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                    prepared,_=prepare(body);before=copy.deepcopy(prepared);source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(prepared,before);self.assertEqual(words[BASE+2],0)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                for row in meta['enemy_movement']['domains']:
                    at=L['DEFINITION_BASE']+row['row']*L['DEFINITION_WORDS']
                    self.assertEqual(words[at+F['KIND']],0);self.assertEqual(words[BASE+MAP+row['row']],1 if name=='유니' else 2)
                bad=copy.deepcopy(body);bad['enemy']['patterns']=[dict(id='future-add',kind='summon',delay=10,spec=dict(count=1,hp=1e30))]
                with self.assertRaisesRegex(ValueError,'Every configured ADD'):compile_product(prepare(bad)[0])
        # Native frame guard must reject a future ADD even before it is live.
        bad['duration']=1
        aliases=(timeline.simulate,sim.simulate)
        with self.assertRaisesRegex(ValueError,'Every configured ADD'):engine_worker.evaluate(bad)
        self.assertEqual(aliases,(timeline.simulate,sim.simulate))

    def test_original_named_carriers_keep_every_definition_and_reject_matching_consumer(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'named-carriers-'+mode)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,_=prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,metadata=compile_product(prepared)
            self.assertEqual(prepared,before);self.assertEqual((iw,ow,len(words)),(104400,786432,104400));validate_composed_stride(source,iw,ow)
            self.assertEqual(set(metadata['binding_source_indices']),set(range(len(prepared['effects']))))
            info=metadata['product_named_carriers'];self.assertTrue(info['all_original_effects_preserved']);self.assertFalse(info['cpu_state_or_schedule_supplied'])
            self.assertEqual(len(info['source_indices']),2)
            for index in info['source_indices']:
                e=prepared['effects'][index]['effect'];row=metadata['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                self.assertEqual(words[at+F['KIND']],0);self.assertEqual(words[at+F['STAT']],93 if e['stat']=='effect_target_count_add' else 94)
                self.assertEqual(words[at+F['TARGET_NAME']],metadata['states'][e['target_effect']])
                import struct
                self.assertEqual(struct.pack('<2I',*words[at+F['VALUE']:at+F['VALUE']+2]),struct.pack('<d',e['fixed_value']))
                self.assertEqual(struct.pack('<2I',*words[at+F['DURATION']:at+F['DURATION']+2]),struct.pack('<d',e['duration']))
                self.assertEqual(words[L['RECIPIENT_BASE']+row*8],12)
            changed=copy.deepcopy(prepared);changed['effects'][-1]['effect']['name']=info['definitions'][0]['effect']['target_effect']
            with self.assertRaisesRegex(UnsupportedPortable,'matching skill definition'):compile_product(changed)

    def test_coordinate_cover_combines_literal_banks_without_cpu_battle(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from portable_cover_defense_wire import LAYOUT as C
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'coordinate-cover-'+mode);before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,run=prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,metadata=compile_product(prepared)
            self.assertEqual(body,before);self.assertEqual(prepared,original)
            self.assertEqual((iw,ow,len(words)),(115704,2048912,115704));validate_composed_stride(source,iw,ow)
            self.assertEqual(set(metadata['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(metadata['product_coordinate_cover'])
            self.assertEqual(metadata['product_manual_cover_owners'],[0])
            self.assertEqual(words[C['BASE']:C['BASE']+4],[0x43444231,1,5,0])
            self.assertFalse(metadata['product_cover_defense']['cpu_state_or_schedule_supplied'])
            self.assertFalse(run.expected)
            with self.assertRaises(ValueError):validate_composed_stride(source,115680,2032000)

    def test_coordinate_public_preserves_all_definitions_and_explicit_empty_scene(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from portable_logical_geometry_wire import LAYOUT
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'coordinate-'+mode);before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,run=prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,metadata=compile_product(prepared)
            self.assertEqual(body,before);self.assertEqual(prepared,original)
            self.assertFalse(run.expected);self.assertEqual(run.config['rng_mode'],'random')
            self.assertEqual((iw,ow,len(words)),(115680,2032000,115680));validate_composed_stride(source,iw,ow)
            self.assertEqual(words[LAYOUT['BASE']+2],0)
            self.assertEqual(set(metadata['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertFalse(metadata['product_coordinate']['cpu_state_or_schedule_supplied'])
            self.assertEqual(run.enemy['coord'],body['reference_models']['coordinate']['coord'])
            with self.assertRaisesRegex(ValueError,'explicit healing source'):
                normalize({**body['reference_models'],'enemy_healing':[]})

    def test_coordinate_model_configures_only_request_run_and_restores_global_aliases(self):
        from product_coordinate_model import normalize_product
        from types import SimpleNamespace
        spec=normalize_product(dict(coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=[]))
        run=SimpleNamespace(enemy={},expected=True,config={'rng_mode':'expected'})
        def native(value):
            self.assertIs(value,run);self.assertFalse(value.expected);self.assertEqual(value.config['rng_mode'],'random')
            self.assertEqual(value.enemy['coord'],spec['coord']);return 'native'
        state=timeline.random.getstate()
        with patch.object(sim,'execute',side_effect=native) as original:
            with execution({'coordinate':spec},['a','b','c','d','e']) as result:
                self.assertEqual(sim.execute(run),'native')
            self.assertIs(sim.execute,original)
        self.assertEqual(timeline.random.getstate(),state)
        self.assertEqual(result['coordinate']['logical_colliders'],0)

    def test_coordinate_empty_add_geometry_is_explicit_and_unowned_output_rejected(self):
        from portable_logical_geometry_wire import pack
        from types import SimpleNamespace
        from portable_product_coordinate import read_result,OUTPUT
        from portable_runtime import UnsupportedPortable
        from portable_specs import LIMITS as L
        from product_coordinate_model import normalize_product
        body=SimpleNamespace(kind=0,identity=0,label='__enemy__',run=-1)
        add=SimpleNamespace(kind=5,identity=0,label='wave#1',run=0)
        with self.assertRaises(ValueError):pack([],[body])
        self.assertEqual(pack([],[body],allow_empty=True)[2],0)
        with self.assertRaisesRegex(ValueError,'Every configured ADD'):pack([],[body,add],allow_empty=True)
        block=array.array('I',[0])*OUTPUT;block[L['WORLD_SKILL_HEAD_BASE']]=0x57534b31
        spec=normalize_product(dict(coord={'auto_aim':[0.,0.]},logical_geometry=[]))
        metadata={'binding_source_indices':[0],'product_coordinate':{'declarations':{'coordinate':spec}}}
        self.assertEqual(read_result(block,metadata)['coordinate']['logical_colliders'],0)
        block[1769856]=1
        with self.assertRaisesRegex(UnsupportedPortable,'coordinate product history'):read_result(block,metadata)

    def test_combined_enemy_healing_magazines_preserve_shared_owners_and_disjoint_banks(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_enemy_healing_wire import AMMO_LAYOUT as H,AMMO_OUTPUT as HO,check_ammo_schema,MAGIC as HM
        from portable_enemy_ammo_wire import LAYOUT as E,MAGIC as EM
        from portable_enemy_ammo_self_destruct_wire import LAYOUT as S
        from portable_cover_defense_wire import LAYOUT as C
        from portable_backend import validate_composed_stride
        check_ammo_schema()
        self.assertEqual(H['BASE']+H['WORDS'],115680)
        self.assertEqual(S['OUTPUT_BASE']+S['HEADER']+S['ROWS']*S['ROW_WORDS'],HO['OUTPUT_BASE'])
        self.assertLessEqual(HO['OUTPUT_BASE']+HO['RECEIPT_BASE']+HO['RECEIPTS']*HO['RECEIPT_WORDS'],C['OUTPUT_BASE'])
        for variant,body in cases_for_program(ROOT,'ammo-cover-fixed-group'):
            if not variant or not variant.startswith('healing-'):continue
            original=copy.deepcopy(body)
            for mode in ('fixed','accumulate'):
                body=copy.deepcopy(original);body['burst_gauge_mode']=mode
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU state as input')):
                    prepared,_=prepare(body);before=copy.deepcopy(prepared);source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(prepared,before);validate_composed_stride(source,iw,ow)
                self.assertEqual(iw,E['INPUT_WORDS']+C['WORDS']);self.assertEqual(words[H['BASE']],HM);self.assertEqual(words[E['BASE']],EM)
                self.assertEqual(meta['product_enemy_healing']['declarations'],{'enemy_healing':body['reference_models']['enemy_healing']})
                self.assertEqual(meta['product_enemy_ammo']['declarations'],{'enemy_ammo':body['reference_models']['enemy_ammo']})
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                self.assertTrue(meta['product_ammo_healing']);self.assertFalse(meta['product_enemy_healing']['cpu_health_generations_or_schedule_supplied'])

    def test_combined_healing_and_ammo_native_frame_and_final_queue_agree(self):
        from portable_product_programs import cases_for_program
        original=timeline.BossScript
        for variant,body in cases_for_program(ROOT,'ammo-cover-fixed-group'):
            if not variant or not variant.startswith('healing-'):continue
            result=engine_worker.evaluate(body)['reference_models']
            receipts=result['enemy_healing']['receipts'];ammo=result['enemy_ammo']
            self.assertTrue(receipts);self.assertTrue(ammo['charges']);self.assertIs(timeline.BossScript,original)
            if variant=='healing-magazines':self.assertTrue(any(r.get('applied',0)>0 for r in receipts))
            else:
                self.assertEqual(len(ammo['retirements']),2)
                self.assertTrue(any(r['status']=='dead-or-inactive' for r in receipts))
                self.assertTrue(any(a.get('retired_queue') for a in ammo['attempts']))

    def test_enemy_ammo_target_modifiers_keep_complete_target_and_group_prefixes(self):
        from portable_product_programs import body_for_program,cases_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            bodies=[body_for_program(ROOT,'ammo-'+mode+'-target'),body_for_program(ROOT,'ammo-cover-'+mode+'-target')]
            for variant,body in cases_for_program(ROOT,'ammo-cover-fixed-group'):
                if variant and variant.startswith('target-modifier'):
                    body['burst_gauge_mode']=mode;bodies.append(body)
            for body in bodies:
                original=copy.deepcopy(body)
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU schedule input')):
                    prepared,_=prepare(body);before=copy.deepcopy(prepared);source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(body,original);self.assertEqual(prepared,before);validate_composed_stride(source,iw,ow)
                axes=meta['real_prepared_input']['target_modifier_carriers'];self.assertEqual(axes['original_effects'],prepared['effects'])
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                grouped=bool(meta['real_prepared_input'].get('declared_attack_group_policy'))
                end=104672 if grouped else 110112
                self.assertFalse(any(words[end:A['BASE']]))
                if grouped:self.assertEqual(words[104408:104410],[0x50474131,1])
                for row,axis in enumerate(axes['axis_rows']):
                    if axis:
                        at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];self.assertEqual(words[at+F['KIND']],4);self.assertEqual(words[at+F['STAT']],0)
                missing=copy.deepcopy(body);missing['reference_models'].pop('enemy_ammo')
                with patch.object(sim,'execute',side_effect=AssertionError('Reject before battle')):
                    with self.assertRaisesRegex(UnsupportedPortable,'explicit.*magazines'):
                        pre,_=prepare(missing);compile_product(pre)

    def test_enemy_ammo_self_destruct_uses_existing_finite_rows_and_magazine_bank(self):
        from portable_enemy_ammo_self_destruct_cases import fixtures
        from portable_detail import prepare,compile_product
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_enemy_ammo_wire import LAYOUT as E
        for case in fixtures():
            body=copy.deepcopy(case['body']);body['reference_models']={'enemy_ammo':case['enemy_ammo']}
            original=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU schedule as GPU input')):
                prepared,_=prepare(body);source,iw,ow,words,meta=compile_product(prepared)
            self.assertEqual(body,original);self.assertTrue(meta['product_enemy_ammo']['self_destruct'])
            self.assertEqual((iw,ow),(E['INPUT_WORDS'],E['OUTPUT_WORDS']))
            self.assertEqual(words[A['BASE']+A['ROW_BASE']+4],1)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
        body['enemy']['patterns'][0]['spec']['attack']['hits']=0
        with patch.object(sim,'execute',side_effect=AssertionError('Reject before battle')):
            with self.assertRaisesRegex(ValueError,'hits'):
                prepared,_=prepare(body);compile_product(prepared)

    def test_declared_product_ammo_reuses_exact_native_final_queue_lifecycle(self):
        from portable_enemy_ammo_self_destruct_cases import fixtures
        original=timeline.BossScript
        for case in fixtures():
            if case['contract']['scenario'] not in ('coincident','reload-final','hp-before-shot','time-close','renewal'):continue
            body=copy.deepcopy(case['body']);body['reference_models']={'enemy_ammo':case['enemy_ammo']}
            result=engine_worker.evaluate(body)['reference_models']['enemy_ammo']
            if case['contract']['scenario'] in ('hp-before-shot','time-close'):
                self.assertNotIn('retirements',result);self.assertFalse(result['attempts'])
            else:
                self.assertTrue(result['retirements'])
                self.assertTrue(any(a.get('retired_queue') for a in result['attempts']))
                if case['contract']['scenario']=='coincident':
                    self.assertTrue(all(r['queued_indices']==[0,1,2] for r in result['retirements']))
                if case['contract']['scenario']=='reload-final':
                    self.assertTrue(any(a.get('retired_queue') and a['status']=='reloading' for a in result['attempts']))
                if case['contract']['scenario']=='renewal':
                    self.assertEqual({r['actor'][2] for r in result['retirements']},{1,2})
            self.assertIs(timeline.BossScript,original)

    def test_final_queue_readback_rejects_unowned_or_unmatched_retirement_data(self):
        from portable_enemy_ammo_readback import read_retirements
        from portable_enemy_ammo_self_destruct_wire import LAYOUT as S,MAGIC
        words=array.array('I',[0])*S['OUTPUT_WORDS'];head=S['OUTPUT_BASE'];words[head]=MAGIC
        self.assertEqual(read_retirements(words,{'patterns':[]},[],[]),[])
        for at in (head+3,head+S['HEADER'],head+1):
            bad=array.array('I',words);bad[at]=1
            with self.subTest(at=at),self.assertRaises(AssertionError):read_retirements(bad,{'patterns':[]},[],[])

    def test_enemy_ammo_shot_groups_keep_original_definitions_and_both_literal_banks(self):
        from portable_runtime import UnsupportedPortable
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from portable_enemy_ammo_wire import LAYOUT as E,MAGIC
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_cover_defense_wire import LAYOUT as C,MAGIC as COVER_MAGIC
        for cover in (False,True):
            for mode in ('fixed','accumulate'):
                name=('ammo-cover-' if cover else 'ammo-')+mode+'-group'
                body=body_for_program(ROOT,name);original=copy.deepcopy(body)
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle as input')):
                    prepared,_=prepare(body);before=copy.deepcopy(prepared)
                    source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(body,original);self.assertEqual(prepared,before)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                self.assertEqual(words[104400:104402],[0x41475331,2])
                self.assertFalse(any(words[104408:A['BASE']]))
                self.assertEqual(words[E['BASE']],MAGIC)
                self.assertEqual(meta['product_enemy_ammo']['declarations'],{'enemy_ammo':body['reference_models']['enemy_ammo']})
                self.assertFalse(meta['product_enemy_ammo']['cpu_state_or_schedule_supplied'])
                self.assertIn('product_add_attacks',meta)
                self.assertEqual(iw,E['INPUT_WORDS']+(C['WORDS'] if cover else 0))
                self.assertEqual(iw,len(words));validate_composed_stride(source,iw,ow)
                self.assertEqual(source,'gpu/product_'+('ammo_cover_' if cover else 'ammo_')+('fixed_' if mode=='fixed' else '')+'group_battle_entry.slang')
                if cover:
                    self.assertEqual(words[E['INPUT_WORDS']],COVER_MAGIC)
                    self.assertEqual(meta['product_cover_defense']['declarations'],{'cover_defense':body['reference_models']['cover_defense']})
                missing=copy.deepcopy(body);missing['reference_models'].pop('enemy_ammo')
                with patch.object(sim,'execute',side_effect=AssertionError('Reject before CPU battle')):
                    with self.assertRaisesRegex(UnsupportedPortable,'explicit.*magazines'):
                        missing_prepared,_=prepare(missing);compile_product(missing_prepared)

    def test_healing_group_preserves_original_effects_and_shared_wire(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from portable_enemy_healing_wire import LAYOUT as H,INPUT_WORDS,OUTPUT
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'healing-'+mode+'-group');original=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,_=prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,metadata=compile_product(prepared)
            self.assertEqual(body,original);self.assertEqual(prepared,before)
            self.assertEqual((iw,ow,len(words)),(INPUT_WORDS,OUTPUT['OUTPUT_WORDS'],INPUT_WORDS))
            self.assertEqual(set(metadata['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertEqual(words[104400:104402],[0x41475331,2])
            self.assertTrue(any(t.startswith('multi_hit:') for e in prepared['effects'] for t in e['effect'].get('trigger',{}).get('timing',[])))
            self.assertFalse(any(words[104408:H['BASE']]))
            validate_composed_stride(source,iw,ow)
            self.assertTrue(metadata['product_enemy_healing']['declarations']['enemy_healing'])
            self.assertFalse(metadata['product_enemy_healing']['cpu_health_generations_or_schedule_supplied'])

    @staticmethod
    def movement_range_body():
        from portable_product_programs import body_for_program
        from detail_coverage import body_for
        body=body_for_program(ROOT,'named-range-accumulate')
        motion=body_for_program(ROOT,'movement-accumulate')['reference_models']['enemy_movement']
        squad=body['squad'][:3]+['유니','얀'];body['squad']=squad
        body['profile']=body_for(squad,body['duration'])['profile']
        spec=body['reference_models']['named_range']
        motion['coord']=copy.deepcopy(spec['coord']);motion['logical_geometry']=copy.deepcopy(spec['logical_geometry'])
        motion['motion']['actors']=[dict(label=r['label'],velocity=[.1,0.],force_center=[0.,0.]) for r in spec['logical_geometry']]
        body['reference_models']['enemy_movement']=motion
        return body

    def test_movement_range_cover_retains_all_definitions_and_owned_banks(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_product_movement_range import INPUT,COVER_INPUT,COVER_OUT,COVER_END,OUTPUT
        from portable_cover_defense_wire import MAGIC,COMPOSED_STAT
        from portable_named_range_battle_wire import COUNT_STAT,RANGE_STAT
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L,FIELDS as F
        self.assertEqual(len({COMPOSED_STAT,COUNT_STAT,RANGE_STAT}),3)
        self.assertLessEqual(COVER_END,OUTPUT)
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'movement-range-cover-'+mode);before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,original);self.assertEqual(body,before)
            self.assertEqual((iw,ow,len(words)),(COVER_INPUT,OUTPUT,COVER_INPUT))
            self.assertEqual(words[INPUT],MAGIC)
            self.assertEqual(meta['product_movement_range_cover'],dict(output_base=COVER_OUT,end=COVER_END))
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_cover_defense']['definition_indices'])
            for index in meta['product_cover_defense']['definition_indices']:
                row=meta['binding_source_indices'].index(index)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],COMPOSED_STAT)
            validate_composed_stride(source,iw,ow)
            for bad_i,bad_o in ((iw-1,ow),(iw,ow-1)):
                with self.assertRaises(ValueError):validate_composed_stride(source,bad_i,bad_o)

    def test_three_model_native_consumers_execute_and_restore_contexts(self):
        from portable_product_programs import body_for_program
        body=body_for_program(ROOT,'movement-range-cover-fixed')
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        result=engine_worker.evaluate(body);models=result['reference_models']
        self.assertEqual(set(models['declarations']),{'enemy_movement','named_range','cover_defense'})
        self.assertTrue(models['enemy_movement']['frames'])
        self.assertTrue(models['named_range']['casts'])
        self.assertTrue(models['cover_defense']['receipts'])
        self.assertTrue(any(r['effective_defense']!=r['base_defense'] for r in models['cover_defense']['receipts']))
        self.assertTrue(result['incoming_hits'])
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))
        bad=copy.deepcopy(body['reference_models']);bad['named_range']['coord']['auto_aim'][0]=1.
        with self.assertRaisesRegex(ValueError,'identical declared coordinate geometry'):normalize(bad)

    def test_three_model_decoder_rejects_corrupt_cover_bank_and_unowned_tail(self):
        from portable_product_cover import read_result
        from portable_product_movement_range import read_result as read_combined,COVER_OUT,COVER_END,OUTPUT
        from portable_cover_defense_wire import MAGIC
        names=['a','b','c','d','e'];words=array.array('I',[0])*OUTPUT;words[COVER_OUT]=MAGIC
        meta=dict(product_cover_defense=dict(declarations={'cover_defense':[dict(name=n,base_defense=100) for n in names]}),
                  product_movement_range_cover=dict(output_base=COVER_OUT,end=COVER_END))
        self.assertEqual(read_result(words,meta,names,30.,out=COVER_OUT,output=OUTPUT)['cover_defense']['receipts'],[])
        for at in (COVER_OUT+16,COVER_END-1):
            words[at]=1
            with self.assertRaises(ValueError):read_result(words,meta,names,30.,out=COVER_OUT,output=OUTPUT)
            words[at]=0
        with patch('portable_product_movement.read_result',return_value={}),patch('portable_product_named_range.read_result',return_value={}):
            self.assertEqual(read_combined(words,meta,30.),[{},{}])
            words[COVER_END]=1
            with self.assertRaises(ValueError):read_combined(words,meta,30.)
            words[COVER_END]=0
            bad=copy.deepcopy(meta);bad['product_movement_range_cover']['end']-=1
            with self.assertRaises(ValueError):read_combined(words,bad,30.)

    def test_movement_range_keeps_all_definitions_and_disjoint_literal_banks(self):
        import portable_detail as product
        from portable_product_movement_range import INPUT,OUTPUT,OUT,END,CAPACITY,check_schema
        from portable_enemy_movement_wire import INPUT as MI,BASE as MB,END as ME,MAGIC as MM
        from portable_named_range_battle_wire import WORDS as RW,MAGIC as RM
        from portable_backend import validate_composed_stride
        self.assertGreater(OUT,ME);self.assertEqual(CAPACITY,8192);self.assertEqual(INPUT,MI+RW);self.assertLessEqual(END,OUTPUT);check_schema(ROOT)
        for mode in ('fixed','accumulate'):
            body=self.movement_range_body();body['burst_gauge_mode']=mode;before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,run=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,original);self.assertEqual(body,before);self.assertFalse(run.expected)
            self.assertEqual((iw,ow,len(words)),(INPUT,OUTPUT,INPUT));validate_composed_stride(source,iw,ow)
            self.assertEqual(words[MB],MM);self.assertEqual(words[MI],RM)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertEqual(set(meta['product_enemy_movement']['declarations']),{'enemy_movement'})
            self.assertEqual(set(meta['product_named_range']['declarations']),{'named_range'})
            self.assertFalse(meta['product_movement_range']['cpu_state_or_schedule_supplied'])
            with self.assertRaises(ValueError):validate_composed_stride(source,iw-1,ow)
            with self.assertRaises(ValueError):validate_composed_stride(source,iw,ow-1)

    def test_movement_range_native_range_reads_the_current_moving_colliders(self):
        body=self.movement_range_body();body['squad'][2],body['squad'][4]=body['squad'][4],body['squad'][2]
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        result=engine_worker.evaluate(body);models=result['reference_models']
        self.assertTrue(models['named_range']['casts'])
        self.assertEqual(models['named_range']['casts'][0]['body_position'],0)
        self.assertEqual(models['named_range']['casts'][0]['add_count'],2)
        self.assertTrue(any(s['forced'] for f in models['enemy_movement']['frames'] for s in f['segments']))
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))

    def test_movement_range_rejects_disagreeing_geometry_and_restores_aliases(self):
        body=self.movement_range_body();models=normalize(body['reference_models'])
        for key in ('coord','logical_geometry'):
            bad=copy.deepcopy(body['reference_models'])
            if key=='coord':bad['named_range'][key]['auto_aim'][0]=1.
            else:bad['named_range'][key][0]['shape']['x']=1.
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'identical declared coordinate geometry'):normalize(bad)
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with execution(models):raise RuntimeError('injected')
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))
        with self.assertRaisesRegex(ValueError,'combined checked'):normalize(dict(body['reference_models'],enemy_healing=[]))

    def test_movement_and_manual_cover_share_literal_banks_and_restore_native_contexts(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_enemy_movement_wire import INPUT as M,OUTPUT as MO
        from portable_cover_defense_wire import LAYOUT as C,MAGIC
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        self.assertEqual(MO,C['OUTPUT_BASE'])
        aliases=(timeline.simulate,sim.simulate);state=timeline.random.getstate()
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'movement-cover-'+mode)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle as input')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow,len(words)),(M+24,2048912,M+24))
            self.assertEqual(words[M:M+4],[MAGIC,1,5,1])
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],6 if mode=='fixed' else 3)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_movement_cover'])
            self.assertEqual(meta['product_manual_cover_owners'],[0])
            for bad in [(iw-24,ow),(iw,MO)]:
                with self.assertRaises(ValueError):validate_composed_stride(source,*bad)
            body['duration']=4
            body['manual_cover_sequences']={body['squad'][0]:[dict(action='cover',t=0,duration=4)]}
            body['enemy']['patterns'].append(dict(id='body-attacks',kind='attack',spec=dict(atk=1000,coeff=100,target='all',hits=3,interval=1.)))
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle in missing-base rejection')):
                pre,_=product.prepare(body)
                with self.assertRaisesRegex(UnsupportedPortable,'explicit.*cover_defense'):product.compile_product(pre)
            body['reference_models']['cover_defense']=[dict(name=n,base_defense=100.) for n in body['squad']]
            original=copy.deepcopy(body);actual=engine_worker.evaluate(body)
            self.assertEqual(body,original)
            self.assertEqual(set(actual['reference_models']['declarations']),{'enemy_movement','cover_defense'})
            self.assertTrue(actual['reference_models']['enemy_movement']['frames'])
            self.assertTrue(actual['reference_models']['cover_defense']['receipts'])
            self.assertEqual(actual['manual_cover_sequences'],body['manual_cover_sequences'])
            self.assertEqual(aliases,(timeline.simulate,sim.simulate));self.assertEqual(timeline.random.getstate(),state)

    def test_composed_stat_alias_is_rejected_before_gpu_even_without_incoming(self):
        import portable_detail as product
        import portable_cover_defense_wire as cover
        from portable_product_programs import body_for_program
        for incoming in (False,True):
            body=body_for_program(ROOT,'named-range-cover-fixed')
            if not incoming:body['enemy']['patterns']=[p for p in body['enemy']['patterns'] if p['kind']!='attack']
            pre,_=product.prepare(body)
            for collision in (93,94):
                with patch.object(cover,'COMPOSED_STAT',collision),patch.object(product,'execute',side_effect=AssertionError('GPU forbidden')):
                    with self.assertRaisesRegex(ValueError,'disjoint stat identifiers'):product.compile_product(pre)

    def test_named_range_and_manual_cover_share_literal_banks_and_restore_native_contexts(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_named_range_battle_wire import INPUT as M,OUTPUT as MO
        from portable_cover_defense_wire import LAYOUT as C,MAGIC
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        self.assertEqual(MO,C['OUTPUT_BASE'])
        aliases=(timeline.simulate,sim.simulate);state=timeline.random.getstate()
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'named-range-cover-'+mode)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle as input')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow,len(words)),(M+24,2048912,M+24))
            self.assertEqual(words[M:M+4],[MAGIC,1,5,0])
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],6 if mode=='fixed' else 3)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_named_range_cover'])
            self.assertEqual(meta['product_manual_cover_owners'],[0])
            for bad in [(iw-24,ow),(iw,MO)]:
                with self.assertRaises(ValueError):validate_composed_stride(source,*bad)
            from portable_cover_defense_wire import NAMED_RANGE_STAT
            from portable_specs import FIELDS as F
            self.assertIn('PORTABLE_COVER_DEFENSE_STAT '+str(NAMED_RANGE_STAT)+'U',(ROOT/'gpu/product_named_range_cover_battle_entry.slang').read_text())
            self.assertNotEqual(NAMED_RANGE_STAT,93)
            for index in meta['product_cover_defense']['definition_indices']:
                row=meta['binding_source_indices'].index(index)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],NAMED_RANGE_STAT)
            body['reference_models'].pop('cover_defense')
            body['duration']=15
            body['manual_cover_sequences']={body['squad'][1]:[dict(action='cover',t=0,duration=15)]}
            body['enemy']['patterns'].append(dict(id='body-attacks',kind='attack',spec=dict(atk=1000,coeff=100,target='all',hits=3,interval=1.)))
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle in missing-base rejection')):
                pre,_=product.prepare(body)
                with self.assertRaisesRegex(UnsupportedPortable,'explicit.*cover_defense'):product.compile_product(pre)
            body['reference_models']['cover_defense']=[dict(name=n,base_defense=100.) for n in body['squad']]
            original=copy.deepcopy(body);actual=engine_worker.evaluate(body)
            self.assertEqual(body,original)
            self.assertEqual(set(actual['reference_models']['declarations']),{'named_range','cover_defense'})
            self.assertTrue(actual['reference_models']['named_range']['casts'])
            self.assertTrue(actual['reference_models']['cover_defense']['receipts'])
            self.assertEqual(actual['manual_cover_sequences'],body['manual_cover_sequences'])
            self.assertEqual(aliases,(timeline.simulate,sim.simulate));self.assertEqual(timeline.random.getstate(),state)

    def test_enemy_ammo_cover_preserves_complete_banks_and_requires_each_literal_model(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_enemy_ammo_wire import LAYOUT as A,MAGIC as AM
        from portable_cover_defense_wire import LAYOUT as C,MAGIC as CM
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        self.assertEqual(A['OUTPUT_WORDS'],C['OUTPUT_BASE'])
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'ammo-cover-'+mode)
            before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                prepared,_=product.prepare(body);old=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual((body,prepared),(before,old))
            validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow,len(words)),(117656,2048912,117656))
            self.assertEqual(words[A['BASE']:A['BASE']+4],[AM,1,0,1])
            self.assertEqual(words[A['INPUT_WORDS']:A['INPUT_WORDS']+4],[CM,1,5,1])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_ammo_cover'])
            self.assertFalse(meta['product_enemy_ammo']['cpu_state_or_schedule_supplied'])
            self.assertFalse(meta['product_cover_defense']['cpu_state_or_schedule_supplied'])
            for bad in [(iw-24,ow),(iw,ow-1)]:
                with self.assertRaises(ValueError):validate_composed_stride(source,*bad)
            body['enemy']['patterns']=[dict(id='attempt',kind='attack',spec=dict(atk=1000,coeff=100,target='all',hits=3,interval=1.))]
            magazine=[dict(label='__enemy__',capacity=4,initial=4,reload_seconds=1.,cancel_on_full=True)]
            covers=[dict(name=n,base_defense=100.) for n in body['squad']]
            # Each consumer must independently refuse missing quantities.
            for declarations,reason in [({'enemy_ammo':magazine},'explicit.*cover_defense'),({'cover_defense':covers},'explicit.*magazines')]:
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                    pre,_=product.prepare(dict(body,reference_models=declarations))
                    with self.assertRaisesRegex(UnsupportedPortable,reason):product.compile_product(pre)
            combined={'enemy_ammo':magazine,'cover_defense':covers}
            self.assertEqual(normalize(combined),combined)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                pre,_=product.prepare(dict(body,reference_models=combined));s,wi,wo,w,m=product.compile_product(pre)
            self.assertEqual((s,wi,wo),(source,iw,ow))
            self.assertEqual(w[A['BASE']:A['BASE']+4],[AM,1,1,1])
            self.assertEqual(w[A['INPUT_WORDS']:A['INPUT_WORDS']+4],[CM,1,5,0])
            self.assertEqual(m['product_enemy_ammo']['declarations'],{'enemy_ammo':magazine})
            self.assertEqual(m['product_cover_defense']['declarations'],{'cover_defense':covers})

    def test_independent_public_models_merge_losslessly_and_reject_overwrite(self):
        from product_reference_models import combine_public,warning,WARNING,COVER_WARNING
        a=dict(schema=1,evidence='declared-model-not-game-verification',declarations={'enemy_healing':[{'node':'heal'}]},enemy_healing={'receipts':[{'applied':2}]})
        b=dict(schema=1,evidence=a['evidence'],declarations={'cover_defense':[{'name':'a'}]},cover_defense={'receipts':[{'applied':3}]})
        before=copy.deepcopy([a,b]);joined=combine_public([a,b])
        self.assertEqual(set(joined['declarations']),{'enemy_healing','cover_defense'})
        self.assertEqual(joined['enemy_healing'],a['enemy_healing']);self.assertEqual(joined['cover_defense'],b['cover_defense'])
        self.assertEqual(warning(joined['declarations']),WARNING+' '+COVER_WARNING)
        joined['enemy_healing']['receipts'][0]['applied']=99
        self.assertEqual([a,b],before)
        with self.assertRaisesRegex(ValueError,'overwrite'):combine_public([a,a])
        for bad in [dict(a,schema=True),dict(a,evidence='verified'),{k:v for k,v in a.items() if k!='enemy_healing'}]:
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'Complete independent'):combine_public([bad])

    def test_enemy_healing_and_cover_keep_both_banks_and_original_effects(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_enemy_healing_wire import INPUT_WORDS as H,OUTPUT as HO
        from portable_cover_defense_wire import LAYOUT as C,MAGIC
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L,FIELDS as F
        self.assertEqual(HO['OUTPUT_WORDS'],C['OUTPUT_BASE'])
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'healing-cover-'+mode)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU state supplied to GPU')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_healing_cover_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow),(H+C['WORDS'],2048912));self.assertEqual(len(words),iw)
            self.assertEqual(words[H:H+4],[MAGIC,1,5,1])
            self.assertEqual(words[115680:115682],[0x45484c31,1])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_healing_cover'])
            self.assertIn('product_enemy_healing',meta);self.assertIn('product_cover_defense',meta)
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],6 if mode=='fixed' else 3)
            # Ann's original revive enables lazy markers in the common
            # compiler. Once the cover placeholder becomes numeric kind0,
            # only that obsolete marker bit must be removed.
            self.assertTrue(any(r['effect'].get('stat')=='revive' for r in prepared['effects']))
            for index in meta['product_cover_defense']['definition_indices']:
                row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                self.assertEqual(words[at+F['KIND']],0)
                self.assertFalse(words[at+F['FLAGS']]&2048)

    def test_healing_cover_and_original_shot_groups_preserve_all_three_consumers(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_backend import validate_composed_stride
        from portable_enemy_healing_wire import INPUT_WORDS as H,OUTPUT as HO
        from portable_cover_defense_wire import LAYOUT as C,MAGIC
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'healing-cover-'+mode+'-group')
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU state supplied')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_healing_cover_'+('fixed_' if mode=='fixed' else '')+'group_battle_entry.slang')
            validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow),(H+C['WORDS'],C['OUTPUT_WORDS']))
            self.assertEqual(words[H:H+4],[MAGIC,1,5,0])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertTrue(meta['product_healing_cover'])
            self.assertEqual(HO['OUTPUT_WORDS'],C['OUTPUT_BASE'])
            self.assertEqual(words[115680:115683],[0x45484c31,1,4])
            # The actual-shot descriptor belongs to the unchanged group prefix,
            # not the zero-reserved padding before the healing bank.
            self.assertTrue(any(words[104400:104408]))
            self.assertEqual(meta['product_enemy_healing']['declarations']['enemy_healing'],body['reference_models']['enemy_healing'])
            self.assertEqual(meta['product_cover_defense']['declarations'],{'cover_defense':body['reference_models']['cover_defense']})

    def lock_body(self,duration=3,typed=False):
        from portable_heavyarms_lock_cases import fixtures,NAME,source_definitions
        from product_lock_model import ORDER,MARKER,DELIVERY_MODEL
        with patch.object(sys,'path',list(sys.path)):body=copy.deepcopy(fixtures()[0]['body'])
        body['duration']=duration
        bindings=[]
        if typed:
            body['enemy']['patterns']=[dict(id='declared-projectiles',kind='idle',until=dict(time=duration))]
            bindings=[dict(node='declared-projectiles',kind=2,identity=11,capacity=1e8)]
        body['reference_models']={'lock_on':dict(owner=NAME,marker=MARKER,packet_skill=source_definitions()[8]['name'],candidate_order=ORDER,delivery=DELIVERY_MODEL,typed_bindings=bindings)}
        return body

    def test_lock_on_original_product_keeps_all_definitions_and_empty_typed_world(self):
        import portable_detail as product
        from portable_backend import validate_composed_stride
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate());paths=list(sys.path);body=self.lock_body();original=copy.deepcopy(body)
        with patch.object(sim,'execute',side_effect=AssertionError('No CPU lock selection before GPU')):
            prepared,run=product.prepare(body);before=copy.deepcopy(prepared);source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual((source,iw,ow,len(words)),('gpu/product_lock_battle_entry.slang',109536,2032000,109536))
        validate_composed_stride(source,iw,ow)
        with self.assertRaises(ValueError):validate_composed_stride(source,iw,ow-1)
        self.assertEqual(prepared,before);self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
        from portable_heavyarms_lock_cases import source_definitions
        own=[r['effect'] for r in prepared['effects'] if r['owner']==body['reference_models']['lock_on']['owner']]
        self.assertTrue(all(effect in own for effect in source_definitions()));self.assertEqual(len(source_definitions()),25)
        self.assertEqual(words[104400+2320],0);self.assertFalse(meta['product_lock_on']['cpu_state_or_schedule_supplied'])
        with patch.object(sys,'setprofile',side_effect=AssertionError('Product must not install a profiler')):
            result=engine_worker.evaluate(body)
        locks=result['reference_models']['lock_on'];self.assertEqual(len(locks['pulses']),12);self.assertEqual(len(locks['shots']),2)
        self.assertEqual(locks['typed'],dict(time=3,finished=True,state=[],attacks=[]));self.assertTrue(all(r['handles']==[[0,0,1]] for r in locks['shots']))
        self.assertEqual(body,original);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()));self.assertEqual(sys.path,paths)

    def test_lock_on_actual_projectile_consumer_uses_literal_binding_and_restores_aliases(self):
        import portable_detail as product
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate());body=self.lock_body(30,True)
        prepared,_=product.prepare(body);_,_,_,words,meta=product.compile_product(prepared)
        self.assertEqual(words[104400+2320],1);self.assertEqual(words[104400+2328:104400+2331],[0,2,11])
        result=engine_worker.evaluate(body)['reference_models']['lock_on'];self.assertTrue(result['typed']['attacks'])
        self.assertEqual(len(result['typed']['state']),1);self.assertTrue(all(r['completed'] for r in result['typed']['attacks']))
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))

    def test_lock_on_standalone_cpu_worker_resolves_providers_before_checked_rewrites(self):
        import json,subprocess
        for typed in (False,True):
            body=self.lock_body(3,typed);body['action']='evaluate'
            process=subprocess.run([sys.executable,str(ROOT/'app/engine_worker.py')],input=json.dumps(body),text=True,capture_output=True,cwd=ROOT,timeout=30)
            self.assertEqual(process.returncode,0,process.stderr+process.stdout)
            result=json.loads(process.stdout);self.assertNotIn('error',result)
            self.assertEqual(len(result['reference_models']['lock_on']['shots']),2)
            self.assertEqual(len(result['reference_models']['lock_on']['typed']['state']),int(typed))
            script="import sys,json;sys.path.insert(0,'app');import portable_detail as p;from unittest.mock import patch;body=json.load(sys.stdin)\nwith patch.object(p.engine_worker.sim,'execute',side_effect=AssertionError('No native input')):prepared,run=p.prepare(body);source,iw,ow,words,meta=p.compile_product(prepared)\nprint(json.dumps(dict(source=source,words=len(words),iw=iw)))"
            process=subprocess.run([sys.executable,'-c',script],input=json.dumps(body),text=True,capture_output=True,cwd=ROOT,timeout=30)
            self.assertEqual(process.returncode,0,process.stderr+process.stdout)
            self.assertEqual(json.loads(process.stdout),dict(source='gpu/product_lock_battle_entry.slang',words=109536,iw=109536))

    def test_lock_on_invalid_policies_bindings_composition_and_source_fail_closed(self):
        import portable_detail as product
        from portable_runtime import UnsupportedPortable
        from product_lock_model import QueueHooks
        body=self.lock_body();spec=body['reference_models']['lock_on'];aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        for change in (dict(candidate_order='nearest'),dict(delivery='retarget'),dict(typed_bindings=[dict(node='x',kind=2,identity=0,capacity=0)]),dict(owner='absent')):
            bad=copy.deepcopy(body);bad['reference_models']['lock_on'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):engine_worker.evaluate(bad)
            self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))
        with self.assertRaisesRegex(ValueError,'combined checked'):normalize({'lock_on':spec,'enemy_healing':[]})
        prepared,_=product.prepare(body)
        authored=copy.deepcopy(prepared);authored['reference_models']={};authored['enemy']['patterns']=[dict(id='future-target',kind='summon',delay=5.,spec=dict(count=1,hp=1e8))]
        with self.assertRaisesRegex(UnsupportedPortable,'explicit reference_models.lock_on'):product.compile_product(authored)
        changed=copy.deepcopy(prepared);next(r['effect'] for r in changed['effects'] if r['effect'].get('stat')=='lock_on')['duration']=1
        with self.assertRaisesRegex(ValueError,'Unchanged original'):product.compile_product(changed)
        import ast
        transform=QueueHooks();transform.visit(ast.parse('def simulate():\n def _land(ev,t):\n  if boss is not None and boss.has_adds:pass\n'))
        self.assertNotEqual(transform.counts,dict(emission=1,landing=1,route=1,clock=1))

    def test_complete_skill_pages_keep_129_and_2048_rows_and_reject_extra_words(self):
        from portable_skill_history import decode_pages
        from portable_product_locks import COVER_SKILL_BASE,COVER_SKILL_END,COVER_HISTORY_CAPACITY,check_cover_history
        from portable_specs import LIMITS as L
        check_cover_history(ROOT)
        for count in (129,COVER_HISTORY_CAPACITY):
            block=array.array('I',[0])*COVER_SKILL_END
            h=L['WORLD_SKILL_HEAD_BASE'];block[h:h+3]=array.array('I',[0x57534b31,count,1])
            for i in range(count):
                at=L['WORLD_SKILL_TRACE_BASE']+i*48 if i<128 else COVER_SKILL_BASE+(i-128)*48
                block[at:at+4]=array.array('I',[7,1,1,1])
                for off in (4,6,8,10):block[at+off:at+off+2]=array.array('I',struct.unpack('<II',struct.pack('<d',i/1000.)))
                block[at+12]=1;block[at+16]=1
            with patch('importlib.util.spec_from_file_location',side_effect=AssertionError('Product history must not import verification entries')):
                rows=decode_pages(block,count,COVER_SKILL_BASE)
            self.assertEqual(len(rows),count);self.assertEqual(rows[-1]['landed'],(count-1)/1000.)
            # Corruption after the original128-row prefix must be observed.
            block[COVER_SKILL_BASE+17]=1
            with self.assertRaises(AssertionError):decode_pages(block,count,COVER_SKILL_BASE)
            block[COVER_SKILL_BASE+17]=0
            if count<COVER_HISTORY_CAPACITY:
                block[COVER_SKILL_BASE+(count-128)*48]=1
                with self.assertRaisesRegex(ValueError,'Unused'):decode_pages(block,count,COVER_SKILL_BASE)
        with self.assertRaises(ValueError):decode_pages(block,COVER_HISTORY_CAPACITY+1,COVER_SKILL_BASE)
        with self.assertRaises(ValueError):decode_pages(block[:-1],COVER_HISTORY_CAPACITY,COVER_SKILL_BASE)

    def test_lock_and_cover_keep_all_original_effects_and_independent_arenas(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_lock_typed_layout import INPUT as LI,OUTPUT as LO
        from portable_cover_defense_wire import LAYOUT as C,COMPOSED_STAT
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_backend import validate_composed_stride
        aliases=(timeline.simulate,sim.simulate);state=timeline.random.getstate()
        self.assertLess(LO,C['OUTPUT_BASE'])
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'lock-cover-'+mode)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle as GPU input')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);validate_composed_stride(source,iw,ow)
            self.assertEqual((iw,ow,len(words)),(LI+24,2048912,LI+24))
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],6 if mode=='fixed' else 3)
            self.assertTrue(meta['product_lock_cover'])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            for index in meta['product_cover_defense']['definition_indices']:
                row=meta['binding_source_indices'].index(index)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],COMPOSED_STAT)
            for short in [(LI,ow),(iw,LO)]:
                with self.assertRaises(ValueError):validate_composed_stride(source,*short)
            body['duration']=3
            body['manual_cover_sequences']={body['squad'][0]:[dict(action='cover',t=.5,duration=1)]}
            body['enemy']['patterns'][1]['delay']=.75
            body['enemy']['patterns'][1]['spec'].update(hits=2,interval=.5)
            original=copy.deepcopy(body);actual=engine_worker.evaluate(body)
            self.assertEqual(body,original)
            self.assertEqual(set(actual['reference_models']['declarations']),{'lock_on','cover_defense'})
            self.assertTrue(actual['reference_models']['cover_defense']['receipts'])
            self.assertIn('lock_on',actual['reference_models'])
            self.assertEqual(aliases,(timeline.simulate,sim.simulate));self.assertEqual(timeline.random.getstate(),state)

    def test_fixed_lock_uses_shared_literal_header_and_preserves_all_effects(self):
        import portable_detail as product
        from portable_backend import validate_composed_stride
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        body=self.lock_body(30,True);body['burst_gauge_mode']='fixed'
        with patch.object(sim,'execute',side_effect=AssertionError('No native battle in fixed input')):
            prepared,_=product.prepare(body);prepared['policies']['config']['first_burst_time']=.75;before=copy.deepcopy(prepared)
            source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(source,'gpu/product_lock_fixed_battle_entry.slang');validate_composed_stride(source,iw,ow)
        self.assertEqual(prepared,before);self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
        self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],4)
        self.assertEqual(meta['real_prepared_input']['policy'],prepared['policies'])
        self.assertEqual(meta['product_fixed_burst']['first_seconds'],.75)
        self.assertFalse(meta['product_fixed_burst']['CPU_state_or_schedule_as_input'])
        bad=copy.deepcopy(prepared);bad['chars'][0]['control']={'sequence':[{'action':'cover'}]}
        with self.assertRaisesRegex(UnsupportedPortable,'control policy'):product.compile_product(bad)
        for value in (True,float('nan'),-1,181):
            bad=copy.deepcopy(prepared);bad['policies']['config']['first_burst_time']=value
            with self.subTest(value=value),self.assertRaisesRegex(UnsupportedPortable,'finite binary64'):product.compile_product(bad)

    def test_lock_on_decoder_checks_complete_arenas_and_reserved_words(self):
        import portable_detail as product
        from portable_product_locks import read_result
        from portable_original_lock_layout import PRODUCT_OUTPUT as OUTPUT
        from portable_specs import LIMITS as L
        from portable_lock_typed_layout import OFFSET
        from portable_physical_lock_layout import HEAD
        from portable_lock_packet_layout import HEAD as PACKET_HEAD,MAGIC
        from portable_effect_target_count_shot_specs import HEAD as QUOTA_HEAD,MAGIC as QUOTA_MAGIC
        from portable_packet_fates import HEAD as FATE_HEAD,MAGIC as FATE_MAGIC
        from portable_runtime import UnsupportedPortable
        prepared,_=product.prepare(self.lock_body());_,_,_,_,meta=product.compile_product(prepared)
        b=array.array('I',[0])*OUTPUT;owner=meta['product_lock_on']['names'].index(meta['product_lock_on']['declarations']['lock_on']['owner'])
        b[HEAD+OFFSET]=0x504c3031;b[HEAD+OFFSET+4]=owner;b[HEAD+OFFSET+5]=meta['physical_lock_pulse_row']
        marker=meta['named_count_physical']['marker'];b[QUOTA_HEAD:QUOTA_HEAD+6]=array.array('I',[QUOTA_MAGIC,1,0,meta['states'][marker],5,128])
        b[L['WORLD_SKILL_HEAD_BASE']]=0x57534b31
        b[PACKET_HEAD+OFFSET]=MAGIC;b[FATE_HEAD]=FATE_MAGIC;b[786432]=0x44425431
        b[789250:789253]=array.array('I',[1,1,1])
        self.assertEqual(read_result(b,meta,3)['lock_on']['typed'],dict(time=0.,finished=True,state=[],attacks=[]))
        for at,value in ((HEAD+OFFSET+1,1025),(HEAD+OFFSET+6,1),(PACKET_HEAD+OFFSET+1,1),(QUOTA_HEAD+2,8193),(FATE_HEAD+1,1),(OUTPUT-1,1),(787456,1),(789252,0)):
            bad=array.array('I',b);bad[at]=value
            with self.subTest(at=at),self.assertRaises(UnsupportedPortable):read_result(bad,meta,3)
        with self.assertRaises(UnsupportedPortable):read_result(b[:-1],meta,3)

    def test_lock_on_typed_no_expiry_sentinel_is_exact_and_bound_to_declared_target(self):
        import portable_detail as product
        from portable_product_locks import read_result
        from portable_original_lock_layout import PRODUCT_OUTPUT as OUTPUT
        from portable_specs import LIMITS as L
        from portable_lock_typed_layout import OFFSET
        from portable_physical_lock_layout import HEAD
        from portable_lock_packet_layout import HEAD as PACKET_HEAD,MAGIC
        from portable_effect_target_count_shot_specs import HEAD as QUOTA_HEAD,MAGIC as QUOTA_MAGIC
        from portable_packet_fates import HEAD as FATE_HEAD,MAGIC as FATE_MAGIC
        from portable_runtime import UnsupportedPortable
        prepared,_=product.prepare(self.lock_body(3,True));_,_,_,_,meta=product.compile_product(prepared)
        b=array.array('I',[0])*OUTPUT;owner=meta['product_lock_on']['names'].index(meta['product_lock_on']['declarations']['lock_on']['owner'])
        b[HEAD+OFFSET]=0x504c3031;b[HEAD+OFFSET+4]=owner;b[HEAD+OFFSET+5]=meta['physical_lock_pulse_row']
        marker=meta['named_count_physical']['marker'];b[QUOTA_HEAD:QUOTA_HEAD+6]=array.array('I',[QUOTA_MAGIC,1,0,meta['states'][marker],5,128])
        b[L['WORLD_SKILL_HEAD_BASE']]=0x57534b31
        b[PACKET_HEAD+OFFSET]=MAGIC;b[FATE_HEAD]=FATE_MAGIC;b[786432]=0x44425431;b[789250:789253]=array.array('I',[1,1,1])
        at=787456;b[at:at+4]=array.array('I',[2,11,1,0]);b[at+10]=0xffffffff
        def number(offset,value):b[at+offset:at+offset+2]=array.array('I',struct.unpack('<II',struct.pack('<d',value)))
        number(4,1e8);number(6,1e8);number(8,-1.)
        self.assertEqual(read_result(b,meta,3)['lock_on']['typed']['state'][0]['expires'],-1.)
        for offset,value in ((8,-2.),(8,0.),(8,float('nan')),(8,float('inf')),(4,1e8+1),(4,-1.),(6,1e8+1)):
            saved=b[:];number(offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(UnsupportedPortable):read_result(b,meta,3)
            b=saved
        b[at+1]=12
        with self.assertRaises(UnsupportedPortable):read_result(b,meta,3)

    def test_lock_on_manual_control_projection_reads_its_relocated_owned_bank(self):
        from portable_world_result import read_product_control_log
        from portable_specs import LIMITS as L
        from portable_physical_lock_cover_layout import BASE
        from portable_lock_typed_layout import OFFSET,OUTPUT
        from portable_manual_control_specs import BASE as OTHER_BASE
        from portable_runtime import UnsupportedPortable
        names=['a','b','c','d','e'];meta=dict(product_lock_on={'declared':True},product_control_labels=[[] for _ in names],product_manual_cover_owners=[2])
        b=array.array('I',[0])*OUTPUT;h=L['WORLD_CONTROL_HEAD_BASE'];t=L['WORLD_CONTROL_TRACE_BASE']
        b[h]=0x57434831;b[h+1]=2;b[h+13]=0x50434c31
        for i in range(5):b[BASE+OFFSET+i*16+14]=0x504d4331
        for i,(kind,time) in enumerate(((4,.4),(5,.8))):
            at=t+i*8;b[at:at+8]=array.array('I',[kind,2,*struct.unpack('<II',struct.pack('<d',time)),1,0,0,0])
        log=read_product_control_log(b,meta,names,30);self.assertEqual(len(log.control_log),1)
        self.assertEqual((log.control_log[0].t0,log.control_log[0].t1,log.control_log[0].caster),(.4,.8,'c'))
        b[BASE+OFFSET+14]=0
        for i in range(5):b[OTHER_BASE+i*16+14]=0x504d4331
        with self.assertRaises(UnsupportedPortable):read_product_control_log(b,meta,names,30)

    def test_named_range_product_consumes_original_count_and_range_modifiers(self):
        from portable_named_range_battle_cases import fixtures
        from portable_runtime import UnsupportedPortable
        from portable_backend import validate_composed_stride
        import portable_detail as product
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        results={}
        for case in fixtures():
            body=copy.deepcopy(case['body']);body['reference_models']={'named_range':dict(coord=case['coord'],logical_geometry=case['logical_geometry'],rules=case['named_range_rules'])}
            original=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU target selection before GPU')):
                prepared,run=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);self.assertEqual((source,iw,ow),('gpu/product_named_range_battle_entry.slang',116224,2032000))
            validate_composed_stride(source,iw,ow)
            with self.assertRaises(ValueError):validate_composed_stride(source,iw-1,ow)
            self.assertFalse(meta['product_named_range']['cpu_state_or_schedule_supplied']);self.assertFalse(run.expected)
            response=engine_worker.evaluate(body);casts=response['reference_models']['named_range']['casts']
            self.assertFalse(response['expected']);self.assertEqual(body,original)
            self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))
            self.assertTrue(any(c['percent']==500 and c['capacity']==3 for c in casts))
            results[case['contract']['scenario']]=sum(c['add_count'] for c in casts)
            fixed=dict(prepared,policies={**prepared['policies'],'config':{**prepared['policies']['config'],'burst_gauge_mode':'fixed'}})
            fixed_source,fi,fo,fw,fm=product.compile_product(fixed)
            from portable_specs import LIMITS
            base=LIMITS['WORLD_CONTROL_INPUT_BASE']
            self.assertEqual(fixed_source,source.replace('_battle_entry','_fixed_battle_entry'))
            self.assertEqual((fi,fo),(iw,ow));validate_composed_stride(fixed_source,fi,fo)
            self.assertEqual(fw[base+1],6);self.assertEqual(fw[base+5:base+8],words[base+5:base+8])
            self.assertEqual(fw[base+12],0x46424731)
            self.assertEqual(fm['real_prepared_input']['policy'],fixed['policies'])
            self.assertFalse(fm['product_fixed_burst']['CPU_state_or_schedule_as_input'])
        self.assertGreater(results['expanded'],results['small-base-control'])
        self.assertGreater(results['expanded'],results['retirement'])

    def test_fixed_coordinate_header_rejects_noncanonical_and_preserves_literal_fields(self):
        from portable_product_fixed import attach
        from portable_specs import LIMITS
        from portable_runtime import UnsupportedPortable
        base=LIMITS['WORLD_CONTROL_INPUT_BASE'];original=dict(policies={'config':{'burst_gauge_mode':'fixed'}})
        words=[0]*(base+16);words[base:base+8]=[0x57434831,3,0,1,0,2,0xffffffff,0x4d435631]
        for offset,value in [(5,32),(6,256),(7,0),(8,1),(15,1)]:
            bad=words[:];bad[base+offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):attach(bad,{'real_prepared_input':{}},original,(3.,[2.]*5))
        meta={'real_prepared_input':{}};attach(words,meta,original,(3.,[1.,2.,3.,2.,1.]))
        self.assertEqual(words[base+5:base+8],[2,0xffffffff,0x4d435631])
        self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[base+8:base+10]))[0],3.)
        self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[base+10:base+12]))[0],3.)
        self.assertFalse(any(words[base+13:base+16]))

    def test_named_range_unknown_binding_and_composition_fail_and_restore_native(self):
        from portable_named_range_battle_cases import fixtures
        c=fixtures()[0];spec=dict(coord=c['coord'],logical_geometry=c['logical_geometry'],rules=c['named_range_rules'])
        with self.assertRaisesRegex(ValueError,'combined checked'):
            normalize({'named_range':spec,'enemy_healing':[]})
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        body=copy.deepcopy(c['body']);bad=copy.deepcopy(spec);bad['rules'][0]['effect']='not-an-original-effect';body['reference_models']={'named_range':bad}
        with self.assertRaisesRegex(ValueError,'owner/effect binding'):engine_worker.evaluate(body)
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))

    def test_named_range_decoder_rejects_reserved_partial_and_capacity_corruption(self):
        from portable_product_named_range import read_result
        from portable_named_range_battle_wire import OUTPUT,OUT,OUT_HEADER,MAGIC
        from portable_runtime import UnsupportedPortable
        b=array.array('I',[0])*OUTPUT;b[OUT:OUT+3]=array.array('I',[MAGIC,1,1]);at=OUT+OUT_HEADER
        def number(offset,value):b[at+offset:at+offset+2]=array.array('I',struct.unpack('<II',struct.pack('<d',value)))
        number(4,1.);number(8,1.);number(10,1.);b[at+12]=b[at+13]=2;b[at+16]=1;b[at+17]=1
        rule=dict(owner='owner',effect='damage',base_radius=1.,base_count=2)
        meta=dict(product_named_range=dict(names=['owner'],declarations={'named_range':dict(rules=[rule])}),named_range_battle=dict(bindings=[dict(row=0,owner='owner',effect='damage')]))
        result=read_result(b,meta,1.);self.assertEqual(result['named_range']['casts'][0]['add_count'],1)
        for offset,value in [(OUT,0),(OUT+2,513),(at+1,5),(at+13,3),(at+16,3),(at+22,1),(at+32,1),(at+7,0x7ff80000)]:
            bad=array.array('I',b);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):read_result(bad,meta,1.)
        with self.assertRaises(UnsupportedPortable):read_result(b[:-1],meta,1.)

    def test_named_range_standalone_cpu_worker_uses_shared_coordinate_context(self):
        import json,subprocess
        from portable_product_programs import body_for_program
        body=body_for_program(ROOT,'named-range-accumulate');body['action']='evaluate'
        process=subprocess.run([sys.executable,str(ROOT/'app/engine_worker.py')],input=json.dumps(body),text=True,capture_output=True,timeout=30)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        response=json.loads(process.stdout);self.assertFalse(response['expected'])
        self.assertEqual(len(response['reference_models']['named_range']['casts']),54)

    def test_movement_product_uses_checked_native_clock_and_literal_shared_input(self):
        from portable_enemy_movement_cases import fixtures
        from portable_runtime import UnsupportedPortable
        import portable_detail as product
        aliases=(timeline.simulate,sim.simulate,timeline.random.getstate())
        for case in fixtures():
            body=copy.deepcopy(case['body'])
            body['reference_models']={'enemy_movement':dict(coord=case['coord'],logical_geometry=case['logical_geometry'],motion=case['enemy_movement'])}
            before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU trajectory may prepare GPU input')):
                prepared,run=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,original);self.assertEqual((source,iw,ow),('gpu/product_movement_battle_entry.slang',117476,2032000))
            from portable_backend import validate_composed_stride
            validate_composed_stride(source,iw,ow)
            with self.assertRaises(ValueError):validate_composed_stride(source,iw-1,ow)
            with self.assertRaises(ValueError):validate_composed_stride(source,iw,ow-1)
            self.assertFalse(run.expected);self.assertEqual(run.config['rng_mode'],'random')
            self.assertFalse(meta['product_enemy_movement']['cpu_state_or_schedule_supplied'])
            actual=engine_worker.evaluate(body);data=actual['reference_models']['enemy_movement']
            self.assertFalse(actual['expected']);self.assertEqual(body,before)
            self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))
            self.assertTrue(data['frames']);self.assertTrue(data['generations'])
            self.assertTrue(any(s['disabled'] or s['forced'] for f in data['frames'] for s in f['segments']))
            self.assertTrue(all('fields' not in s for f in data['frames'] for s in f['segments']))
            fixed=dict(prepared,policies={**prepared['policies'],'config':{**prepared['policies']['config'],'burst_gauge_mode':'fixed'}})
            fixed_source,fi,fo,fw,fm=product.compile_product(fixed)
            from portable_specs import LIMITS
            base=LIMITS['WORLD_CONTROL_INPUT_BASE']
            self.assertEqual(fixed_source,source.replace('_battle_entry','_fixed_battle_entry'))
            self.assertEqual((fi,fo),(iw,ow));validate_composed_stride(fixed_source,fi,fo)
            self.assertEqual(fw[base+1],6);self.assertEqual(fw[base+5:base+8],words[base+5:base+8])
            self.assertEqual(fw[base+12],0x46424731)
            self.assertEqual(fm['real_prepared_input']['policy'],fixed['policies'])
            self.assertFalse(fm['product_fixed_burst']['CPU_state_or_schedule_as_input'])
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with execution(normalize(body['reference_models'])):raise RuntimeError('injected')
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.random.getstate()))

    def test_product_lock_continuations_keep_prefixes_and_reject_unused_or_overflow_words(self):
        from portable_original_lock_layout import PRODUCT_BANKS,PRODUCT_OUTPUT,PRODUCT_END,product_address,product_rows,product_schema
        from portable_physical_lock_layout import SNAPSHOTS
        from portable_lock_packet_layout import SHOT_TIMES
        from portable_lock_typed_layout import OFFSET,OUTPUT
        self.assertEqual(PRODUCT_BANKS['snapshots']['base'],SNAPSHOTS+OFFSET)
        self.assertEqual(PRODUCT_BANKS['shot_times']['base'],SHOT_TIMES+OFFSET)
        occupied=set()
        for name,bank in PRODUCT_BANKS.items():
            block=array.array('I',[0])*PRODUCT_OUTPUT;prefix=bank['prefix'];width=bank['width']
            for index in (0,prefix-1,prefix,bank['capacity']-1):
                address=product_address(name,index);block[address]=index+1
                self.assertGreaterEqual(address,OUTPUT if index>=prefix else bank['base'])
            rows=product_rows(block,name,bank['capacity'])
            self.assertEqual([rows[i][0] for i in (0,prefix-1,prefix,bank['capacity']-1)],[i+1 for i in (0,prefix-1,prefix,bank['capacity']-1)])
            with self.assertRaises(ValueError):product_rows(block,name,bank['capacity']+1)
            with self.assertRaises(ValueError):product_rows(block,name,prefix)
            block=array.array('I',[0])*PRODUCT_OUTPUT;block[bank['base']+width]=1
            with self.assertRaises(ValueError):product_rows(block,name,1)
            span=set(range(bank['extra'],bank['extra']+(bank['capacity']-prefix)*width))
            self.assertFalse(occupied&span);occupied|=span
        self.assertEqual(max(occupied)+1,PRODUCT_END)
        self.assertLessEqual(PRODUCT_END,PRODUCT_OUTPUT)
        self.assertIn('#ifdef PORTABLE_PRODUCT_LONG_LOCK',product_schema())
        from portable_specs import shader_schema
        self.assertIn('#elif defined(PORTABLE_PRODUCT_LONG_LOCK)\nstatic const uint P_OUTPUT_WORDS = PL_LAYOUT_OUTPUT;',shader_schema())

    def test_original_product_typed_owners_pack_exact_logical_handles_without_native_state(self):
        from portable_product_programs import logical_owner_body
        from portable_detail import prepare,compile_product
        from product_typed_model import normalize_product
        from coordinate_typed_actor_policy import FIELD_MODE
        for name in ('typed-fixed','typed-accumulate','typed-lock-fixed','typed-lock-accumulate'):
            body=logical_owner_body(ROOT,name);before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No native generations or fields supplied to GPU')):
                pre,run=prepare(body);source,iw,ow,words,meta=compile_product(pre)
            self.assertEqual(body,before);self.assertEqual(iw,123732)
            base=115680 if 'lock' in name else 109968
            self.assertEqual(words[base+12:base+16],[3,1,1,2]);self.assertEqual(words[base+3],0)
            for i,row in enumerate(body['reference_models']['typed_targets']['bindings']):
                self.assertEqual(words[base+2328+i*12+5:base+2328+i*12+8],row['owner'])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))
            bad=copy.deepcopy(body);bad['reference_models']['typed_targets']['actor_policy']={'mode':FIELD_MODE}
            with self.assertRaisesRegex(ValueError,'BODY-owned'):normalize_product(bad['reference_models']['typed_targets'])
            bad=copy.deepcopy(body);bad['reference_models']['typed_targets']['bindings'][0]['owner']=[5,123,1]
            if 'lock_on' in bad['reference_models']:bad['reference_models']['lock_on']['typed_bindings']=copy.deepcopy(bad['reference_models']['typed_targets']['bindings'])
            with patch.object(sim,'execute',side_effect=AssertionError('Unknown owner must fail without native execution')):
                with self.assertRaisesRegex(ValueError,'configured logical enemy'):compile_product(prepare(bad)[0])

    def test_plain_ammo_version_and_output_stride_are_checked_before_device_work(self):
        from portable_backend import validate_composed_stride,validate_product_ammo_versions
        from portable_enemy_ammo_wire import LAYOUT as E
        from portable_product_ammo import LONG_PLAIN_OUTPUT_WORDS
        source='gpu/product_ammo_fixed_battle_entry.slang'
        words=array.array('I',[2]+[0]*(2*E['INPUT_WORDS']))
        for i in range(2):words[1+i*E['INPUT_WORDS']+E['BASE']+1]=2
        validate_composed_stride(source,E['INPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS)
        validate_product_ammo_versions(source,words.tobytes(),E['INPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS,2)
        for bad in (E['OUTPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS-1):
            with self.assertRaises(ValueError):validate_product_ammo_versions(source,words.tobytes(),E['INPUT_WORDS'],bad,2)
        words[1+E['INPUT_WORDS']+E['BASE']+1]=1
        with self.assertRaisesRegex(ValueError,'version and output stride'):
            validate_product_ammo_versions(source,words.tobytes(),E['INPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS,2)
        for other in ('gpu/world_enemy_ammo_entry.slang','gpu/product_ammo_fixed_group_battle_entry.slang','gpu/product_ammo_fixed_target_battle_entry.slang'):
            with self.assertRaises(ValueError):validate_composed_stride(other,E['INPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS)

    def test_long_plain_ammo_resource_tail_has_explicit_version_and_complete_decoder(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare,compile_product
        from portable_enemy_ammo_wire import LAYOUT as E
        from portable_product_ammo import LONG_PLAIN_OUTPUT_WORDS
        from portable_resource_decode import resource_readback
        from portable_specs import LIMITS as L
        for mode in ('fixed','accumulate'):
            for duration,version,output in ((30.,1,E['OUTPUT_WORDS']),(30.01,2,LONG_PLAIN_OUTPUT_WORDS),(180.,2,LONG_PLAIN_OUTPUT_WORDS)):
                body=copy.deepcopy(selected_profile_bodies(['\ubca8\ubcb3'],0)[0][2]);body.update(duration=duration,burst_gauge_mode=mode)
                with patch.object(sim,'execute',side_effect=AssertionError('No native resource state supplied to GPU')):
                    pre,run=prepare(body);before=copy.deepcopy(pre);source,iw,ow,words,meta=compile_product(pre)
                self.assertEqual(pre,before);self.assertEqual((iw,ow),(E['INPUT_WORDS'],output))
                self.assertEqual(words[E['BASE']+1],version)
                self.assertEqual(meta['product_enemy_ammo']['output_words'],output)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))
        meta=dict(resource_names=['charge'],product_enemy_ammo=dict(output_words=LONG_PLAIN_OUTPUT_WORDS))
        words=array.array('I',[0])*LONG_PLAIN_OUTPUT_WORDS
        count=128+(E['OUTPUT_WORDS']-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8+1
        words[L['RESOURCE_HEADER_BASE']]=words[L['RESOURCE_HEADER_BASE']+1]=count
        for i in range(count):
            at=L['RESOURCE_TRACE_BASE']+i*8 if i<128 else E['OUTPUT_BASE']+E['RESOURCE_BASE']+(i-128)*8
            words[at]=26
        result=resource_readback(words,meta,L,lambda at:0.)
        self.assertEqual(len(result['resource_trace']),count)
        self.assertEqual(result['resource_trace_total'],count)
        with self.assertRaisesRegex(RuntimeError,'Invalid complete product resource history'):
            resource_readback(words[:-1],meta,L,lambda at:0.)
        bad=copy.deepcopy(meta);bad['product_enemy_ammo']['output_words']=LONG_PLAIN_OUTPUT_WORDS+1
        with self.assertRaisesRegex(RuntimeError,'output ownership'):
            resource_readback(words,bad,L,lambda at:0.)

    def test_long_product_groups_choose_lossless_existing_codec_without_cpu_execution(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare,compile_product
        from portable_battle_attack_group_input import product_history
        for name in ('\ubca8\ub85c\ud0c0','\ub2c8\ud790\ub9ac\uc2a4\ud0c0'):
            for duration,flag in ((30.,0),(30.01,1),(180.,1)):
                body=copy.deepcopy(selected_profile_bodies([name],0)[0][2]);body.update(duration=duration,burst_gauge_mode='fixed')
                with patch.object(sim,'execute',side_effect=AssertionError('No native schedules supplied to group input')):
                    pre,run=prepare(body);before=copy.deepcopy(pre);source,iw,ow,words,meta=compile_product(pre)
                self.assertEqual(pre,before);self.assertEqual((iw,ow),(104408,1048576))
                self.assertEqual(words[104403],flag);self.assertEqual(product_history(pre),'compact' if flag else 'fixed64')
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))

    def test_default_body_preserves_expected_policy_and_all_original_motion_lock_definitions(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare,compile_product
        for name in ('\uc720\ub2c8','\uc580','\uc2a4\ub178\uc6b0 \ud654\uc774\ud2b8 : \ud5e4\ube44\uc554\uc988'):
            for mode in ('fixed','accumulate'):
                body=copy.deepcopy(selected_profile_bodies([name],0)[0][2]);body['burst_gauge_mode']=mode;before=copy.deepcopy(body)
                with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle or model selection in static preparation')):
                    pre,run=prepare(body);original=copy.deepcopy(pre);source,iw,ow,words,meta=compile_product(pre)
                self.assertEqual(pre,original);self.assertEqual(body,before);self.assertTrue(run.expected)
                self.assertEqual(pre['policies']['config']['rng_mode'],'expected');self.assertFalse(body.get('reference_models'))
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))
                if name.startswith('\uc2a4\ub178\uc6b0'):
                    self.assertTrue(meta['product_static_body_lock']);self.assertEqual(len(meta['product_lock_on']['bindings']),1)
                    self.assertEqual(meta['product_lock_on']['declarations']['lock_on']['typed_bindings'],[])
                else:
                    info=meta['product_static_enemy_movement'];self.assertEqual(info['movable_actor_count'],0)
                    self.assertFalse(info['coordinate_model_inferred']);self.assertEqual(info['original_effects'],[pre['effects'][i] for i in info['source_indices']])
                    self.assertEqual((iw,ow),(104400,786432))

    def test_default_body_does_not_assume_movement_or_lock_policy_in_authored_world(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_detail import prepare,compile_product
        from portable_runtime import UnsupportedPortable
        for name in ('\uc720\ub2c8','\uc580','\uc2a4\ub178\uc6b0 \ud654\uc774\ud2b8 : \ud5e4\ube44\uc554\uc988'):
            base=selected_profile_bodies([name],0)[0][2]
            for change in (dict(patterns=[dict(id='future',kind='summon',delay=5.,spec=dict(count=1,hp=1e8))]),dict(patterns=[dict(id='idle',kind='idle')]),dict(has_parts=True),dict(part_break_interval=1.),dict(coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.))):
                body=copy.deepcopy(base);body['enemy'].update(change)
                with patch.object(sim,'execute',side_effect=AssertionError('Unknown active model must stop before battle')):
                    with self.assertRaises((UnsupportedPortable,ValueError)):
                        pre,_=prepare(body);compile_product(pre)

    def test_movement_declarations_reject_unknown_geometry_or_composition_before_battle(self):
        from portable_enemy_movement_cases import fixtures
        from product_movement_model import normalize as movement
        c=fixtures()[0];spec=dict(coord=c['coord'],logical_geometry=c['logical_geometry'],motion=c['enemy_movement'])
        bad=copy.deepcopy(spec);bad['motion']['actors'].reverse()
        for value in ({},dict(spec,coord=None),dict(spec,coord={'auto_aim':[True,0]}),bad):
            with self.subTest(value=value),self.assertRaises(ValueError):movement(value)
        with self.assertRaisesRegex(ValueError,'combined checked'):
            normalize({'enemy_movement':spec,'enemy_healing':[]})

    def test_movement_standalone_cpu_worker_resolves_provider_before_checked_rewrites(self):
        import json,subprocess
        from portable_enemy_movement_cases import fixtures
        c=fixtures()[0];body=copy.deepcopy(c['body']);body['action']='evaluate'
        body['reference_models']={'enemy_movement':dict(coord=c['coord'],logical_geometry=c['logical_geometry'],motion=c['enemy_movement'])}
        process=subprocess.run([sys.executable,str(ROOT/'app/engine_worker.py')],input=json.dumps(body),text=True,capture_output=True,timeout=30)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        result=json.loads(process.stdout);self.assertFalse(result['expected'])
        self.assertTrue(result['reference_models']['enemy_movement']['frames'])

    def test_movement_readback_rejects_partial_identity_reserved_and_segment_discontinuity(self):
        from portable_product_movement import read_result
        from portable_enemy_movement_wire import OUTPUT,OUT,STATE,STATE_WORDS,FRAMES,FRAME_WORDS,SEGMENTS,MAGIC
        from portable_runtime import UnsupportedPortable
        b=array.array('I',[0])*OUTPUT;label='__enemy__:wave#1'
        spec=dict(motion=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',actors=[dict(label=label)]))
        meta=dict(product_enemy_movement=dict(declarations={'enemy_movement':spec},bindings=[dict(kind=0,identity=0,label='__enemy__'),dict(kind=5,identity=0,label=label)]))
        def number(at,x):b[OUT+at:OUT+at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',x)))
        b[OUT:OUT+3]=array.array('I',[MAGIC,2,1])
        for at in (FRAMES,FRAMES+FRAME_WORDS):b[OUT+at:OUT+at+5]=array.array('I',[1,1,1,0,int(at!=FRAMES)])
        number(FRAMES+FRAME_WORDS+6,1.);number(FRAMES+FRAME_WORDS+8,2.)
        b[OUT+SEGMENTS:OUT+SEGMENTS+3]=array.array('I',[1,1,0]);number(SEGMENTS+6,1.);number(SEGMENTS+12,2.)
        at=STATE+STATE_WORDS;b[OUT+at:OUT+at+2]=array.array('I',[1,1]);b[OUT+at+8]=1;number(at+2,1.);number(at+4,2.)
        data=read_result(b,meta,1.)['enemy_movement'];self.assertEqual(data['frames'][-1]['position'],[2.,0.])
        for offset,value in ((OUT,0),(OUT+1,4097),(OUT+FRAMES,0),(OUT+FRAMES+5,1),(OUT+SEGMENTS+2,4),(OUT+SEGMENTS+4,1),(OUT+at+9,1)):
            bad=array.array('I',b);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):read_result(bad,meta,1.)
        with self.assertRaises(UnsupportedPortable):read_result(b[:-1],meta,1.)

    def test_original_enemy_magazine_product_uses_literal_state_and_restores_native_operator(self):
        from portable_enemy_ammo_cases import fixtures
        import portable_detail as product
        case=fixtures()[0];body=copy.deepcopy(case['body']);body['reference_models']={'enemy_ammo':case['enemy_ammo']}
        before=copy.deepcopy(body);aliases=(timeline.simulate,sim.simulate);register=timeline._register_instant_handlers
        with patch.object(sim,'execute',side_effect=AssertionError('No native battle during input preparation')):
            prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
            source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,original);self.assertEqual((source,iw,ow),('gpu/product_ammo_battle_entry.slang',117632,2032000))
        self.assertFalse(meta['product_enemy_ammo']['cpu_state_or_schedule_supplied'])
        actual=engine_worker.evaluate(body);data=actual['reference_models']['enemy_ammo']
        self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate));self.assertIs(register,timeline._register_instant_handlers)
        self.assertTrue(data['charges']);self.assertTrue(data['attempts']);self.assertTrue(data['reloads'])
        self.assertTrue(any(t['after']<t['before'] for r in data['charges'] for t in r['targets']))
        self.assertTrue(all(len(r['completion'])==1 for r in data['charges']))

    def test_enemy_magazine_default_has_no_fabricated_capacity_and_attack_requires_declaration(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_enemy_ammo_cases import fixtures
        from portable_runtime import UnsupportedPortable
        import portable_detail as product
        body=selected_profile_bodies(['벨벳'],0)[0][2];prepared,_=product.prepare(body);source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(words[116464:116468],[0x45414d31,1,0,1]);self.assertFalse(any(words[116468:]))
        self.assertEqual(meta['real_prepared_input']['prepared_effects'],len(prepared['effects']))
        prepared,_=product.prepare(fixtures()[0]['body'])
        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*magazines'):product.compile_product(prepared)
        with self.assertRaisesRegex(ValueError,'combined checked native'):
            normalize({'enemy_ammo':fixtures()[0]['enemy_ammo'],'weighted_incoming':{}})

    def test_extended_resource_history_is_complete_and_cannot_use_a_short_prefix(self):
        from portable_resource_decode import resource_readback
        from portable_specs import LIMITS as L
        from portable_enemy_ammo_wire import LAYOUT as E
        words=array.array('I',[0])*E['OUTPUT_WORDS'];h=L['RESOURCE_HEADER_BASE'];words[h]=words[h+1]=129
        for i in range(129):
            at=L['RESOURCE_TRACE_BASE']+i*8 if i<128 else E['OUTPUT_BASE']+E['RESOURCE_BASE']+(i-128)*8
            words[at]=26;words[at+4:at+6]=array.array('I',struct.unpack('<II',struct.pack('<d',i/60)))
        def number(at):return struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
        meta=dict(resource_names=['original'],product_enemy_ammo={})
        data=resource_readback(words,meta,L,number);self.assertEqual(len(data['resource_trace']),129)
        self.assertEqual(data['resource_trace'][-1]['time'],128/60)
        with self.assertRaises(RuntimeError):resource_readback(words[:159744],meta,L,number)
        with self.assertRaises(RuntimeError):resource_readback(words,dict(resource_names=['original']),L,number)

    def test_magazine_blocked_attempt_requires_matching_source_generation_and_no_query(self):
        from portable_product_add_attack import query_sources
        from portable_add_attack_battle_wire import LAYOUT as A,MAGIC
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        words=array.array('I',[0])*A['OUTPUT_WORDS'];words[A['OUTPUT_BASE']]=MAGIC;words[A['OUTPUT_BASE']+1]=1
        h=L['WORLD_FRAME_OUTPUT_BASE'];words[h+2]=1;at=h+2832;words[at]=3;words[at+2]=1
        words[A['OUTPUT_BASE']+A['MAP_BASE']]=1;words[A['OUTPUT_BASE']+A['MAP_BASE']+1]=1
        meta=dict(product_add_attacks=dict(labels=['','wave#1'],source_nodes=[-1,0]),product_enemy_ammo=dict(bindings=[dict(label='__enemy__'),dict(label='__enemy__:wave#1')],case=dict(patterns=[dict(id='wave')])))
        attempt=dict(label='__enemy__:wave#1',actor=[5,0,1],pattern='wave',index=1,status='empty')
        self.assertEqual(query_sources(words,meta,ammo_attempts=[attempt]),{})
        with self.assertRaises(UnsupportedPortable):query_sources(words,meta)
        for key,value in [('status','fired'),('actor',[5,0,2]),('pattern','other'),('index',2)]:
            bad=dict(attempt,**{key:value})
            with self.subTest(key=key),self.assertRaises(UnsupportedPortable):query_sources(words,meta,ammo_attempts=[bad])
        words[at+5]=1;self.assertEqual(query_sources(words,meta,ammo_attempts=[dict(attempt,status='fired')]),{0:'wave#1'})

    def test_default_world_preserves_all_original_carriers_without_inventing_incoming_quantities(self):
        from portable_original_identity_inventory import selected_profile_bodies
        import portable_detail as product
        from portable_specs import LIMITS as L,FIELDS as F
        with patch.object(sim,'execute',side_effect=AssertionError('World requirements must be static')):
            for name,stage,body in selected_profile_bodies(['베이','솔져 O.W.']):
                prepared,_=product.prepare(dict(body,burst_gauge_mode='fixed'));before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
                kind='product_weighted_incoming' if name=='베이' else 'product_cover_defense'
                self.assertTrue(meta[kind]['unspecified_quantities']);self.assertEqual(meta[kind]['declarations'],{})
                self.assertEqual(prepared,before);self.assertEqual(meta['real_prepared_input']['prepared_effects'],len(prepared['effects']))
                self.assertEqual(words[115683],1);self.assertFalse(any(words[115684:115690] if name=='베이' else words[115688:115698]))
                if name!='베이':
                    for index in meta[kind]['definition_indices']:
                        row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                        self.assertEqual((words[at+F['KIND']],words[at+F['STAT']]),(0,93))

    def test_no_incoming_contract_checks_every_attack_node_without_predicting_schedule(self):
        from portable_product_world_contract import has_incoming_attacks
        from portable_weighted_battle_cases import fixtures
        import portable_detail as product
        from portable_runtime import UnsupportedPortable
        case=fixtures()[0];body=copy.deepcopy(case['body']);body['enemy']['patterns'][1]['delay']=181
        prepared,_=product.prepare(body)
        self.assertTrue(has_incoming_attacks(prepared))
        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*weights'):product.compile_product(prepared)
        body['enemy']['patterns']=[dict(id='owner',kind='summon',spec=dict(name='x',count=1,hp=1000,attack=dict(atk=10,coeff=100,target='all')))]
        prepared,_=product.prepare(body)
        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*weights'):product.compile_product(prepared)

    def test_cover_product_keeps_literal_operations_and_independent_bases(self):
        from portable_cover_defense_battle_cases import fixtures
        import portable_detail as product
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'cover_defense':case['cover_defense']};body['manual_cover_sequences']=case['declared_manual_sequences']
        before=copy.deepcopy(body);aliases=(timeline.simulate,sim.simulate)
        with patch.object(sim,'execute',side_effect=AssertionError('Static input may not simulate')):
            prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
            source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,original);self.assertEqual((source,iw,ow),('gpu/product_cover_battle_entry.slang',115704,2048912))
        self.assertFalse(meta['product_cover_defense']['cpu_state_or_schedule_supplied']);self.assertFalse(any(words[104400:115680]))
        actual=engine_worker.evaluate(body);data=actual['reference_models']['cover_defense']
        self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        self.assertEqual(actual['manual_cover_sequences'],body['manual_cover_sequences'])
        self.assertEqual(len(data['receipts']),15)
        self.assertTrue(any(r['effective_defense']>r['base_defense'] for r in data['receipts']))
        self.assertEqual(data['base_defenses'],[r['base_defense'] for r in case['cover_defense']])

    def test_cover_malformed_or_unknown_roster_fails_closed(self):
        from portable_cover_defense_battle_cases import fixtures
        import portable_detail as product
        from portable_runtime import UnsupportedPortable
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        prepared,_=product.prepare(body)
        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*bases'):product.compile_product(prepared)
        body['reference_models']={'cover_defense':case['cover_defense']}
        body['manual_cover_sequences']=case['declared_manual_sequences'];body['burst_gauge_mode']='fixed'
        prepared,_=product.prepare(body)
        source,_,_,_,_=product.compile_product(prepared)
        self.assertEqual(source,'gpu/product_cover_fixed_battle_entry.slang')
        bad=copy.deepcopy(case['cover_defense']);bad[0]['name']='wrong original owner'
        with self.assertRaisesRegex(ValueError,'original cover owner'):
            engine_worker.evaluate(dict(body,reference_models={'cover_defense':bad}))
        for rows in ([],[dict(name='a',base_defense=True)]*5,[dict(name=str(i),base_defense=float('inf')) for i in range(5)]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):normalize({'cover_defense':rows})
        for overrides in ({}, {'not-in-squad':[dict(action='cover',t=1,duration=1)]}, {body['squad'][0]:[dict(action='cover',t=True,duration=1)]}):
            with self.subTest(overrides=overrides),patch.object(sim,'execute',side_effect=AssertionError('Invalid cover control may not simulate')),self.assertRaises(ValueError):
                engine_worker.evaluate(dict(body,manual_cover_sequences=overrides))

    def test_fixed_cover_keeps_posture_controls_literal_and_restores_fixed_policy(self):
        import struct
        from portable_cover_defense_battle_cases import fixtures
        from portable_specs import LIMITS as L
        import portable_detail as product
        for case in fixtures():
            body=copy.deepcopy(case['body'])
            body.update(burst_gauge_mode='fixed',
                reference_models={'cover_defense':case['cover_defense']},
                manual_cover_sequences=case['declared_manual_sequences'])
            with self.subTest(case=case['name']),patch.object(sim,'execute',side_effect=AssertionError('No native state in GPU input')):
                prepared,_=product.prepare(body);prepared['policies']['config']['first_burst_time']=4.25;before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_cover_fixed_battle_entry.slang')
            self.assertEqual((iw,ow),(115704,2048912))
            at=L['WORLD_CONTROL_INPUT_BASE']
            self.assertEqual(words[at+1],6)
            self.assertEqual(words[at+7],0x4d435631)
            self.assertEqual(words[at+12],0x46424731)
            self.assertEqual(words[at+13:at+16],[0,0,0])
            self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[at+8:at+10]))[0],4.25)
            self.assertEqual(meta['real_prepared_input']['policy'],before['policies'])
            self.assertEqual(meta['product_manual_cover_owners'],list(range(5)))
            self.assertFalse(meta['product_fixed_burst']['CPU_state_or_schedule_as_input'])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(before['effects']))))

    def test_manual_cover_without_cover_effect_routes_to_existing_product_consumer(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_specs import LIMITS as L
        from portable_cover_defense_wire import LAYOUT as C,MAGIC
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,mode)
            owner=body['squad'][0]
            body['manual_cover_sequences']={owner:[dict(action='cover',t=.5,duration=.25)]}
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            self.assertFalse(any(r['effect'].get('stat')=='cover_def_pct' for r in prepared['effects']))
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle in preparation')):
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_cover_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            self.assertEqual((iw,ow),(115704,2048912))
            self.assertEqual(meta['product_manual_cover_owners'],[0])
            self.assertTrue(meta['product_cover_defense']['unspecified_quantities'])
            self.assertEqual(meta['product_cover_defense']['definition_indices'],[])
            self.assertEqual(words[C['BASE']:C['BASE']+4],[MAGIC,1,5,1])
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],6 if mode=='fixed' else 3)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            # An authored attack still requires independent declared DEF;
            # the routing change must never manufacture a defense value.
            body['enemy']['patterns']=[dict(id='incoming',kind='attack',spec=dict(atk=100,coeff=100,hits=1,target='all'))]
            incoming,_=product.prepare(body)
            with self.assertRaisesRegex(UnsupportedPortable,'explicit.*cover_defense'):
                product.compile_product(incoming)

    def test_cover_and_original_group_listeners_share_one_product_input(self):
        import portable_detail as product
        from detail_coverage import body_for
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_cover_defense_wire import STAT
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for(['솔져 O.W.','벨로타','미란다','도라','드레이크'],30)
            body.update(burst_gauge_mode=mode,
                reference_models={'cover_defense':[dict(name=n,base_defense=100) for n in body['squad']]},
                manual_cover_sequences={body['squad'][0]:[dict(action='cover',t=.5,duration=1)]})
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU events as GPU input')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_cover_'+('fixed_' if mode=='fixed' else '')+'group_battle_entry.slang')
            self.assertEqual((iw,ow),(115704,2048912))
            self.assertEqual(words[104400],0x41475331)
            self.assertTrue(words[104402]);self.assertFalse(any(words[104408:115680]))
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            indices=meta['product_cover_defense']['definition_indices'];self.assertTrue(indices)
            for index in indices:
                row=meta['binding_source_indices'].index(index)
                self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],STAT)
            self.assertTrue(meta['real_prepared_input']['declared_attack_group_policy']['listener_owners'])
            # A connected combination must still reject an unauthored healing source.
            prepared['reference_models']['enemy_healing']=[dict(node='world',targets=['x'],amount=1)]
            with self.assertRaisesRegex(ValueError,'Healing source must be an existing idle node'):
                product.compile_product(prepared)

    def test_cover_composes_original_target_modifiers_and_optional_groups(self):
        import portable_detail as product
        from detail_coverage import body_for
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_cover_defense_wire import STAT
        from portable_backend import validate_composed_stride
        for kind,roster,prefix in [
            ('target',['솔져 O.W.','아스카','미란다','도라','드레이크'],110112),
            ('group-target',['솔져 O.W.','사쿠라','벨로타','도라','드레이크'],104672),
        ]:
            for mode in ('fixed','accumulate'):
                body=body_for(roster,30)
                body.update(burst_gauge_mode=mode,
                    reference_models={'cover_defense':[dict(name=n,base_defense=100) for n in roster]},
                    manual_cover_sequences={roster[0]:[dict(action='cover',t=.5,duration=1)]})
                with patch.object(sim,'execute',side_effect=AssertionError('No native schedule as input')):
                    prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                    source,iw,ow,words,meta=product.compile_product(prepared)
                with self.subTest(kind=kind,mode=mode):
                    self.assertEqual(prepared,before)
                    self.assertEqual(source,'gpu/product_cover_'+('fixed_' if mode=='fixed' else '')+kind.replace('-','_')+'_battle_entry.slang')
                    validate_composed_stride(source,iw,ow)
                    self.assertEqual((iw,ow),(115704,2048912))
                    self.assertFalse(any(words[prefix:115680]))
                    self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                    axes=meta['real_prepared_input']['target_modifier_carriers']['axis_rows']
                    self.assertTrue(any(axes))
                    self.assertEqual(bool(meta['real_prepared_input'].get('declared_attack_group_policy')),kind=='group-target')
                    for index in meta['product_cover_defense']['definition_indices']:
                        row=meta['binding_source_indices'].index(index)
                        self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['STAT']],STAT)

    def test_fixed_cover_header_conversion_rejects_invalid_tap_masks_and_reserved_words(self):
        import portable_detail as product
        from portable_product_cover import compile_product
        from portable_product_programs import body_for_program
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        body=body_for_program(ROOT,'default-cover-fixed')
        prepared,_=product.prepare(body)
        for version,mask,reserved in [(2,0,False),(2,32,False),(1,0,True),(2,1,True)]:
            def producer(inner):
                source,iw,ow,words,meta=product.compile_product(inner)
                at=L['WORLD_CONTROL_INPUT_BASE'];words[at+1]=version
                words[at+5:at+16]=[0]*11
                if version==2:words[at+5]=mask
                if reserved:words[at+15]=1
                return source,iw,ow,words,meta
            with self.subTest(version=version,mask=mask,reserved=reserved),self.assertRaisesRegex(UnsupportedPortable,'canonical control header'):
                compile_product(prepared,producer)

    def test_cover_readback_rejects_overflow_and_stale_depth_state(self):
        from portable_product_cover import read_result
        from portable_cover_defense_wire import LAYOUT as C,MAGIC,OUTPUT
        from portable_runtime import UnsupportedPortable
        names=['a','b','c','d','e'];meta=dict(product_cover_defense=dict(declarations={'cover_defense':[dict(name=n,base_defense=100) for n in names]}))
        words=array.array('I',[0])*OUTPUT;head=C['OUTPUT_BASE'];words[head]=MAGIC
        self.assertEqual(read_result(words,meta,names,30.)['cover_defense']['receipts'],[])
        for offset,value in [(head,0),(head+1,513),(head+2,1),(head+C['SNAPSHOT_BASE'],1),(head+C['RECEIPT_BASE'],1)]:
            bad=array.array('I',words);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):read_result(bad,meta,names,30.)

    def test_manual_cover_control_intervals_require_gpu_open_close_and_marker(self):
        from portable_world_result import read_product_control_log
        from portable_specs import LIMITS as L
        from portable_manual_control_specs import BASE
        from portable_runtime import UnsupportedPortable
        words=array.array('I',[0])*2048912;head=L['WORLD_CONTROL_HEAD_BASE'];trace=L['WORLD_CONTROL_TRACE_BASE']
        words[head]=0x57434831;words[head+1]=2;words[head+13]=0x50434c31
        for who in range(5):words[BASE+who*16+14]=0x504d4331
        for index,(kind,when) in enumerate([(4,.5),(5,.75)]):
            at=trace+index*8;words[at]=kind;words[at+4]=1
            words[at+2:at+4]=array.array('I',struct.unpack('<II',struct.pack('<d',when)))
        meta=dict(product_control_labels=[[] for _ in range(5)],product_manual_cover_owners=[0],states={})
        actual=read_product_control_log(words,meta,['a','b','c','d','e'],1.)
        row=actual.control_log[0];self.assertEqual((row.t0,row.t1,row.caster,row.input,row.mode,row.producer),(.5,.75,'a','cover','cover','엄폐(시퀀스)'))
        for offset,value in [(BASE+14,0),(head+13,0),(trace,5),(trace+1,1),(trace+8,4),(trace+8+4,0)]:
            bad=array.array('I',words);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):read_product_control_log(bad,meta,['a','b','c','d','e'],1.)

    def test_weighted_original_product_consumes_real_markers_and_preserves_definitions(self):
        from portable_weighted_battle_cases import fixtures
        import portable_detail as product
        case=fixtures()[0];body=copy.deepcopy(case['body']);body['reference_models']={'weighted_incoming':case['allocation']}
        before=copy.deepcopy(body);aliases=(timeline.simulate,sim.simulate)
        with patch.object(sim,'execute',side_effect=AssertionError('No native battle in GPU preparation')):
            prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
            source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual((iw,ow),(115696,2048912));self.assertEqual(prepared,original)
        self.assertEqual(source,'gpu/product_weighted_battle_entry.slang')
        self.assertFalse(meta['product_weighted_incoming']['cpu_state_or_schedule_supplied'])
        self.assertFalse(any(words[104400:115680]))
        result=engine_worker.evaluate(body);self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        data=result['reference_models']['weighted_incoming']
        self.assertTrue(data['snapshots']);self.assertTrue(data['cover_receipts'])
        self.assertTrue(any(s['active_mask']&32 for s in data['snapshots']))
        self.assertGreater(len(result['incoming_hits']),len(case['patterns'])-1)
        self.assertFalse(data['in_game_rules_verified'])

    def test_weighted_groups_preserve_original_markers_group_bank_and_literal_weights(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_weighted_battle_wire import LAYOUT as W,compiler_policy,MAGIC
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'weighted-'+mode+'-group')
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            inner=dict(prepared,_product_weighted_compiled=True);inner.pop('reference_models')
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU state as GPU input')):
                with compiler_policy():base,iw,ow,prefix,_=product.compile_product(inner)
                source,full_iw,full_ow,words,meta=product.compile_product(prepared)
            with self.subTest(mode=mode):
                self.assertEqual(prepared,before)
                self.assertEqual(source,'gpu/product_weighted_'+('fixed_' if mode=='fixed' else '')+'group_battle_entry.slang')
                self.assertEqual((iw,ow),(104408,1048576));self.assertEqual(words[:iw],prefix)
                self.assertFalse(any(words[iw:W['BASE']]))
                self.assertEqual(words[104400],0x41475331)
                self.assertEqual(words[W['BASE']:W['BASE']+4],[MAGIC,1,5,0])
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                rows=meta['product_weighted_incoming']['source_rows'];self.assertEqual(len(set(rows)),2)
                self.assertEqual(words[W['BASE']+10:W['BASE']+12],[r+1 for r in rows])
                self.assertTrue(meta['real_prepared_input']['declared_attack_group_policy']['listener_owners'])
                validate_composed_stride(source,full_iw,full_ow)
            missing=copy.deepcopy(prepared);missing.pop('reference_models')
            with self.assertRaisesRegex(UnsupportedPortable,'explicit.*weighted_incoming'):
                product.compile_product(missing)

    def test_coordinate_lock_preserves_all_definitions_and_disjoint_complete_arenas(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_product_coordinate_lock import check_schema,LockView,SHIFT,OUTPUT,FATE_EXTRA
        from portable_product_locks import COVER_SKILL_BASE,COVER_FATE_BASE
        from portable_skill_history import BASE
        check_schema(ROOT)
        body=body_for_program(ROOT,'coordinate-lock-accumulate');before=copy.deepcopy(body)
        with patch.object(sim,'execute',side_effect=AssertionError('No native schedule in input')):
            prepared,_=product.prepare(body);source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(body,before);self.assertEqual((iw,ow,len(words)),(120816,2558208,120816))
        self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
        self.assertEqual(words[115680+5120],meta['binding_source_indices'].index(meta['product_lock_on']['typed_source']))
        self.assertEqual(words[115680+2320],3)
        raw=[0]*OUTPUT
        for at,value in [(787456+SHIFT,11),(BASE,22),(FATE_EXTRA,33)]:raw[at]=value
        view=LockView(raw)
        self.assertEqual([view[787456],view[COVER_SKILL_BASE],view[COVER_FATE_BASE]],[11,22,33])
        from portable_product_coordinate_lock import validate_trace_addresses,COORDINATE_OUTPUT
        from portable_runtime import UnsupportedPortable
        at=COORDINATE_OUTPUT+153568+544
        raw[COORDINATE_OUTPUT+1]=2;raw[at+530]=COORDINATE_OUTPUT+3568+1040;raw[at+531]=2
        validate_trace_addresses(raw)
        raw[at+530]+=5*OUTPUT
        with self.assertRaisesRegex(UnsupportedPortable,'relative'):validate_trace_addresses(raw)
        raw[at+530]=0
        with self.assertRaisesRegex(UnsupportedPortable,'Unpaired'):validate_trace_addresses(raw)
        bad=copy.deepcopy(body['reference_models']);bad['enemy_healing']=[]
        with self.assertRaisesRegex(ValueError,'matching|combined'):normalize(bad)

    def test_typed_product_model_rejects_unknown_alias_mixed_owner_and_fixed_geometry(self):
        from portable_product_programs import body_for_program
        from product_typed_model import normalize_product
        body=body_for_program(ROOT,'typed-accumulate');spec=body['reference_models']['typed_targets'];before=copy.deepcopy(spec)
        self.assertEqual(normalize_product(spec),spec);self.assertEqual(spec,before)
        mutations=[]
        bad=copy.deepcopy(spec);bad['extra']=True;mutations.append(bad)
        bad=copy.deepcopy(spec);bad['bindings'][0]['label']='core';mutations.append(bad)
        bad=copy.deepcopy(spec);bad['bindings'][0]['owner']=[5,0,1];mutations.append(bad)
        bad=copy.deepcopy(spec);bad['bindings'][0]['kind']=4;mutations.append(bad)
        bad=copy.deepcopy(spec);bad['geometry']['point_source']='fixed';bad['geometry']['point']=[0.,0.];mutations.append(bad)
        for bad in mutations:
            with self.subTest(bad=bad),self.assertRaises(ValueError):normalize_product(bad)
        with self.assertRaisesRegex(ValueError,'matching checked consumer'):normalize({'typed_targets':spec,'enemy_healing':[]})

    def test_typed_product_packs_all_original_effects_and_no_cpu_target_state(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'typed-'+mode);before=copy.deepcopy(body)
            with patch.object(sim,'execute',side_effect=AssertionError('No native state in GPU input')):
                prepared,run=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(body,before);self.assertEqual(prepared,original)
            self.assertFalse(run.expected);self.assertEqual(run.config['rng_mode'],'random')
            self.assertEqual((iw,ow,len(words)),(123732,2345384,123732));validate_composed_stride(source,iw,ow)
            self.assertEqual(source,'gpu/product_typed_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertFalse(meta['product_typed_targets']['cpu_state_or_schedule_supplied'])
            self.assertEqual(words[109968+12:109968+16],[1,1,1,2])
            bad=copy.deepcopy(prepared);bad['effects'][0]['effect'].update(type='damage',stat='damage',target='all_projectiles')
            with self.assertRaisesRegex(UnsupportedPortable,'Original typed skill damage'):product.compile_product(bad)

    def test_coordinate_healing_keeps_all_effects_scene_and_literal_source_bank(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_product_coordinate import compile_product as coordinates
        from portable_enemy_healing_wire import LAYOUT as H,OUTPUT as O,compiler_policy,MAGIC
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'coordinate-healing-'+mode)
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            inner=dict(prepared,_product_healing_compiled=True)
            inner['reference_models']={'coordinate':prepared['reference_models']['coordinate']}
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle in GPU input')):
                with compiler_policy():_,iw,ow,prefix,_=coordinates(inner)
                source,wi,wo,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual((iw,ow),(115680,2032000));self.assertEqual(words[:iw],prefix)
            self.assertEqual((wi,wo,len(words)),(120048,2032000,120048))
            self.assertEqual(source,'gpu/product_coordinate_healing_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            validate_composed_stride(source,wi,wo)
            self.assertEqual(words[H['BASE']:H['BASE']+2],[MAGIC,1])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertEqual(set(meta['product_coordinate']['declarations']),{'coordinate'})
            self.assertEqual(set(meta['product_enemy_healing']['declarations']),{'enemy_healing'})
            self.assertTrue(meta['product_coordinate_healing'])
            bad=copy.deepcopy(prepared);bad['enemy']['patterns'][0]['spec']['attack']=dict(atk=100.,coeff=100.,target='all',hits=1,interval=0.)
            with self.assertRaisesRegex(UnsupportedPortable,'ADD-attack composition'):product.compile_product(bad)

    def test_coordinate_healing_requires_complete_projection_context_before_receipts(self):
        from portable_product_coordinate import read_result,OUTPUT
        from portable_runtime import UnsupportedPortable
        words=array.array('I',[0])*OUTPUT
        metadata={'product_coordinate_healing':True}
        for names,duration in [(None,None),(['a']*5,30),(['a','b','c','d','e'],float('nan')),(['a','b','c','d','e'],0)]:
            with self.subTest(names=names,duration=duration),self.assertRaises(UnsupportedPortable):read_result(words,metadata,names=names,duration=duration)

    def test_coordinate_add_preserves_original_shot_descriptors_scene_and_definitions(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_product_add_attack import lower
        from portable_backend import validate_composed_stride
        from portable_add_attack_battle_wire import LAYOUT as A,MAGIC
        from portable_product_coordinate import compile_product as coordinates
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'coordinate-add-'+mode)
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle input')):
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);self.assertEqual((iw,ow,len(words)),(116464,2032000,116464))
            self.assertEqual(source,'gpu/product_coordinate_add_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            validate_composed_stride(source,iw,ow)
            self.assertTrue(meta['product_coordinate_add'])
            self.assertTrue(meta['product_add_attacks']['CPU_schedule_or_state_supplied'] is False)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertEqual(words[A['BASE']:A['BASE']+2],[MAGIC,1])
            at=A['BASE']+A['ROW_BASE']
            self.assertEqual(words[at],2);self.assertEqual(words[at+1],3)
            self.assertEqual(words[at+4],1);self.assertEqual(words[at+5:at+7],list(struct.unpack('<II',struct.pack('<d',.25))))
            self.assertEqual(meta['product_coordinate']['declarations'],normalize(body['reference_models']))
            with self.assertRaises(ValueError):validate_composed_stride(source,iw-1,ow)

    def test_coordinate_add_receipt_ownership_rejects_reserved_and_forged_retirement(self):
        from portable_product_add_attack import coordinate_output_ownership
        from portable_add_attack_battle_wire import LAYOUT as A,MAGIC
        from portable_add_self_destruct_wire import LAYOUT as R,MAGIC as RM
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        words=array.array('I',[0])*A['OUTPUT_WORDS'];h=L['WORLD_FRAME_OUTPUT_BASE']
        words[A['OUTPUT_BASE']]=MAGIC;words[R['OUTPUT_BASE']]=RM
        meta=dict(product_coordinate_add=True,product_coordinate={},product_add_attacks=dict(labels=['','wave#1'],source_nodes=[-1,0]),product_world=dict(nodes=[dict(id='wave',kind='summon')]))
        # Presence, not a fabricated scalar marker, establishes coordinate metadata.
        meta['product_coordinate']={'declarations':{'coordinate':{}}}
        self.assertEqual(coordinate_output_ownership(words,meta),(A['OUTPUT_BASE'],R['OUTPUT_BASE']+R['HEADER']+R['ROWS']*R['ROW_WORDS']))
        at=R['OUTPUT_BASE']+R['HEADER'];words[R['OUTPUT_BASE']+1]=words[R['OUTPUT_BASE']+2]=1
        words[h+2]=1;w=h+2832;words[w:w+5]=array.array('I',[5,0,1,*struct.unpack('<II',struct.pack('<d',1.))])
        words[at:at+12]=array.array('I',[0,1,1,3,*struct.unpack('<II',struct.pack('<d',1.)),0,1,0,0,0,0])
        self.assertIsNotNone(coordinate_output_ownership(words,meta))
        for offset,value in [(at+1,0),(at+2,0),(at+3,0),(at+6,1),(at+7,0),(at+8,1),(A['OUTPUT_BASE']+2,1),(A['OUTPUT_BASE']+A['MAP_BASE']+2,1),(R['OUTPUT_BASE']+3,1),(at+12,1)]:
            bad=array.array('I',words);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):coordinate_output_ownership(bad,meta)
        missing=copy.deepcopy(meta);missing.pop('product_coordinate')
        with self.assertRaises(UnsupportedPortable):coordinate_output_ownership(words,missing)

    def test_weighted_coordinate_preserves_complete_scene_markers_and_disjoint_banks(self):
        import portable_detail as product
        from portable_product_programs import body_for_program
        from portable_product_coordinate import compile_product as coordinates
        from portable_weighted_battle_wire import compiler_policy,LAYOUT as W,MAGIC
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            body=body_for_program(ROOT,'coordinate-weighted-'+mode)
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            inner=dict(prepared,_product_weighted_compiled=True)
            inner['reference_models']={'coordinate':prepared['reference_models']['coordinate']}
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle in GPU input')):
                with compiler_policy():_,iw,ow,prefix,_=coordinates(inner)
                source,wi,wo,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual((iw,ow),(115680,2032000));self.assertEqual(words[:iw],prefix)
            self.assertEqual((wi,wo,len(words)),(115696,2048912,115696))
            self.assertEqual(source,'gpu/product_coordinate_weighted_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
            validate_composed_stride(source,wi,wo)
            self.assertEqual(words[W['BASE']:W['BASE']+4],[MAGIC,1,5,0])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
            self.assertEqual(set(meta['product_weighted_incoming']['declarations']),{'weighted_incoming'})
            self.assertEqual(set(meta['product_coordinate']['declarations']),{'coordinate'})
            self.assertTrue(meta['product_coordinate_weighted'])
            missing=copy.deepcopy(prepared);missing['reference_models'].pop('weighted_incoming')
            with self.assertRaisesRegex(UnsupportedPortable,'explicit.*weights'):product.compile_product(missing)
            mixed=copy.deepcopy(body['reference_models']);mixed['cover_defense']=[dict(name=n,base_defense=100.) for n in body['squad']]
            with self.assertRaisesRegex(ValueError,'combined checked landing'):normalize(mixed)

    def test_weighted_missing_weights_and_unsupported_composition_fail_before_dispatch(self):
        from portable_weighted_battle_cases import fixtures
        from portable_runtime import UnsupportedPortable
        import portable_detail as product
        case=fixtures()[0];prepared,_=product.prepare(case['body'])
        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*weights'):product.compile_product(prepared)
        prepared['reference_models']={'weighted_incoming':case['allocation'],'enemy_healing':[dict(node='world',targets=['x'],amount=1)]}
        with self.assertRaisesRegex(UnsupportedPortable,'combined wire'):product.compile_product(prepared)
        for key,value in [('caster_weight',0),('other_weight',True),('cover_weight',float('nan'))]:
            bad=copy.deepcopy(case['allocation']);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):normalize({'weighted_incoming':bad})
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with execution(normalize({'weighted_incoming':case['allocation']}),case['names']):raise RuntimeError('injected')
        self.assertIs(timeline.simulate,sim.simulate)
        self.assertNotIn('_nikke_weighted_snapshot',timeline.simulate.__globals__)

    def test_weighted_readback_rejects_overflow_scratch_and_unaccounted_cover_receipts(self):
        from portable_product_weighted import read_result
        from portable_weighted_battle_wire import LAYOUT as W,MAGIC,OUTPUT
        from portable_runtime import UnsupportedPortable
        spec=dict(policy='declared-weighted-incoming-v1',caster_weight=8.,other_weight=3.,cover_weight=262.)
        meta=dict(product_weighted_incoming=dict(declarations={'weighted_incoming':spec},source_rows=[0,2],source_name='body',cover_name='cover'))
        words=array.array('I',[0])*OUTPUT;head=W['OUTPUT_BASE'];words[head]=MAGIC
        with patch.object(sim,'execute',side_effect=AssertionError('Readback may not replay native')):
            self.assertEqual(read_result(words,meta,['a','b','c','d','e'],30.)['weighted_incoming']['snapshots'],[])
            for offset,value in [(head,0),(head+1,129),(head+2,1),(head+3,1),(head+W['SCRATCH'],1),(head+W['SNAPSHOTS'],1),(head+W['RECEIPTS'],1)]:
                bad=array.array('I',words);bad[offset]=value
                with self.subTest(offset=offset),self.assertRaises(UnsupportedPortable):read_result(bad,meta,['a','b','c','d','e'],30.)

    def test_static_original_anne_connects_the_same_consumer_with_or_without_healing_sources(self):
        from portable_enemy_healing_cases import fixtures
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_enemy_healing_wire import LAYOUT as H,INPUT_WORDS
        from portable_specs import LIMITS as L
        import portable_detail as product
        plain=selected_profile_bodies(['앤 : 미라클 페어리'],0)[0][2]
        case=fixtures()[0];declared=dict(case['body'],reference_models={'enemy_healing':case['enemy_healing']})
        for body,count in [(plain,0),(declared,4)]:
            with self.subTest(count=count),patch.object(sim,'execute',side_effect=AssertionError('No CPU battle before GPU')):
                prepared,_=product.prepare(body);prepared['policies']['config']['first_burst_time']=4.25;before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before);self.assertEqual(iw,INPUT_WORDS);self.assertEqual(ow,2032000)
            self.assertIn(source,('gpu/product_healing_battle_entry.slang','gpu/product_healing_fixed_battle_entry.slang'))
            self.assertEqual(words[H['BASE']:H['BASE']+3],[0x45484c31,1,count])
            self.assertEqual(meta['real_prepared_input']['prepared_effects'],len(prepared['effects']))
            self.assertFalse(meta['product_enemy_healing']['cpu_health_generations_or_schedule_supplied'])
            self.assertFalse(any(words[104400:H['BASE']]))

    def test_gpu_healing_projection_preserves_hp_credit_and_rejects_incomplete_receipts(self):
        from portable_product_healing import read_result
        from portable_enemy_healing_wire import OUTPUT as O
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        names=['a','b','c','d','e'];label='__enemy__:wave#1'
        meta=dict(product_enemy_healing=dict(nodes=['heal','wave'],bindings=[dict(kind=0,identity=0,label='__enemy__',run=-1),dict(kind=5,identity=0,label=label,run=1)],declarations={'enemy_healing':[dict(node='heal',targets=[label],amount=100.)]}))
        block=array.array('I',[0])*O['OUTPUT_WORDS'];h=O['OUTPUT_BASE'];a=h+O['RECEIPT_BASE'];pool=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];p=L['WORLD_ACTOR_POOL_STATE_BASE']+16
        def number(at,x):block[at:at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',x)))
        block[h:h+3]=array.array('I',[0x45484c31,1,1]);block[h+16]=1
        block[a:a+5]=array.array('I',[0,1,1,1,3]);number(a+6,1.);number(a+8,100.)
        for off,val in [(10,.5),(12,50.),(14,120.),(16,70.),(18,50.),(20,50.),(22,1000.)]:number(a+off,val)
        block[a+24]=block[a+25]=3;block[pool]=0x57485031;block[pool+1]=2
        block[p:p+4]=array.array('I',[1,1,0,3]);number(p+4,70.);number(L['DAMAGE_ACCOUNTING_STATE_BASE']+30,120.)
        block[L['WORLD_FRAME_OUTPUT_BASE']+16+1]=1
        actual=read_result(block,meta,names,2.)['enemy_healing'];r=actual['receipts'][0]
        self.assertEqual((r['hp_before'],r['hp_after'],r['effective_gain']),(880.,930.,50.))
        self.assertEqual(actual['final_scored_damage'],dict(a=120.,b=0.,c=0.,d=0.,e=0.))
        self.assertEqual(actual['final_adds'][0]['dealt'],70.)
        for at,value in [(h,0),(h+1,1025),(h+2,0),(h+16,0),(a+2,0),(a+3,0),(a+5,1),(a+25,4),(a+26,1),(pool+1,3),(a+32,1)]:
            bad=array.array('I',block);bad[at]=value
            with self.subTest(offset=at,value=value),self.assertRaises(UnsupportedPortable):read_result(bad,meta,names,2.)

    def test_original_anne_reduction_reaches_actual_product_healing_and_restores_aliases(self):
        from portable_enemy_healing_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'enemy_healing':copy.deepcopy(case['enemy_healing'])};before=copy.deepcopy(body)
        aliases=(timeline.simulate,sim.simulate)
        result=engine_worker.evaluate(body)
        self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        model=result['reference_models'];self.assertEqual(model['declarations'],body['reference_models'])
        self.assertEqual(model['evidence'],'declared-model-not-game-verification')
        receipts=model['enemy_healing']['receipts'];self.assertEqual(len(receipts),8)
        self.assertTrue(any(r.get('multiplier',1)<1 for r in receipts))
        self.assertTrue(any(r.get('effective_gain',0)>0 for r in receipts))
        self.assertIn(WARNING,result['app_warnings'])

    def test_target_carriers_and_stationary_add_healing_share_existing_executor(self):
        import portable_detail as product
        from detail_coverage import body_for
        from portable_enemy_healing_cases import fixtures
        from portable_enemy_ammo_wire import LAYOUT as A, MAGIC as AM
        from portable_enemy_healing_wire import AMMO_LAYOUT as H, MAGIC as HM
        from portable_backend import validate_composed_stride
        from portable_runtime import UnsupportedPortable
        case=fixtures()[0]
        for grouped in (False,True):
            names=['앤 : 미라클 페어리','사쿠라' if grouped else '아스카',
                '벨로타' if grouped else '미란다','도라','드레이크']
            for mode in ('fixed','accumulate'):
                for cover in (False,True):
                    body=copy.deepcopy(case['body']);body.update(squad=names,
                        profile=body_for(names,26)['profile'],duration=26,burst_gauge_mode=mode,
                        reference_models={'enemy_healing':copy.deepcopy(case['enemy_healing'])})
                    if cover:
                        body['reference_models']['cover_defense']=[dict(name=n,base_defense=1000.) for n in names]
                        body['manual_cover_sequences']={names[-1]:[dict(action='cover',t=.5,duration=.25)]}
                    prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                    with patch.object(sim,'execute',side_effect=AssertionError('No CPU battle during packing')):
                        source,iw,ow,words,meta=product.compile_product(prepared)
                    with self.subTest(grouped=grouped,mode=mode,cover=cover):
                        self.assertEqual(prepared,before)
                        self.assertEqual(source,'gpu/product_ammo_'+('cover_' if cover else '')+
                            ('fixed_' if mode=='fixed' else '')+('group_' if grouped else 'target_')+'battle_entry.slang')
                        validate_composed_stride(source,iw,ow)
                        self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                        self.assertEqual(words[A['BASE']:A['BASE']+4],[AM,1,0,len(meta['product_enemy_ammo']['bindings'])])
                        self.assertEqual(words[H['BASE']],HM)
                        self.assertEqual(meta['product_enemy_ammo']['declarations'],{})
                        self.assertEqual(meta['product_enemy_healing']['declarations'],{'enemy_healing':body['reference_models']['enemy_healing']})
                        self.assertTrue(meta['product_add_attacks'])
                    # An attacking world cannot inherit guessed magazines
                    # from the stationary empty-magazine admission.
                    attack=copy.deepcopy(body);attack['enemy']['patterns'].append(dict(id='incoming',kind='attack',spec=dict(atk=100,coeff=100,hits=1,target='all')))
                    incoming,_=product.prepare(attack)
                    if not cover:
                        with self.assertRaisesRegex(UnsupportedPortable,'explicit.*enemy_ammo'):
                            product.compile_product(incoming)

    def test_missing_sources_reject_before_shared_dispatch_and_legacy_stays_closed(self):
        from portable_product_programs import body_for_program
        import portable_detail as product
        body=body_for_program(ROOT,'accumulate')
        body['reference_models']={'enemy_healing':[dict(node='heal',targets=['__enemy__:wave#1'],amount=10)]}
        with patch.object(sim,'execute',side_effect=AssertionError('Static preparation must not simulate')):
            prepared,_=product.prepare(body)
        self.assertEqual(prepared['reference_models'],body['reference_models'])
        with patch.object(product,'execute',side_effect=AssertionError('No unconnected model may reach GPU')) as gpu:
            with self.assertRaisesRegex(ValueError,'Healing source must'):product.compile_product(prepared)
        gpu.assert_not_called()
        for flag in ('_compile_gpu','_compile_gpu_detail'):
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'no legacy GPU producer'):
                engine_worker.evaluate(dict(body,**{flag:True}))

    def test_invalid_or_unknown_models_fail_before_simulation(self):
        from portable_product_programs import body_for_program
        body=body_for_program(ROOT,'accumulate')
        for value in ([],True,{'lock_on':{}},{'enemy_healing':[]},{'enemy_healing':[dict(node='x',targets=['y'],amount=True)]}):
            with self.subTest(value=value),patch.object(sim,'execute',side_effect=AssertionError('Invalid declarations may not simulate')),self.assertRaises(ValueError):
                engine_worker.evaluate(dict(body,reference_models=value))

    def test_adapter_unwinds_after_execution_error_and_default_installs_nothing(self):
        aliases=(timeline.simulate,sim.simulate)
        with execution({}) as data:self.assertIsNone(data);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        declarations=normalize({'enemy_healing':[dict(node='x',targets=['y'],amount=1)]})
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with execution(declarations):
                self.assertIsNot(timeline.simulate,aliases[0]);raise RuntimeError('injected')
        self.assertEqual(aliases,(timeline.simulate,sim.simulate))

    @staticmethod
    def typed_lock_body(mode='accumulate',capacity=1e8):
        from portable_product_programs import body_for_program
        from coordinate_typed_actor_policy import FIELD_MODE
        from coordinate_typed_aim_runtime import POLICY
        body=body_for_program(ROOT,'coordinate-lock-'+mode);body['duration']=4.
        body['enemy']['patterns'][0]['until']['time']=5.
        models=body['reference_models'];locks=copy.deepcopy(models['lock_on'])
        for i,row in enumerate(locks['typed_bindings']):
            row.update(capacity=capacity,owner=[0,0,1],label='projectile-'+str(i))
        typed=dict(coord=models['coordinate']['coord'],bindings=copy.deepcopy(locks['typed_bindings']),
            geometry=dict(point_source='caster_aim',shapes=[dict(x=0.,y=0.,r=1000.,z=float(i)) for i in range(3)]),
            aim_policy={'mode':POLICY},actor_policy={'mode':FIELD_MODE})
        body['reference_models']=dict(typed_targets=typed,lock_on=locks)
        return body

    def test_typed_weapons_and_original_lock_skill_share_one_live_world(self):
        from destructible_world_runtime import DestructibleWorld
        from portable_detail import prepare,compile_product
        from portable_runtime import UnsupportedPortable
        for mode in ('fixed','accumulate'):
            for capacity in (1e8,1.):
                with self.subTest(mode=mode,capacity=capacity):
                    body=self.typed_lock_body(mode,capacity);before=copy.deepcopy(body)
                    aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
                    rng=timeline.random.getstate();worlds=[];original=DestructibleWorld.from_clock
                    def create(*a,**kw):
                        world=original(*a,**kw);worlds.append(world);return world
                    with patch.object(DestructibleWorld,'from_clock',side_effect=create):
                        result=engine_worker.evaluate(body)
                    self.assertEqual(len(worlds),1);self.assertTrue(worlds[0].finished)
                    self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
                    self.assertEqual(rng,timeline.random.getstate())
                    models=result['reference_models'];typed=models['typed_targets'];locks=models['lock_on']
                    self.assertEqual(typed['state'],locks['typed']['state'])
                    self.assertGreater(typed['packet_count'],0)
                    self.assertTrue(locks['pulses']);self.assertTrue(locks['shots'])
                    self.assertEqual(typed['packet_count'],len(typed['weapon_packets']))
                    self.assertTrue(all(a['completed'] for a in typed['skill_attacks']))
                    if capacity==1e8:
                        self.assertEqual(len(typed['skill_attacks']),1)
                        self.assertEqual(len(locks['typed']['attacks']),1)
                        skill=typed['skill_attacks'][0];lock=locks['typed']['attacks'][0]
                        self.assertEqual(skill['attack_id'],lock['attack_id']);self.assertEqual(skill['damage'],lock['damage'])
                        self.assertEqual(len(skill['receipts']),3)
                        # Native Lock On alone has the same scalar definitions;
                        # sharing weapon damage must reduce that same target HP.
                        standalone=copy.deepcopy(body)
                        standalone['reference_models']={'lock_on':copy.deepcopy(body['reference_models']['lock_on']),
                            'coordinate':dict(coord=copy.deepcopy(body['reference_models']['typed_targets']['coord']),logical_geometry=[])}
                        other=engine_worker.evaluate(standalone)['reference_models']['lock_on']['typed']['state']
                        self.assertLess(sum(t['remaining'] for t in typed['state']),sum(t['remaining'] for t in other))
                    else:
                        self.assertTrue(all(not t['alive'] and t['remaining']==0 for t in typed['state']))
                        self.assertTrue(any(p['broken'] for p in typed['weapon_packets']))
                    # Static preparation may not execute a CPU battle or silently
                    # omit any original skill while admitting the shared GPU consumer.
                    with patch.object(sim,'execute',side_effect=AssertionError('No battle as GPU input')):
                        prepared,_=prepare(body)
                        original_prepared=copy.deepcopy(prepared)
                        source,iw,ow,words,meta=compile_product(prepared)
                        self.assertEqual((iw,ow,len(words)),(123732,2945320,123732))
                        self.assertTrue(meta['product_typed_lock'])
                        self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                        self.assertEqual(prepared,original_prepared)

    def test_typed_lock_logical_adds_share_one_world_and_existing_packet_route(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from destructible_world_runtime import DestructibleWorld
        import coordinate_logical_actor_geometry as logical
        for mode in ('fixed','accumulate'):
            body=next(b for v,b in cases_for_program(ROOT,'typed-lock-'+mode) if v=='two-adds')
            before=copy.deepcopy(body);worlds=[];geometries=[]
            make=DestructibleWorld.from_clock;geometry=logical.LogicalGeometry
            def create(*a,**kw):
                w=make(*a,**kw);worlds.append(w);return w
            def capture(*a,**kw):
                value=geometry(*a,**kw);geometries.append(value);return value
            aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
            with patch.object(DestructibleWorld,'from_clock',side_effect=create),patch.object(logical,'LogicalGeometry',side_effect=capture):
                result=engine_worker.evaluate(body)
            self.assertEqual(len(worlds),1);self.assertTrue(worlds[0].finished)
            self.assertEqual(len(geometries),1)
            packets=geometries[0].data['packets']
            self.assertTrue(any(p['target'][0]==5 and p['damage']>0 for p in packets))
            self.assertTrue(all(not g.pending and not g.frames and not g.routing for g in geometries))
            self.assertTrue(any(any(h[0]==5 for h in shot['handles']) for shot in result['reference_models']['lock_on']['shots']))
            self.assertGreater(result['reference_models']['typed_targets']['packet_count'],0)
            self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU oracle in packing')):
                pre,_=prepare(body);source,iw,ow,words,meta=compile_product(pre)
            self.assertEqual((iw,ow),(123732,2945320))
            self.assertEqual(len(meta['product_coordinate']['declarations']['coordinate']['logical_geometry']),2)

    def test_typed_motion_uses_one_geometry_world_and_live_nearby_positions(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from destructible_world_runtime import DestructibleWorld
        import coordinate_logical_actor_geometry as logical
        for name in ('typed-fixed','typed-accumulate','typed-lock-fixed','typed-lock-accumulate'):
            body=copy.deepcopy(next(body for variant,body in cases_for_program(ROOT,name) if variant=='moving-long30'));before=copy.deepcopy(body)
            worlds=[];geometries=[];create=DestructibleWorld.from_clock;initialize=logical.LogicalGeometry.__init__
            def make(*a,**kw):
                value=create(*a,**kw);worlds.append(value);return value
            def attach(value,*a,**kw):
                initialize(value,*a,**kw);geometries.append(value)
            aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
            with patch.object(DestructibleWorld,'from_clock',side_effect=make),patch.object(logical.LogicalGeometry,'__init__',attach):result=engine_worker.evaluate(body)['reference_models']
            self.assertEqual((len(worlds),len(geometries)),(1,1));self.assertTrue(worlds[0].finished)
            self.assertTrue(result['typed_targets']['nearby_casts']);self.assertTrue(result['typed_targets']['weapon_packets'])
            casts=result['typed_targets']['nearby_casts']
            self.assertGreater(len({cast['recipient_count'] for cast in casts}),1)
            initial=body['reference_models']['typed_targets']['logical_geometry'][0]['shape']
            self.assertNotEqual(casts[0]['aim'],[initial['x'],initial['y']])
            movement=result['enemy_movement'];self.assertEqual(len(movement['generations']),3)
            self.assertTrue(any(segment['before']!=segment['after'] for frame in movement['frames'] for segment in frame['segments']))
            self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
            if name.startswith('typed-lock-'):self.assertTrue(result['lock_on']['shots'])
            with patch.object(sim,'execute',side_effect=AssertionError('No native positions in input')):
                pre,_=prepare(body);source,iw,ow,words,meta=compile_product(pre)
            self.assertEqual((iw,ow),(123732,2945320 if name.startswith('typed-lock-') else 2345384));validate_composed_stride(source,iw,ow)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))

    def test_typed_physical_history_preserves_order_across_spill_and_rejects_unowned_words(self):
        import array
        from portable_product_typed_movement import weapon_rows,END,LOCK_END,OUTPUT,LOCK_OUTPUT,WEAPON_CAPACITY,WEAPON_PREFIX_CAPACITY,SPILL_WORDS
        for base,spill,size in ((1769856,END,OUTPUT),(2032000,LOCK_END,LOCK_OUTPUT)):
            block=array.array('I',[0])*size
            first=base+170976+64
            block[first]=101;block[first+(WEAPON_PREFIX_CAPACITY-1)*24]=202;block[spill]=303
            rows=weapon_rows(block,base,WEAPON_PREFIX_CAPACITY+1,spill)
            self.assertEqual((len(rows),rows[0][0],rows[-2][0],rows[-1][0]),(2049,101,202,303))
            for at in (base+220192,spill+24,spill+SPILL_WORDS-1):
                block[at]=1
                with self.assertRaises(ValueError):weapon_rows(block,base,2049,spill)
                block[at]=0
            with self.assertRaises(ValueError):weapon_rows(block,base,WEAPON_CAPACITY+1,spill)
            with self.assertRaises(ValueError):weapon_rows(block,base,2049,spill+1)

    def test_typed_lock_extended_histories_reject_unused_quota_and_team_spill(self):
        import array
        from portable_product_typed_movement import quota_rows,team_rows,QUOTA_EXTRA,QUOTA_END,TEAM_EXTRA,TEAM_END,LOCK_OUTPUT
        from portable_original_lock_layout import QUOTAS,TEAMS
        from portable_product_coordinate_lock import SHIFT
        for reader,start,spill,end,limit,width in ((quota_rows,QUOTAS+SHIFT,QUOTA_EXTRA,QUOTA_END,2048,20),(team_rows,TEAMS+SHIFT,TEAM_EXTRA,TEAM_END,4096,8)):
            block=array.array('I',[0])*LOCK_OUTPUT;block[start]=101;block[start+(limit-1)*width]=202;block[spill]=303
            rows=reader(block,limit+1);self.assertEqual((rows[0][0],rows[-2][0],rows[-1][0]),(101,202,303))
            for at in (spill+width,end-1):
                block[at]=1
                with self.assertRaises(ValueError):reader(block,limit+1)
                block[at]=0
            with self.assertRaises(ValueError):reader(block,limit*2+1)

    def test_typed_motion_rejects_disagreeing_colliders_and_unowned_history(self):
        from portable_product_programs import cases_for_program
        from product_reference_models import normalize
        from portable_product_typed_movement import read_result,OUT,OUTPUT
        body=cases_for_program(ROOT,'typed-lock-fixed')[-1][1]
        for kind in ('order','coord','shape'):
            models=copy.deepcopy(body['reference_models']);motion=models['enemy_movement']
            if kind=='order':motion['logical_geometry'].reverse();motion['motion']['actors'].reverse()
            elif kind=='coord':motion['coord']['auto_aim'][0]+=1.
            else:motion['logical_geometry'][0]['shape']['x']+=1.
            with patch.object(sim,'execute',side_effect=AssertionError('Reject before battle')):
                with self.assertRaises(ValueError):normalize(models)
        import array
        block=array.array('I',[0])*OUTPUT
        self.assertIsNone(read_result(block,{},12.))
        block[OUT]=1
        with self.assertRaises(ValueError):read_result(block,{},12.)

    def test_shared_lock_nearby_world_filters_projectile_skills_including_empty_subset(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from destructible_world_runtime import DestructibleWorld
        for mode in ('fixed','accumulate'):
            for kinds in ((2,3),(2,2),(3,3)):
                body=copy.deepcopy(next(b for v,b in cases_for_program(ROOT,'typed-lock-'+mode) if v=='nearby-mixed'));typed=body['reference_models']['typed_targets']
                for model,key in ((typed,'bindings'),(body['reference_models']['lock_on'],'typed_bindings')):
                    for row,kind in zip(model[key],kinds):row['kind']=kind
                before=copy.deepcopy(body);worlds=[];original=DestructibleWorld.from_clock
                def create(*a,**kw):
                    value=original(*a,**kw);worlds.append(value);return value
                aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
                with patch.object(DestructibleWorld,'from_clock',side_effect=create):result=engine_worker.evaluate(body)['reference_models']
                self.assertEqual(len(worlds),1);self.assertTrue(worlds[0].finished)
                self.assertTrue(result['typed_targets']['nearby_casts']);self.assertTrue(result['lock_on']['shots'])
                self.assertEqual(result['typed_targets']['state'],result['lock_on']['typed']['state'])
                receipts=[p for attack in result['typed_targets']['skill_attacks'] for p in attack['receipts']]
                self.assertTrue(all(p['actor'][0]==2 for p in receipts))
                if 2 in kinds:self.assertTrue(receipts)
                else:self.assertEqual(receipts,[])
                self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
                with patch.object(sim,'execute',side_effect=AssertionError('No native world state in input')):
                    pre,_=prepare(body);source,iw,ow,words,meta=compile_product(pre)
                self.assertEqual((iw,ow,len(words)),(123732,2945320,123732));validate_composed_stride(source,iw,ow)
                self.assertEqual(words[115680+3],0 if len(set(kinds))>1 else kinds[0]);self.assertEqual(words[121394],1)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))

    def test_typed_nearby_selects_primary_neighbours_and_ordered_handles(self):
        import hashlib
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        for variant in ('tie','swap','primary-only'):
            body=copy.deepcopy(next(b for v,b in cases_for_program(ROOT,'typed-fixed') if v=='nearby-primary'));spec=body['reference_models']['typed_targets']
            expected=[[5,0,1],[5,1,1],[0,0,1]]
            if variant=='swap':
                spec['logical_geometry'][1]['shape']['x']=100.
                spec['logical_geometry'][2]['shape']['x']=10.
                expected=[[5,0,1],[5,2,1],[0,0,1]]
            if variant=='primary-only':spec['nearby_rules'][0]['base_radius']=0.;expected=[[5,0,1]]
            before=copy.deepcopy(body);aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
            result=engine_worker.evaluate(body)['reference_models']['typed_targets'];casts=result['nearby_casts']
            self.assertTrue(casts);digest=hashlib.sha256(b''.join(struct.pack('<IIII',*h,0) for h in expected)).hexdigest()
            self.assertTrue(all(c['recipient_count']==len(expected) and c['recipient_sha256']==digest and c['split'] for c in casts))
            self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
            with patch.object(sim,'execute',side_effect=AssertionError('No CPU-selected recipients in GPU input')):
                pre,_=prepare(body);source,iw,ow,words,meta=compile_product(pre)
            self.assertEqual((iw,ow,len(words)),(123732,2345384,123732));validate_composed_stride(source,iw,ow)
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))
            self.assertEqual(words[121392:121395],[0x4e524231,1,1])
            self.assertEqual(words[121392+32+5],1)
            bad=copy.deepcopy(body);bad['reference_models']['typed_targets']['nearby_rules'][0]['base_count']=2
            with patch.object(sim,'execute',side_effect=AssertionError('Invalid rule before battle')):
                invalid,_=prepare(bad)
                from portable_runtime import UnsupportedPortable
                with self.assertRaisesRegex(UnsupportedPortable,'original primary'):compile_product(invalid)

    def test_mixed_typed_weapons_use_actual_kind_after_front_target_breaks(self):
        from portable_product_programs import body_for_program
        from portable_detail import prepare,compile_product
        from destructible_battle_runtime import typed_battle
        for mode in ('fixed','accumulate'):
            for kinds in ((2,3),(3,2)):
                body=body_for_program(ROOT,'typed-'+mode);spec=body['reference_models']['typed_targets']
                for i,row in enumerate(spec['bindings']):
                    row['kind']=kinds[i];row['identity']=10
                    row['capacity']=1. if i==0 else 1e30
                for shape in spec['geometry']['shapes']:shape.update(x=0.,y=0.,r=1000.)
                before=copy.deepcopy(body);result=engine_worker.evaluate(body)['reference_models']['typed_targets']
                self.assertEqual({p['actor'][0] for p in result['weapon_packets']},{2,3})
                self.assertTrue(any(p['broken'] and p['actor'][0]==kinds[0] for p in result['weapon_packets']))
                self.assertEqual(body,before)
                with patch.object(sim,'execute',side_effect=AssertionError('No native oracle in mixed input')):
                    prepared,_=prepare(body);source,iw,ow,words,meta=compile_product(prepared)
                self.assertEqual(words[109968+3],0)
                self.assertEqual([words[109968+2328+i*12+1] for i in range(2)],list(kinds))
                # Legacy/private skill geometry still refuses a mixed universe.
                with self.assertRaisesRegex(ValueError,'one explicit actor kind'):
                    with typed_battle(spec['bindings'],modifier_model=True,typed_geometry=spec['geometry']):pass

    def test_typed_lock_requires_exact_logical_collider_registry_before_battle(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_runtime import UnsupportedPortable
        body=next(b for v,b in cases_for_program(ROOT,'typed-lock-accumulate') if v=='nearby-mixed')
        for variant in ('missing','foreign'):
            changed=copy.deepcopy(body);rows=changed['reference_models']['typed_targets']['logical_geometry']
            if variant=='missing':rows.pop()
            else:rows[-1]['label']='__enemy__:foreign#1'
            with patch.object(sim,'execute',side_effect=AssertionError('Registry mismatch before CPU battle')):
                pre,_=prepare(changed)
                with self.assertRaises((ValueError,UnsupportedPortable)):compile_product(pre)

    def test_standalone_typed_logical_geometry_keeps_complete_input_and_world(self):
        from portable_product_programs import cases_for_program
        from portable_detail import prepare,compile_product
        from portable_backend import validate_composed_stride
        from destructible_world_runtime import DestructibleWorld
        import coordinate_logical_actor_geometry as logical
        for mode in ('fixed','accumulate'):
            body=next(b for v,b in cases_for_program(ROOT,'typed-'+mode) if v=='mixed-two-adds');before=copy.deepcopy(body)
            worlds=[];geometries=[];make=DestructibleWorld.from_clock;geometry=logical.LogicalGeometry
            def create(*a,**kw):
                value=make(*a,**kw);worlds.append(value);return value
            def capture(*a,**kw):
                value=geometry(*a,**kw);geometries.append(value);return value
            with patch.object(DestructibleWorld,'from_clock',side_effect=create),patch.object(logical,'LogicalGeometry',side_effect=capture):result=engine_worker.evaluate(body)
            self.assertEqual(len(worlds),1);self.assertTrue(worlds[0].finished)
            self.assertTrue(any(p['target'][0]==5 and p['damage']>0 for p in geometries[0].data['packets']))
            self.assertTrue(result['reference_models']['typed_targets']['weapon_packets'])
            self.assertEqual(body,before)
            with patch.object(sim,'execute',side_effect=AssertionError('No native state in packing')):
                pre,_=prepare(body);source,iw,ow,words,meta=compile_product(pre)
            self.assertEqual((iw,ow,len(words)),(123732,2345384,123732));validate_composed_stride(source,iw,ow)
            self.assertEqual(words[115680:115683],[0x4c414731,1,2])
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(pre['effects']))))
            missing=copy.deepcopy(body);missing['reference_models']['typed_targets']['logical_geometry'].pop()
            from portable_runtime import UnsupportedPortable
            with patch.object(sim,'execute',side_effect=AssertionError('Incomplete colliders before battle')):
                bad,_=prepare(missing)
                with self.assertRaisesRegex(UnsupportedPortable,'Every configured'):compile_product(bad)

    def test_typed_lock_rejects_different_or_nonprojectile_worlds_before_simulating(self):
        body=self.typed_lock_body();base=body['reference_models']
        variants=[]
        changed=copy.deepcopy(base);changed['lock_on']['typed_bindings'].reverse();variants.append(changed)
        changed=copy.deepcopy(base);changed['lock_on']['typed_bindings'][0]['capacity']=3.;variants.append(changed)
        changed=copy.deepcopy(base)
        for model,key in ((changed['typed_targets'],'bindings'),(changed['lock_on'],'typed_bindings')):
            for row in model[key]:row['kind']=4
        variants.append(changed)
        with patch.object(sim,'execute',side_effect=AssertionError('Invalid world must not execute')):
            for value in variants:
                with self.subTest(value=value),self.assertRaises(ValueError):
                    engine_worker.evaluate(dict(body,reference_models=value))
        self.assertEqual(body['reference_models'],base)

    def test_shared_typed_lock_unwinds_on_error_and_rejects_foreign_runtime(self):
        from product_lock_model import execution as locks
        from product_typed_model import execution as typed
        models=normalize(self.typed_lock_body()['reference_models']);names=self.typed_lock_body()['squad']
        aliases=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage)
        holder={}
        with self.assertRaisesRegex(RuntimeError,'shared abort'):
            with typed(models['typed_targets'],names,runtime=holder):
                with locks(models['lock_on'],names,typed_runtime=holder):raise RuntimeError('shared abort')
        self.assertFalse(holder['active'])
        self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))
        for runtime in (holder,{'active':True,'bindings':[],'data':{}},{'active':True,'bindings':models['lock_on']['typed_bindings'],'data':{'worlds':[object()],'managers':[]}}):
            with self.subTest(runtime=runtime),self.assertRaises(ValueError):
                with locks(models['lock_on'],names,typed_runtime=runtime):pass
            self.assertEqual(aliases,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.calc_damage))

if __name__=='__main__':unittest.main()
