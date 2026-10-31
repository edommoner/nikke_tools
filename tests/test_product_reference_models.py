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
        self.assertEqual((source,iw,ow,len(words)),('gpu/product_lock_battle_entry.slang',109536,1310720,109536))
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
        with self.assertRaisesRegex(UnsupportedPortable,'explicit reference_models.lock_on'):product.compile_product(dict(prepared,reference_models={}))
        changed=copy.deepcopy(prepared);next(r['effect'] for r in changed['effects'] if r['effect'].get('stat')=='lock_on')['duration']=1
        with self.assertRaisesRegex(ValueError,'Unchanged original'):product.compile_product(changed)
        import ast
        transform=QueueHooks();transform.visit(ast.parse('def simulate():\n def _land(ev,t):\n  if boss is not None and boss.has_adds:pass\n'))
        self.assertNotEqual(transform.counts,dict(emission=1,landing=1,route=1,clock=1))

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
        with self.assertRaisesRegex(UnsupportedPortable,'manual cover'):product.compile_product(bad)
        for value in (True,float('nan'),-1,181):
            bad=copy.deepcopy(prepared);bad['policies']['config']['first_burst_time']=value
            with self.subTest(value=value),self.assertRaisesRegex(UnsupportedPortable,'finite binary64'):product.compile_product(bad)

    def test_lock_on_decoder_checks_complete_arenas_and_reserved_words(self):
        import portable_detail as product
        from portable_product_locks import read_result,OUTPUT
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
        b[PACKET_HEAD+OFFSET]=MAGIC;b[FATE_HEAD]=FATE_MAGIC;b[786432]=0x44425431
        b[789250:789253]=array.array('I',[1,1,1])
        self.assertEqual(read_result(b,meta,3)['lock_on']['typed'],dict(time=0.,finished=True,state=[],attacks=[]))
        for at,value in ((HEAD+OFFSET+1,257),(HEAD+OFFSET+6,1),(PACKET_HEAD+OFFSET+1,1),(QUOTA_HEAD+2,2049),(FATE_HEAD+1,1),(OUTPUT-1,1),(787456,1),(789252,0)):
            bad=array.array('I',b);bad[at]=value
            with self.subTest(at=at),self.assertRaises(UnsupportedPortable):read_result(bad,meta,3)
        with self.assertRaises(UnsupportedPortable):read_result(b[:-1],meta,3)

    def test_lock_on_typed_no_expiry_sentinel_is_exact_and_bound_to_declared_target(self):
        import portable_detail as product
        from portable_product_locks import read_result,OUTPUT
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
            # Other dedicated banks remain explicit unsupported combinations.
            prepared['reference_models']['enemy_healing']=[dict(node='world',targets=['x'],amount=1)]
            with self.assertRaisesRegex(UnsupportedPortable,'combined consumer wire'):
                product.compile_product(prepared)

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
