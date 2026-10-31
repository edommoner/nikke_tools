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
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
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

if __name__=='__main__':unittest.main()
