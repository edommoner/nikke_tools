"""Product payload parity and fail-closed paths, without a GPU or CPU replay."""
import array,copy,hashlib,json,os,sys,tempfile,unittest
from contextlib import nullcontext,contextmanager
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as product
import portable_product_artifact as artifacts
from portable_projectile_roster_input import compile_projectile_battle

class PortableDetail(unittest.TestCase):
    def test_original_reload_cancel_policy_reaches_existing_ammo_executor(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        body=selected_profile_bodies(['홍련 : 흑영'],0)[0][2]
        body.update(duration=20,shooting_policy='character',burst_gauge_mode='accumulate')
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU schedule')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            _,_,_,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        flags=[words[L['WEAPON_QUANTITY_BASE']+who*L['WEAPON_QUANTITY_WORDS']+3] for who in range(5)]
        owners=[c['name'] for c in prepared['chars']]
        self.assertEqual(flags,[int(n=='홍련 : 흑영') for n in owners])
        self.assertEqual(meta['real_prepared_input']['policy']['controls'],prepared['policies']['controls'])
        for invalid in [dict(cancel_on_full=1),dict(cancel_on_full=True,when='combat_start')]:
            changed=copy.deepcopy(prepared);changed['chars'][0]['control']={'reload':invalid}
            changed['policies']['controls'][changed['chars'][0]['name']]=changed['chars'][0]['control']
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):product.compile_product(changed)

    def test_add_debuffs_reuse_external_definitions_and_exact_firing_descriptor(self):
        from portable_product_programs import PROGRAMS,body_for_program
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_specs import LIMITS as L,FIELDS as F
        import struct
        for program in (n for n in PROGRAMS if n.startswith('add-')):
            body=body_for_program(ROOT,program)
            spec=body['enemy']['patterns'][0]['spec'];spec['atk']=1234
            spec['attack'].update(atk=3456,debuffs=[dict(stat='atk_pct',value=-20),
                dict(stat='dot',coeff=25,interval=.125,duration=1)])
            with self.subTest(program=program),patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,_,_,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual(source,PROGRAMS[program]['source'])
            anchor=L['WORLD_FRAME_PAYLOAD_BASE'];firing=A['BASE']+A['ROW_BASE']+8
            self.assertEqual(words[anchor:anchor+16],words[firing:firing+16])
            self.assertEqual(words[L['WORLD_FRAME_INPUT_BASE']+16+6],0,'The anchor must not schedule a BODY shot')
            rows=meta['boss_debuffs']['definitions'];self.assertEqual(len(rows),2)
            self.assertEqual(words[anchor+4:anchor+8],[rows[0]+1,2,0x42444631,1])
            self.assertTrue(all(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['OWNER']]==5 for row in rows))
            row=rows[1];at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            self.assertEqual(words[at+F['STAT']],95)
            fixed=L['DEFINITION_EXTRA_BASE']+row*L['DEFINITION_EXTRA_WORDS']+4
            self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[fixed:fixed+2]))[0],3456)
            self.assertFalse(meta['boss_debuffs']['cpu_recipients_or_schedule_supplied'])

    def test_add_product_reuses_existing_prefix_and_literal_attack_retirement_wire(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_product_add_attack import lower
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_backend import validate_composed_stride
        profiles=selected_profile_bodies(['미란다','벨로타','아스카'],0)
        by_name={row[0]:row[2] for row in profiles}
        mixed=copy.deepcopy(by_name['아스카']);mixed['profile']['chars'].update(by_name['벨로타']['profile']['chars'])
        mixed['squad']=['아스카','벨로타','미란다','도라','드레이크']
        for name,kind,original in [('미란다','',by_name['미란다']),('벨로타','group_',by_name['벨로타']),
                ('아스카','target_',by_name['아스카']),('mixed','group_target_',mixed)]:
            for mode in ('accumulate','fixed'):
                body=copy.deepcopy(original)
                body.update(duration=3,burst_gauge_mode=mode)
                body['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(
                    name='escort',count=2,hp=1e12,attack_at=.25,self_destruct=True,
                    attack=dict(atk=1234,coeff=50,hits=2,interval=.5,target='random:2')))]
                with self.subTest(name=name,mode=mode),patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                    prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                    source,iw,ow,words,meta=product.compile_product(prepared)
                    lowered,_=lower(prepared);_,base_iw,_,base_words,_=product.compile_product(lowered)
                    self.assertEqual(prepared,before)
                    self.assertEqual(words[:base_iw],base_words)
                    self.assertFalse(any(words[base_iw:A['BASE']]))
                    self.assertEqual((iw,ow,len(words)),(A['INPUT_WORDS'],A['OUTPUT_WORDS'],A['INPUT_WORDS']))
                    self.assertEqual(source,'gpu/product_add_'+('fixed_' if mode=='fixed' else '')+kind+'battle_entry.slang')
                    validate_composed_stride(source,iw,ow)
                    at=A['BASE']+A['ROW_BASE']
                    self.assertEqual(words[at:at+2],[2,2])
                    self.assertEqual(words[at+4:at+8],[1,0,1070596096,0])
                    self.assertEqual(meta['product_add_attacks']['labels'],['','escort#1','escort#2'])
                    self.assertFalse(meta['product_add_attacks']['CPU_schedule_or_state_supplied'])

    def test_add_source_projection_rejects_unknown_slots_and_misbound_nodes(self):
        from portable_product_add_attack import query_sources
        from portable_add_attack_battle_wire import MAGIC,LAYOUT as A
        from portable_add_self_destruct_wire import MAGIC as RM,LAYOUT as R
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        block=array.array('I',[0])*A['OUTPUT_WORDS'];h=L['WORLD_FRAME_OUTPUT_BASE']
        block[A['OUTPUT_BASE']]=MAGIC;block[R['OUTPUT_BASE']]=RM
        block[h+2]=1;block[h+2832:h+2832+6]=array.array('I',[3,2,0,0,0,1])
        block[A['OUTPUT_BASE']+1]=1;m=A['OUTPUT_BASE']+A['MAP_BASE']
        block[m:m+2]=array.array('I',[1,3])
        meta={'product_add_attacks':dict(labels=['','escort#1'],source_nodes=[-1,2])}
        self.assertEqual(query_sources(block,meta),{0:'escort#1'})
        for slot,generation,node in [(2,3,2),(1,0,2),(1,3,1)]:
            block[m:m+2]=array.array('I',[slot,generation]);block[h+2833]=node
            with self.assertRaises(UnsupportedPortable):query_sources(block,meta)

    def test_dot_down_ordinal_preserves_queued_attack_and_revive_order(self):
        from portable_world_result import order_squad_logs
        dot=dict(time=1.,pattern='dot',event='down',outcome='')
        attack=dict(time=1.,pattern='shot',event='down',outcome='')
        plan=[0,{**dot,'direct_downs_before':0},dict(time=1.,revive_after_downs=1)]
        self.assertEqual(order_squad_logs(plan,{0:[attack]}),
            [dot,dict(time=1.,pattern='',event='revive',outcome=''),attack])

    def test_boss_attack_debuffs_preserve_external_identity_and_static_order(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        from calculator.boss_pattern import DEBUFF_STATS
        body=selected_profile_bodies(['미란다'],0)[0][2]
        body.update(duration=4,burst_gauge_mode='accumulate')
        entries=[dict(stat=k,**({'value':v*10} if v else {}),**({} if k=='atk_pct' else {'duration':2})) for k,v in DEBUFF_STATS.items() if k!='dot']
        body['enemy']['patterns']=[dict(id='native-hit',kind='attack',delay=.5,spec=dict(coeff=100,target='all',debuffs=entries))]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in lowering')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            source,_,_,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(source,'gpu/product_battle_entry.slang')
        rows=meta['boss_debuffs']['definitions'];self.assertEqual(len(rows),14)
        payload=L['WORLD_FRAME_PAYLOAD_BASE']
        self.assertEqual(words[payload+4:payload+8],[rows[0]+1,14,0x42444631,1])
        self.assertEqual(meta['real_prepared_input']['prepared_effects'],len(prepared['effects']))
        self.assertFalse(meta['boss_debuffs']['cpu_recipients_or_schedule_supplied'])
        for row,entry in zip(rows,entries):
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            self.assertEqual(words[at+F['OWNER']],5)
            self.assertEqual(words[at+F['RECIPIENTS']],0)
            self.assertEqual(words[at+F['FLAGS']],0)
            self.assertEqual(meta['effects'][row],'native-hit·'+entry['stat'])
            self.assertEqual(words[L['RECIPIENT_BASE']+row*8+7],0)
        from portable_world_roster_input import compile_world_battle
        with self.assertRaisesRegex(ValueError,'Attack debuff payload is not connected'):compile_world_battle(prepared)

    def test_boss_dot_lowers_only_literal_coeff_interval_and_attack(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_runtime_layout import runtime_initializer
        import struct
        body=selected_profile_bodies(['미란다'],0)[0][2]
        body['enemy']['patterns']=[dict(kind='attack',spec=dict(atk=123456,coeff=100,target='all',debuffs=[dict(stat='dot',coeff=10,interval=.5,duration=2)]))]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in lowering')):
            prepared,_=product.prepare(body)
            before=copy.deepcopy(prepared);_,_,_,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        row=meta['boss_debuffs']['definitions'][0];at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        self.assertEqual((words[at+F['STAT']],words[at+F['OWNER']],words[at+F['RECIPIENTS']]),(95,5,0))
        number=lambda pos:struct.unpack('<d',struct.pack('<II',*words[pos:pos+2]))[0]
        self.assertEqual((number(at+F['VALUE']),number(at+F['INTERVAL'])),(10,.5))
        self.assertEqual(number(L['DEFINITION_EXTRA_BASE']+row*L['DEFINITION_EXTRA_WORDS']+4),123456)
        self.assertEqual(runtime_initializer(),(ROOT/'gpu/runtime_init.slang').read_text())

    def test_standalone_boss_debuff_uses_the_same_external_definitions_without_damage(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        body=selected_profile_bodies(['미란다'],0)[0][2]
        body.update(duration=4,burst_gauge_mode='fixed')
        body['enemy']['patterns']=[dict(id='cast',kind='debuff',delay=.5,
            spec=dict(target='slot:2',hits=3,interval=.5,
                debuffs=[dict(stat='atk_pct',value=-20,duration=1)]))]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('Static input only')):
            prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
            source,_,_,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,original)
        self.assertEqual(source,'gpu/product_fixed_battle_entry.slang')
        at=L['WORLD_FRAME_PAYLOAD_BASE']
        self.assertEqual(words[at:at+4],[33,0,0,0])
        self.assertEqual(words[at+8:at+12],[0,0,0,0])
        self.assertEqual(words[at+5:at+7],[1,0x42444631])
        self.assertEqual(meta['effects'][meta['boss_debuffs']['definitions'][0]],'cast·atk_pct')

    def test_boss_debuffs_compose_with_all_product_binding_families(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        belorta=selected_profile_bodies(['벨로타'],0)[0][2]
        asuka=selected_profile_bodies(['아스카'],0)[0][2]
        mixed=copy.deepcopy(asuka);mixed['profile']['chars'].update(belorta['profile']['chars'])
        mixed['squad']=['아스카','벨로타','미란다','도라','드레이크']
        for body,kind in [(belorta,'group'),(asuka,'target'),(mixed,'group_target')]:
            body=copy.deepcopy(body);body.update(duration=4,burst_gauge_mode='fixed')
            body['enemy']['patterns']=[dict(id='incoming',kind='attack',spec=dict(coeff=100,target='all',debuffs=[dict(stat='atk_pct',value=-10,duration=2)]))]
            with self.subTest(kind=kind),patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('Static only')):
                prepared,_=product.prepare(body);source,_,_,words,meta=product.compile_product(prepared)
                self.assertEqual(source,'gpu/product_fixed_'+kind+'_battle_entry.slang')
                for row in meta['boss_debuffs']['definitions']:
                    self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['OWNER']],5)

    def world_projection_fixture(self):
        """Synthetic readback for format tests; never GPU execution evidence."""
        from portable_specs import LIMITS as limits
        body=copy.deepcopy(self.fixture['body'])
        body['enemy']['patterns']=[dict(id='armor',kind='buff',enemy=dict(def_mult=2),until=dict(time=1)),
            dict(id='salvo',kind='attack',delay=.5,spec=dict(coeff=100,atk=100,target='slot:3',hits=1)),
            dict(id='wave',kind='summon',spec=dict(count=1,hp=100))]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU schedule in lowering')):
            prepared,run=product.prepare(body)
            before=copy.deepcopy(prepared);_,_,_,words,meta=product.compile_product(prepared)
            self.assertEqual(prepared,before)
        block=array.array('I',[0])*limits['WORLD_FRAME_OUTPUT_WORDS'];head=limits['WORLD_FRAME_OUTPUT_BASE']
        number=lambda value:product.struct.unpack('<II',product.struct.pack('<d',value))
        events=[(1,0,0,0.),(1,1,0,.5),(1,2,0,.5),(3,1,0,.5),(4,0,0,.75),(5,2,1,.8),
                (2,0,2,1.),(2,1,4,1.),(2,2,4,1.)]
        block[head+2]=len(events);block[head+5]=len(events);block[head+6]=1;block[head+7]=1
        for i,(kind,node,arg,t) in enumerate(events):
            at=head+2832+i*6;block[at:at+6]=array.array('I',[kind,node,arg,*number(t),1 if kind==3 else 0])
        at=limits['WORLD_FRAME_HIT_BASE'];block[at:at+4]=array.array('I',[*number(.5),1,2<<3])
        for offset,value in ((4,30.),(6,0.),(8,20.),(10,0.),(12,10.),(14,1000.)):
            block[at+offset:at+offset+2]=array.array('I',number(value))
        return body,prepared,run,meta,block

    def test_boss_lowering_keeps_literal_identity_and_all_original_effects(self):
        body,prepared,run,meta,_=self.world_projection_fixture()
        self.assertFalse(prepared['cpu_battle_executed'])
        self.assertEqual(meta['real_prepared_input']['prepared_effects'],len(prepared['effects']))
        self.assertEqual(meta['product_world']['nodes'],[dict(id=p['id'],kind=p['kind']) for p in body['enemy']['patterns']])
        self.assertTrue(meta['product_world']['literal_pattern_identity_only'])
        self.assertFalse(meta['product_world']['cpu_schedule_or_state_supplied'])

    def test_complete_product_boss_and_incoming_projection_uses_gpu_history(self):
        body,prepared,run,meta,block=self.world_projection_fixture()
        with patch.object(product,'decode',return_value=copy.deepcopy(self.fixture['gpu_projection'])):
            payload=product.decode_payload(body,prepared,run,meta,block)
        self.assertEqual(payload['boss_patterns'],body['enemy']['patterns'])
        self.assertEqual(payload['app_warnings'][0],'設定したボス行動で計算した参考値です。実機のギミックや生存の再現は未検証です。')
        self.assertEqual([(r['pattern'],r['kind'],r['event'],r['outcome']) for r in payload['boss_timeline']],
            [('armor','buff','start',None),('salvo','attack','start',None),('wave','summon','start',None),
             ('armor','buff','dispel',None),('armor','buff','end','expired'),('salvo','attack','end','end'),('wave','summon','end','end')])
        self.assertEqual(payload['incoming_hits'],[dict(time=.5,pattern='salvo',target=prepared['chars'][2]['name'],damage=30.,
            pierce=False,decoy=0.,shield=0.,cover=20.,hp=10.,hp_after=1000.,down=False,by='')])
        from portable_world_result import read_histories
        self.assertIn('destroy',[r['event'] for r in read_histories(block,meta['product_world']['nodes'])['boss_log']])

    def test_bad_world_capacity_identity_owner_and_nonfinite_hits_are_rejected(self):
        from portable_specs import LIMITS as limits
        body,prepared,run,meta,block=self.world_projection_fixture();head=limits['WORLD_FRAME_OUTPUT_BASE'];hit=limits['WORLD_FRAME_HIT_BASE']
        def nonfinite(words):words[hit+14:hit+16]=array.array('I',product.struct.unpack('<II',product.struct.pack('<d',float('nan'))))
        for mutate in (lambda words:words.__setitem__(head+2,2049),lambda words:words.__setitem__(head+2833,32),
                       lambda words:words.__setitem__(hit+3,7<<3),nonfinite):
            changed=array.array('I',block);mutate(changed)
            with patch.object(product,'decode',return_value=copy.deepcopy(self.fixture['gpu_projection'])):
                with self.assertRaises(product.UnsupportedPortable):product.decode_payload(body,prepared,run,meta,changed)

    def test_native_groups_use_shared_boss_compiler_without_widening_declared_routing(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_battle_attack_group_input import compile_battle
        body=selected_profile_bodies(['벨로타'],0)[0][2]
        body.update(duration=4,burst_gauge_mode='fixed')
        body['enemy']['parts']=[dict(name='group-part',hp=1,reach=1)]
        body['enemy']['patterns']=[dict(id='volley',kind='attack',spec=dict(coeff=100,atk=100,target='all',hits=2,interval=.1))]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU schedule in lowering')):
            prepared,_=product.prepare(body);source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(source,'gpu/product_fixed_group_battle_entry.slang')
        self.assertEqual(len(words),iw)
        self.assertEqual(meta['product_parts'],[dict(name='group-part',slot=1,node=0)])
        self.assertEqual(meta['real_prepared_input']['declared_attack_group_policy']['routing'],'native')
        self.assertFalse(meta['product_world']['cpu_schedule_or_state_supplied'])
        with self.assertRaisesRegex(ValueError,'plain idle/summon'):compile_battle(prepared,routing='all-logical-enemies')
        invalid=copy.deepcopy(prepared);invalid['enemy']['patterns']=[dict(kind='summon',spec=dict(self_destruct=True))]
        with self.assertRaisesRegex(ValueError,'declared world consumer'):compile_battle(invalid,routing='native')

    def test_original_character_shooting_controls_reach_existing_shared_wire(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        for name,key in [('앨리스','tap_fire'),('밀크 : 블루밍 바니','hold'),
                         ('에이다','hold'),('라푼젤 : 퓨어 그레이스','sequence')]:
            body=selected_profile_bodies([name],0)[0][2]
            mode='accumulate' if key=='tap_fire' or name=='밀크 : 블루밍 바니' else 'fixed'
            body.update(shooting_policy='character',duration=20,burst_gauge_mode=mode)
            if name=='앨리스':body['profile']['chars'][name]['equip_skills']['charge_speed_pct']=9.26
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU schedule')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
            self.assertIn(key,next(c['control'] for c in prepared['chars'] if c['name']==name))
            self.assertEqual(prepared,before);self.assertEqual(len(words),iw)
            self.assertEqual(meta['real_prepared_input']['policy']['controls'],prepared['policies']['controls'])
            self.assertEqual(words[L['WORLD_CONTROL_INPUT_BASE']+1],2 if mode=='accumulate' else 4)
            self.assertFalse(meta['real_prepared_input']['cpu_battle_executed'])
            invalid=copy.deepcopy(prepared)
            invalid['chars'][0]['control']={'cover':{'policy':'own_full_burst'}}
            invalid['policies']['controls'][invalid['chars'][0]['name']]=invalid['chars'][0]['control']
            with self.assertRaisesRegex(ValueError,'Cover/reload/aim/burst'):product.compile_product(invalid)

    def test_product_control_history_uses_gpu_intervals_and_rejects_corruption(self):
        from portable_world_result import read_product_control_log
        from portable_specs import LIMITS as L
        names=[c['name'] for c in self.prepared['chars']]
        labels=[[dict(mode='tap',producer='always'),dict(mode='tap',producer='always')],[],[],[],[]]
        meta=dict(product_control_labels=labels,states={})
        block=array.array('I',[0])*786432;h=L['WORLD_CONTROL_HEAD_BASE'];base=L['WORLD_CONTROL_TRACE_BASE']
        block[h]=0x57434831;block[h+1]=5;block[h+8]=1;block[h+13]=0x50434c31
        number=lambda t:array.array('I',product.struct.unpack('<II',product.struct.pack('<d',t)))
        for i,(kind,who,t,row,reason) in enumerate([(0,1,0.,0,0),(2,0,.2,1,0),(3,0,2.,1,0),(2,0,2.,2,0),(3,0,3.,2,1)]):
            a=base+i*8;block[a:a+8]=array.array('I',[kind,who,*number(t),row,reason,0,0])
        log=read_product_control_log(block,meta,names,8.)
        self.assertEqual(len(log.control_log),1)
        self.assertEqual((log.control_log[0].t0,log.control_log[0].t1),(.2,3.))
        self.assertEqual(log.control_occupancy()['by_char'],{names[0]:2.8})
        self.assertEqual(log.control_summary(),f'조작 구간: {names[0]} 2.8s')
        changed=array.array('I',block);changed[h+1]=2
        self.assertEqual(read_product_control_log(changed,meta,names,8.).control_log[0].t1,8.)
        for offset,value in [(h+1,221),(h+13,0),(base+8,9),(base+9,7),(base+12,9),(base+8+3,0x7ff80000)]:
            bad=array.array('I',block);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(product.UnsupportedPortable):read_product_control_log(bad,meta,names,8.)
        bad=array.array('I',block);bad[base+16+2:base+16+4]=number(.1)
        with self.assertRaises(product.UnsupportedPortable):read_product_control_log(bad,meta,names,8.)

    def test_fixed_tap_preserves_original_masks_controls_and_all_nonheader_words(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        base=L['WORLD_CONTROL_INPUT_BASE']
        for name in ('앨리스','밀크 : 블루밍 바니'):
            body=selected_profile_bodies([name],0)[0][2]
            body.update(shooting_policy='character',duration=20,burst_gauge_mode='fixed')
            if name=='앨리스':body['profile']['chars'][name]['equip_skills']['charge_speed_pct']=9.26
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,fixed,meta=product.compile_product(prepared)
                accumulated=copy.deepcopy(prepared);accumulated['policies']['config']['burst_gauge_mode']='accumulate'
                _,_,_,original,_=product.compile_product(accumulated)
            self.assertEqual(prepared,before)
            self.assertEqual(source,'gpu/product_fixed_battle_entry.slang')
            self.assertEqual(original[base+1],2);self.assertEqual(fixed[base+1],5)
            self.assertTrue(0<original[base+5]<32);self.assertEqual(fixed[base+10],original[base+5])
            self.assertEqual(fixed[:base],original[:base]);self.assertEqual(fixed[base+16:],original[base+16:])
            self.assertEqual(fixed[base+2:base+5],original[base+2:base+5]);self.assertFalse(any(fixed[base+11:base+16]))
            self.assertEqual(meta['real_prepared_input']['policy']['controls'],prepared['policies']['controls'])

    def test_original_parts_lowering_and_gpu_result_projection_are_lossless(self):
        from portable_specs import LIMITS as L
        from portable_world_result import read_product_parts
        body=copy.deepcopy(self.fixture['body'])
        body['enemy']['parts']=[dict(name='breakable',hp=10,reach=1),dict(name='unbreakable',hp=0,reach=3)]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in parts preparation')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            _,_,_,_,meta=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(meta['product_parts'],[dict(name='breakable',slot=1,node=0),dict(name='unbreakable',slot=2,node=0)])
        self.assertEqual(meta['real_prepared_input']['actor_bindings'],3)
        block=array.array('I',[0])*786432;head=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];state=L['WORLD_ACTOR_POOL_STATE_BASE'];extra=L['COUNTER_LANDING_EXTRA_BASE'];graph=L['WORLD_FRAME_OUTPUT_BASE']
        number=lambda x:array.array('I',product.struct.unpack('<II',product.struct.pack('<d',x)))
        block[head:head+2]=array.array('I',[0x57485031,3]);block[graph+2]=1
        block[graph+2832:graph+2838]=array.array('I',[5,0,1,*number(.25),0])
        for slot in (1,2):block[state+slot*16]=1
        block[state+16+2]=1;block[state+16+3]=2;block[state+16+6:state+16+8]=number(5000.)
        block[extra+4]=3;block[extra+6:extra+8]=number(2500.75)
        block[state+32+1]=1;block[extra+8]=5;block[extra+10:extra+12]=number(2800.5)
        self.assertEqual(read_product_parts(block,meta,body['enemy']['parts'],30),[
            dict(name='breakable',damage=7500.75,hits=5,destroyed=True,destroyed_at=.25),
            dict(name='unbreakable',damage=2800.5,hits=5,destroyed=False,destroyed_at=None)])
        for offset,value in [(head,0),(head+1,2),(state+16,2),(state+18,0),(graph+2,2049),(graph+2833,31),(extra+7,0x7ff80000)]:
            bad=array.array('I',block);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(product.UnsupportedPortable):read_product_parts(bad,meta,body['enemy']['parts'],30)

    def descriptor(self,folder,**changes):
        document=dict(schema=1,programs={product.SOURCE:dict(battle_package=folder,request=dict(package=folder,capture=folder))})
        document.update(changes)
        path=Path(folder)/'programs.json';path.write_text(json.dumps(document))
        return path

    def test_fixed_burst_changes_only_authored_control_header_and_keeps_source_input(self):
        from portable_specs import LIMITS as limits
        base=limits['WORLD_CONTROL_INPUT_BASE']
        fixed=copy.deepcopy(self.prepared)
        fixed['policies']['config'].update(burst_gauge_mode='fixed',first_burst_time=1.25)
        delays=[0.,.5,3.,1.,2.]
        for char,delay in zip(fixed['chars'],delays):char['burst_regen_time']=delay
        before=copy.deepcopy(fixed)
        accumulate=copy.deepcopy(fixed);accumulate['policies']['config']['burst_gauge_mode']='accumulate'
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle or schedule in lowering')):
            source,iw,ow,words,meta=product.compile_product(fixed)
            _,aiw,aow,original,_=product.compile_product(accumulate)
        self.assertEqual(fixed,before)
        self.assertEqual(source,'gpu/product_fixed_battle_entry.slang')
        self.assertEqual((iw,ow),(aiw,aow))
        self.assertEqual(words[:base],original[:base])
        self.assertEqual(words[base+16:],original[base+16:])
        self.assertEqual(words[base:base+5],[original[base],4,*original[base+2:base+5]])
        self.assertEqual(words[base+10:base+16],[0]*6)
        self.assertEqual(words[base+5],0x46424731)
        self.assertEqual(product.struct.unpack('<dd',product.struct.pack('<4I',*words[base+6:base+10])),(1.25,3.))
        self.assertEqual(meta['product_fixed_burst']['member_regen_seconds'],delays)
        self.assertFalse(meta['product_fixed_burst']['CPU_state_or_schedule_as_input'])
        self.assertEqual(meta['real_prepared_input']['policy'],fixed['policies'])
        from portable_backend import validate_composed_stride
        validate_composed_stride(source,iw,ow)

    def test_real_unsupported_effect_reports_owner_and_definition_without_dispatch(self):
        from portable_original_identity_inventory import selected_profile_bodies
        for name,stat in [('얀','force_move'),('유니','enemy_movement_disable'),('벨벳','ammo_charge_pct')]:
            body=selected_profile_bodies([name],0)[0][2];body.update(burst_gauge_mode='fixed',compute_backend='metal_detail')
            prepared,run=product.prepare(body);before=copy.deepcopy(prepared)
            with self.assertRaises(product.UnsupportedPortable) as raised:product.compile_product(prepared)
            context=raised.exception.effect_context
            self.assertEqual(context['character'],name)
            self.assertEqual(context['stat'],stat)
            self.assertTrue(context['effect'])
            original=next(row['effect'] for row in prepared['effects'] if row['owner']==name and row['effect']['stat']==stat)
            self.assertEqual(context['target'],original['target'])
            self.assertEqual(prepared,before)
            with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,NIKKE_DETAIL_CAPTURE_ROOT=folder),\
                 patch.object(product,'prepare',return_value=(prepared,run)),\
                 patch.object(product,'execute',side_effect=AssertionError('No GPU on unsupported definition')) as dispatch,\
                 patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
                output=product.evaluate(body)
                record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                self.assertEqual(record['unsupported'],output['compute']['unsupported'])
            self.assertEqual(output['compute']['backend'],'cpu')
            self.assertEqual(output['compute']['unsupported'][0],dict(context,reason=str(raised.exception)))
            dispatch.assert_not_called()

    def test_fixed_delay_invalid_numbers_stop_before_lowering(self):
        for value in (True,float('nan'),float('inf'),-.1,181,'2'):
            for field in ('first','regen'):
                fixed=copy.deepcopy(self.prepared);fixed['policies']['config']['burst_gauge_mode']='fixed'
                if field=='first':fixed['policies']['config']['first_burst_time']=value
                else:fixed['chars'][2]['burst_regen_time']=value
                with self.subTest(field=field,value=value),patch.object(product,'compile_projectile_battle',side_effect=AssertionError('No lowering on invalid delay')):
                    with self.assertRaisesRegex(ValueError,'Fixed burst delays'):product.compile_product(fixed)

    def test_fixed_product_timeline_retains_bursts_without_accumulate_only_records(self):
        body={**self.fixture['body'],'burst_gauge_mode':'fixed'}
        with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
            actual=product.decode_payload(body,self.prepared,self.prepared_run,self.metadata,[])
        expected=[row for row in self.fixture['cpu_payload']['burst_timeline']
                  if not row['event'].startswith(('카메라 초점:','게이지 만충'))]
        self.assertEqual(actual['burst_timeline'],expected)
        self.assertEqual(actual['burst_gauge_mode'],'fixed')

    def test_saved_artifact_descriptor_is_explicit_and_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            path=self.descriptor(folder)
            with patch.dict(os.environ,{artifacts.ENV:str(path)}):
                self.assertEqual(artifacts.select(product.SOURCE)['battle_package'],folder)
                with self.assertRaisesRegex(ValueError,'未準備'):artifacts.select('gpu/product_group_battle_entry.slang')
            for document in [dict(schema=True,programs={}),dict(schema=1,programs={'gpu/unknown.slang':{}}),dict(schema=1,programs=[],extra=1)]:
                path.write_text(json.dumps(document))
                with patch.dict(os.environ,{artifacts.ENV:str(path)}),self.assertRaises(ValueError):artifacts.select(product.SOURCE)
            path=self.descriptor(folder);document=json.loads(path.read_text());document['programs'][product.SOURCE]['request']['package']='relative';path.write_text(json.dumps(document))
            with patch.dict(os.environ,{artifacts.ENV:str(path)}),self.assertRaisesRegex(ValueError,'absolute'):artifacts.select(product.SOURCE)
            for value in ('','relative.json',str(Path(folder)/'missing.json')):
                with patch.dict(os.environ,{artifacts.ENV:value}),self.assertRaises(ValueError):artifacts.descriptor_file()

    def test_saved_program_requires_the_current_sealed_source_before_loading_image(self):
        cli=artifacts.proof_cli()
        from portable_backend import source_hashes
        owner=dict(package_id='mock-owner',suite='product-detail',purpose='sealed',golden=dict(source_sha256=source_hashes(product.SOURCE)))
        with tempfile.TemporaryDirectory() as folder:
            path=self.descriptor(folder);capture=Path(folder)/'capture';capture.mkdir()
            for changed in [dict(purpose='development'),dict(selected_cases=['one']),dict(golden=dict(source_sha256={})),dict(suite='damage-factors')]:
                with patch.dict(os.environ,{artifacts.ENV:str(path)}),patch.object(artifacts,'proof_cli',return_value=cli),\
                     patch.object(cli,'verify_package',return_value={**owner,**changed}),patch.object(cli,'saved_linked_provider') as provider:
                    with self.assertRaisesRegex(ValueError,'current battle source'):
                        with artifacts.saved_program(product.SOURCE,capture):pass
                    provider.assert_not_called()
            receipt=dict(identity=dict(provider='mock; not hardware evidence'),key='mock')
            @contextmanager
            def provider(manifest,where,backend,journal):
                self.assertEqual(manifest,owner);self.assertEqual(backend,'cuda')
                self.assertEqual(json.loads((where/'linked-artifact-request.json').read_text()),dict(package=folder,capture=folder))
                journal.emit('cuda_linked_origin','verified',receipt=receipt)
                journal.emit('cuda_linked_artifact','entered')
                journal.emit('cuda_linked_artifact','returned')
                journal.emit('cuda_linked_artifact_receipt','verified',receipt=receipt)
                yield receipt
            with patch.dict(os.environ,{artifacts.ENV:str(path)}),patch.object(artifacts,'proof_cli',return_value=cli),\
                 patch.object(cli,'verify_package',return_value=owner),patch.object(cli,'saved_linked_provider',side_effect=provider):
                with artifacts.saved_program(product.SOURCE,capture) as actual:self.assertEqual(actual,receipt)

    def test_saved_program_preserves_execution_errors_and_restores_import_state(self):
        @contextmanager
        def admitted(*args):
            # Only the provider boundary is mocked; no hardware claim.
            yield dict(identity=dict(provider='mock'),key='mock')
        with tempfile.TemporaryDirectory() as folder:
            path=self.descriptor(folder)
            previous=list(sys.path);bytecode=sys.dont_write_bytecode
            for error in (KeyError('execution field'),TypeError('execution argument'),ImportError('execution dependency')):
                with patch.dict(os.environ,{artifacts.ENV:str(path)}),patch.object(artifacts,'_audited_program',side_effect=admitted):
                    with self.assertRaises(type(error)) as raised:
                        with artifacts.saved_program(product.SOURCE,Path(folder)):
                            self.assertEqual(sys.path,previous)
                            raise error
                self.assertIs(raised.exception,error)
                self.assertEqual(sys.path,previous)
                self.assertEqual(sys.dont_write_bytecode,bytecode)

    def test_product_saved_receipt_is_bound_to_transport_and_cpu_still_runs_after_gpu(self):
        body={**self.fixture['body'],'compute_backend':'cuda_shared_detail'}
        expected=copy.deepcopy(self.fixture['cpu_payload']);expected['evaluator']=product.engine_worker.sim.evaluator()
        receipt=dict(identity=dict(provider='mock; not hardware evidence'),key='mock-key')
        for matching,retained_history in ((True,False),(False,False),(True,True),(False,True)):
            receipt['identity'].pop('historical_link_environment',None)
            if retained_history:receipt['identity']['historical_link_environment']=dict(capture=str(ROOT),observation_sha256='a'*64,missing_identities=[dict(pid=71,path='c:/tools/node.exe',creation_filetime_ticks='133700000000000007')],disposition='retained-failure',preservation_verified=False,service_preservation_verified=False,service_status_before='unverified',service_status_after='unverified',termination_cause='unknown')
            events=[]
            @contextmanager
            def provider(source,folder):
                self.assertEqual(source,product.SOURCE);events.append('admission');yield receipt
            def execute(source,entry,packed,iw,ow,backend,*,readback_path):
                events.append('gpu');raw=bytes(ow*4);readback_path.write_bytes(raw)
                return None,dict(backend='cuda',gpu_execution_verified=True,input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),transport=dict(device='mock',cases=1,command_status='completed',host_dispatch_seconds=.1,compile_artifact=receipt if matching else {}))
            def cpu(request):events.append('cpu');return copy.deepcopy(expected)
            with tempfile.TemporaryDirectory() as folder:
                path=self.descriptor(folder)
                with patch.dict(os.environ,{artifacts.ENV:str(path),'NIKKE_DETAIL_CAPTURE_ROOT':folder,'NIKKE_SLANG_GENERATION_CACHE':folder,'NIKKE_CUDA_COMPILE_CACHE':''}),\
                     patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                     patch.object(product,'saved_program',side_effect=provider),patch.object(product,'execute',side_effect=execute),\
                     patch.object(product,'decode',return_value=self.fixture['gpu_projection']),patch.object(product.engine_worker,'evaluate',side_effect=cpu):
                    result=product.evaluate(body)
                self.assertEqual(events,['admission','gpu','cpu'])
                self.assertEqual(result['compute']['backend'],'cuda_shared_detail' if matching else 'cpu')
                self.assertEqual(result['compute']['saved_cubin_admission'],'verified' if matching else 'not_admitted')
                capture=next(Path(folder).glob('*/result.json')).parent
                self.assertTrue((capture/'evidence.json').is_file())
                if matching:
                    self.assertEqual(result['compute']['artifact_key'],receipt['key'])
                    self.assertEqual(json.loads((capture/'result.json').read_text())['artifact_receipt'],receipt)
                else:self.assertIn('receipt mismatch',result['compute']['unsupported'][0]['reason'])
                if retained_history:
                    self.assertIs(result['compute']['historical_link_preservation_verified'],False)
                    self.assertEqual(result['compute']['historical_link_missing_processes_count'],1)
                    self.assertIs(json.loads((capture/'result.json').read_text())['historical_link_preservation_verified'],False)

    def test_real_product_admission_rejects_missing_processes_tampered_owner_and_missing_entry(self):
        cli=artifacts.proof_cli()
        from portable_backend import source_hashes
        owner=dict(package_id='mock-owner',suite='product-detail',purpose='sealed',golden=dict(source_sha256=source_hashes(product.SOURCE)))
        body={**self.fixture['body'],'compute_backend':'cuda_shared_detail'}
        for failure in ('missing_existing_processes','tampered owner','missing entry','malformed metadata','missing dependency'):
            with tempfile.TemporaryDirectory() as folder:
                path=self.descriptor(folder)
                if failure=='missing entry':
                    d=json.loads(path.read_text());d['programs']={};path.write_text(json.dumps(d))
                previous=list(sys.path);bytecode=sys.dont_write_bytecode
                with patch.dict(os.environ,{artifacts.ENV:str(path),'NIKKE_DETAIL_CAPTURE_ROOT':folder,'NIKKE_SLANG_GENERATION_CACHE':folder}),\
                     patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                     patch.object(artifacts,'proof_cli',return_value=cli),patch.object(cli,'verify_package',side_effect=ValueError(failure) if failure=='tampered owner' else None,return_value=owner),\
                     patch.object(cli,'saved_linked_admission',side_effect=KeyError('comparison') if failure=='malformed metadata' else ImportError('observer') if failure=='missing dependency' else ValueError('missing_existing_processes')) as admission,\
                     patch.object(product,'execute',side_effect=AssertionError('No GPU or compiler')) as dispatch,\
                     patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
                    result=product.evaluate(body)
                self.assertEqual(result['compute']['backend'],'cpu');dispatch.assert_not_called()
                capture=next(Path(folder).glob('*/result.json')).parent
                self.assertNotIn('artifact_receipt',json.loads((capture/'result.json').read_text()))
                if failure in ('tampered owner','missing entry'):admission.assert_not_called()
                if failure=='tampered owner':self.assertFalse((capture/'linked-artifact-request.json').exists())
                self.assertEqual(sys.path,previous);self.assertEqual(sys.dont_write_bytecode,bytecode)

    def test_product_uses_actual_saved_loader_and_forbids_nvrtc_with_mocked_driver_output(self):
        import test_portable_linked_artifact as existing
        import portable_backend as backend
        fixture=existing.LinkedArtifactTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        cli=artifacts.proof_cli()
        owner=dict(package_id='mock-owner',suite='product-detail',purpose='sealed',golden=dict(source_sha256=backend.source_hashes(product.SOURCE)))
        state=fixture.state();events=[]
        expected=copy.deepcopy(self.fixture['cpu_payload']);expected['evaluator']=product.engine_worker.sim.evaluator()
        def execute(source,entry,packed,iw,ow,actual_backend,*,readback_path):
            self.assertEqual(sys.path,previous);self.assertEqual(sys.dont_write_bytecode,bytecode)
            image,receipt=backend.compile_cuda_source(fixture.source)
            self.assertEqual(image,fixture.image.read_bytes());self.assertEqual(receipt,state['receipt'])
            if attempt_forbidden:
                with self.assertRaisesRegex(RuntimeError,'forbidden'):backend.compile_cuda_artifact(None,b'',[])
            events.append('gpu');raw=bytes(ow*4);readback_path.write_bytes(raw)
            return None,dict(backend='cuda',gpu_execution_verified=True,input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),transport=dict(device='mock; no actual GPU',cases=1,command_status='completed',host_dispatch_seconds=.1,compile_artifact=receipt))
        def cpu(request):events.append('cpu');return copy.deepcopy(expected)
        for attempt_forbidden in (False,True):
            events.clear()
            with tempfile.TemporaryDirectory() as folder:
                path=self.descriptor(folder);previous=list(sys.path);bytecode=sys.dont_write_bytecode
                with patch.dict(os.environ,{artifacts.ENV:str(path),'NIKKE_DETAIL_CAPTURE_ROOT':folder,'NIKKE_SLANG_GENERATION_CACHE':folder}),\
                     patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                     patch.object(artifacts,'proof_cli',return_value=cli),patch.object(cli,'verify_package',return_value=owner),\
                     patch.object(cli,'saved_linked_admission',return_value=state),patch.object(product,'execute',side_effect=execute),\
                     patch.object(product,'decode',return_value=self.fixture['gpu_projection']),patch.object(product.engine_worker,'evaluate',side_effect=cpu):
                    result=product.evaluate({**self.fixture['body'],'compute_backend':'cuda_shared_detail'})
                self.assertEqual(result['compute']['backend'],'cpu' if attempt_forbidden else 'cuda_shared_detail');self.assertEqual(events,['gpu','cpu'])
                if not attempt_forbidden:self.assertEqual(result['compute']['artifact_key'],state['receipt']['key'])
                self.assertEqual(sys.path,previous);self.assertEqual(sys.dont_write_bytecode,bytecode)

    def test_bad_saved_image_phase_order_or_completion_rejects_product_output(self):
        cli=artifacts.proof_cli()
        from portable_backend import source_hashes
        owner=dict(package_id='mock-owner',suite='product-detail',purpose='sealed',golden=dict(source_sha256=source_hashes(product.SOURCE)))
        receipt=dict(identity=dict(provider='mock; not hardware evidence'),key='mock')
        for bad in ('missing-return','duplicate-marker','wrong-order'):
            @contextmanager
            def provider(manifest,where,backend,journal):
                rows=[('cuda_linked_origin','verified',dict(receipt=receipt)),('cuda_linked_artifact','entered',{}),('cuda_linked_artifact','returned',{}),('cuda_linked_artifact_receipt','verified',dict(receipt=receipt))]
                if bad=='missing-return':rows.pop(2)
                elif bad=='duplicate-marker':rows.append(rows[-1])
                else:rows[0],rows[1]=rows[1],rows[0]
                for stage,state,facts in rows:journal.emit(stage,state,**facts)
                yield receipt
            def execute(source,entry,packed,iw,ow,backend,*,readback_path):
                raw=bytes(ow*4);readback_path.write_bytes(raw)
                return None,dict(transport=dict(compile_artifact=receipt))
            with tempfile.TemporaryDirectory() as folder:
                path=self.descriptor(folder)
                with patch.dict(os.environ,{artifacts.ENV:str(path),'NIKKE_DETAIL_CAPTURE_ROOT':folder,'NIKKE_SLANG_GENERATION_CACHE':folder}),\
                     patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                     patch.object(artifacts,'proof_cli',return_value=cli),patch.object(cli,'verify_package',return_value=owner),\
                     patch.object(cli,'saved_linked_provider',side_effect=provider),patch.object(product,'execute',side_effect=execute),\
                     patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
                    result=product.evaluate({**self.fixture['body'],'compute_backend':'cuda_shared_detail'})
                self.assertEqual(result['compute']['backend'],'cpu')
                capture=next(Path(folder).glob('*/result.json')).parent
                self.assertNotIn('artifact_receipt',json.loads((capture/'result.json').read_text()))
                self.assertTrue((capture/'evidence.json').exists())

    def test_descriptor_history_reaches_real_admission_loader_and_product_result(self):
        import test_portable_linked_artifact as existing
        import portable_linked_artifact as saved
        import portable_backend as backend
        from windows_validation_observer import compare_snapshots
        f=existing.LinkedArtifactTests();f.setUp();self.addCleanup(f.doCleanups);cli=artifacts.proof_cli()
        hashes=backend.source_hashes(product.SOURCE)
        for item in (f.golden,f.linked['golden'],f.producer,f.compiler):item['source_sha256']=hashes
        owner=dict(package_id='mock-owner',suite='product-detail',purpose='sealed',golden=copy.deepcopy(f.golden))
        package=f.root/'link-owner';capture=f.root/'link';obj=f.root/'object';producer=f.root/'producer'
        for p in (package,capture,obj,producer):p.mkdir()
        cli.write(package/'gpu-package.json',f.linked);cli.write(package/'jit-link-object-claimed-cuda.json',{});cli.write(capture/'artifacts.json',{})
        cli.write(capture/'object-request.json',dict(object_capture=str(obj)));cli.write(obj/'object-request.json',dict(source_capture=str(producer)));cli.write(producer/'compiler.json',f.compiler)
        cli.write(capture/'jit-link.json',dict(origin=dict(object_receipt=dict(identity=dict(origin=dict(producer=f.producer)))),receipt=f.link));(capture/'jit-linked.cubin').write_bytes(f.image.read_bytes())
        row=dict(pid=71,path='C:/Tools/CUA/node.exe',creation_filetime_ticks='133700000000000007',role='unrelated')
        before=dict(processes=[row],service_status='unverified');after=dict(processes=[],service_status='unverified')
        cli.write(capture/'observation.json',dict(before=before,after=after,comparison=compare_snapshots(before,after)))
        binding=dict(capture=str(capture),observation_sha256=saved.digest((capture/'observation.json').read_bytes()),missing_identities=saved.missing_identities([row]),disposition='retained-failure')
        path=self.descriptor(str(f.root));document=json.loads(path.read_text());request=dict(package=str(package),capture=str(capture),historical_link_observation=binding);document['programs'][product.SOURCE]['request']=request;path.write_text(json.dumps(document))
        expected=copy.deepcopy(self.fixture['cpu_payload']);expected['evaluator']=product.engine_worker.sim.evaluator()
        def verify(where,**kwargs):return f.linked if where==package else owner
        def execute(source,entry,packed,iw,ow,actual_backend,*,readback_path):
            image,receipt=backend.compile_cuda_source(f.source);self.assertEqual(image,f.image.read_bytes())
            self.assertFalse(receipt['identity']['historical_link_environment']['preservation_verified'])
            raw=bytes(ow*4);readback_path.write_bytes(raw)
            return None,dict(backend='cuda',gpu_execution_verified=True,input_sha256=saved.digest(packed),output_sha256=saved.digest(raw),transport=dict(device='mock; not GPU evidence',cases=1,command_status='completed',host_dispatch_seconds=.1,compile_artifact=receipt))
        with patch.dict(os.environ,{artifacts.ENV:str(path),'NIKKE_DETAIL_CAPTURE_ROOT':str(f.root/'requests'),'NIKKE_SLANG_GENERATION_CACHE':str(f.root)}),\
             patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
             patch.object(artifacts,'proof_cli',return_value=cli),patch.object(cli,'verify_package',side_effect=verify),\
             patch.object(cli,'audit_jit_link_capture',return_value=dict(link_verified=True,containment_verified=True)),\
             patch.object(product,'execute',side_effect=execute),patch.object(product,'decode',return_value=self.fixture['gpu_projection']),patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(expected)):
            self.assertEqual(artifacts.select(product.SOURCE)['request'],request)
            result=product.evaluate({**self.fixture['body'],'compute_backend':'cuda_shared_detail'})
            self.assertEqual(result['compute']['backend'],'cuda_shared_detail');self.assertIs(result['compute']['historical_link_preservation_verified'],False)
            where=f.root/'requests'/result['compute']['capture_id'];self.assertEqual(json.loads((where/'linked-artifact-request.json').read_text()),request)
            self.assertFalse(json.loads((where/'result.json').read_text())['artifact_receipt']['identity']['historical_link_environment']['preservation_verified'])
            changed=copy.deepcopy(document);changed['programs'][product.SOURCE]['request']['historical_link_observation']['capture']=str(f.root);path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'capture mismatch'):artifacts.select(product.SOURCE)
            changed=copy.deepcopy(document);changed['programs'][product.SOURCE]['request']['historical_link_observation']['missing_identities']=[];path.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):artifacts.select(product.SOURCE)

    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/'tests/fixtures/portable-detail-product-v1.json').read_text(encoding='utf-8'))
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('Preparation must not run a battle')):
            cls.prepared,cls.prepared_run=product.prepare(cls.fixture['body'])
            cls.words,cls.metadata=compile_projectile_battle(cls.prepared)
    def test_saved_actual_gpu_projection_reconstructs_complete_original_product_payload(self):
        with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
            payload=product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[])
        expected=copy.deepcopy(self.fixture['cpu_payload'])
        # Run provenance is stamped at response time; the saved capture keeps
        # its historical commit. No calculation/payload fields are excluded.
        expected['evaluator']=product.engine_worker.sim.evaluator()
        self.assertEqual(payload,expected)
        self.assertEqual(self.prepared['cpu_battle_executed'],False)
        self.assertEqual(len(self.prepared['effects']),len(self.metadata['effects']))
    def test_invalid_status_truncation_nonfinite_and_bad_owner_cannot_be_published(self):
        for mutate in (lambda v:v.update(status=64),lambda v:v.update(burst_trace_total=999),
            lambda v:v['queries'][0]['damage'].__setitem__(0,float('nan')),
            lambda v:v['burst_trace'][0].update(owner=9)):
            view=copy.deepcopy(self.fixture['gpu_projection']);mutate(view)
            with patch.object(product,'decode',return_value=view):
                with self.assertRaises((ValueError,RuntimeError)):
                    product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[])
    def test_original_model_warnings_are_collected_without_a_cpu_battle(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from staged_dot_runtime import MODEL_WARNING
        from periodic_source_runtime import LEGACY_WARNING
        from target_counter_runtime import SINGLE_BODY_WARNING
        for name,warning in [('사쿠라 : 블룸 인 서머',MODEL_WARNING),
                             ('아인',LEGACY_WARNING),('일레그 : 붐 앤 쇼크',SINGLE_BODY_WARNING)]:
            body=selected_profile_bodies([name],0)[0][2]
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                prepared,run=product.prepare(body)
            self.assertEqual(run._portable_detail_model_warnings,[warning])
            with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
                payload=product.decode_payload(body,prepared,run,self.metadata,[])
            self.assertEqual(payload['app_warnings'],[self.fixture['cpu_payload']['app_warnings'][0],warning])
    def test_backend_failure_preserves_cpu_label_and_strips_internal_request_flags(self):
        body={**self.fixture['body'],'_compile_gpu_detail':True}
        calls=[]
        def cpu(request):
            calls.append(request);return copy.deepcopy(self.fixture['cpu_payload'])
        for error in (RuntimeError('device unavailable'),KeyError('execution field'),TypeError('execution argument'),ImportError('execution dependency')):
            with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),\
                 patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                 patch.object(product,'execute',side_effect=error),\
                 patch.object(product.engine_worker,'evaluate',side_effect=cpu):
                result=product.evaluate(body)
                self.assertEqual(result['compute']['backend'],'cpu')
                self.assertEqual(result['compute']['requested'],'metal_detail')
                self.assertFalse(result['compute']['gpu_execution_verified'])
                self.assertNotIn('_compile_gpu_detail',calls[0])
                self.assertEqual(len(list(Path(folder).glob('*/result.json'))),1)
                record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                self.assertEqual(record['error_type'],type(error).__name__)
                self.assertEqual(record['error'],str(error))
                self.assertNotIn('audit metadata incomplete',record['error'])
    def test_invalid_product_parts_fall_back_before_any_gpu_dispatch(self):
        body=copy.deepcopy(self.fixture['body']);body['enemy']['parts']=[dict(id='example')]
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),\
             patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
             patch.object(product,'execute',side_effect=AssertionError('No dispatch')),\
             patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
            result=product.evaluate(body)
            self.assertEqual(result['compute']['backend'],'cpu')
            self.assertIn('パーツ',result['compute']['unsupported'][0]['reason'])
    def test_both_backends_use_identical_inputs_decoder_and_post_readback_cpu_check(self):
        wires=[]
        for requested,backend in product.BACKENDS.items():
            body={**self.fixture['body'],'compute_backend':requested}
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in input')):
                prepared,run=product.prepare(body)
            expected=copy.deepcopy(self.fixture['cpu_payload']);expected['evaluator']=product.engine_worker.sim.evaluator()
            events=[]
            def execute(source,entry,packed,iw,ow,actual_backend,*,readback_path):
                self.assertEqual(actual_backend,backend);wires.append(packed);events.append('gpu')
                if backend=='cuda':
                    self.assertEqual({k:os.environ[k] for k in ('NIKKE_CUDA_ARTIFACT','NIKKE_CUDA_CACHE_REQUIRED','NIKKE_CUDA_PTXAS_OPT_LEVEL','NIKKE_SLANG_GENERATION_REQUIRED')},
                        dict(NIKKE_CUDA_ARTIFACT='cubin',NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_CUDA_PTXAS_OPT_LEVEL='1',NIKKE_SLANG_GENERATION_REQUIRED='1'))
                raw=bytes(ow*4);readback_path.write_bytes(raw)
                return None,dict(backend=backend,gpu_execution_verified=True,input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),
                    transport=dict(device='mock transport; not GPU evidence',cases=1,command_status='completed',**{'gpu_seconds' if backend=='metal' else 'host_dispatch_seconds':.1}))
            def cpu(request):
                self.assertEqual(events,['gpu']);events.append('cpu');return copy.deepcopy(expected)
            with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,dict(NIKKE_DETAIL_CAPTURE_ROOT=folder,NIKKE_SLANG_GENERATION_CACHE=folder,NIKKE_CUDA_COMPILE_CACHE=folder,
                NIKKE_CUDA_ARTIFACT='ptx',NIKKE_CUDA_CACHE_REQUIRED='0',NIKKE_CUDA_PTXAS_OPT_LEVEL='3',NIKKE_SLANG_GENERATION_REQUIRED='0')),\
                patch.object(product.platform,'system',return_value='Windows'),patch.object(product,'prepare',return_value=(prepared,run)),\
                patch.object(product,'decode',return_value=self.fixture['gpu_projection']),patch.object(product,'execute',side_effect=execute),patch.object(product.engine_worker,'evaluate',side_effect=cpu):
                result=product.evaluate(body);self.assertEqual(events,['gpu','cpu'])
                self.assertEqual(result['compute']['backend'],requested);self.assertTrue(result['compute']['cpu_verification']['matched'])
                self.assertIn('gpu_seconds' if backend=='metal' else 'host_dispatch_seconds',result['compute'])
                self.assertNotIn('host_dispatch_seconds' if backend=='metal' else 'gpu_seconds',result['compute'])
                self.assertEqual(os.environ['NIKKE_CUDA_ARTIFACT'],'ptx')
                record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                self.assertEqual(len(record['request_sha256']),64)
                self.assertEqual(record['capture_id'],result['compute']['capture_id'])
        self.assertEqual(wires[0],wires[1])
    def test_cuda_environment_and_required_cache_failures_remain_cpu_results(self):
        body={**self.fixture['body'],'compute_backend':'cuda_shared_detail'}
        for platform_name,configured,error in [('Darwin',True,'Windows'),('Windows',False,'キャッシュ'),('Windows',True,'required cache miss')]:
            with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,dict(NIKKE_DETAIL_CAPTURE_ROOT=folder,
                NIKKE_SLANG_GENERATION_CACHE=folder if configured else '',NIKKE_CUDA_COMPILE_CACHE=folder if configured else '')),\
                patch.object(product.platform,'system',return_value=platform_name),patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                patch.object(product,'execute',side_effect=RuntimeError('required cache miss; compiler forbidden')) as dispatch,\
                patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
                result=product.evaluate(body);self.assertEqual(result['compute']['requested'],'cuda_shared_detail')
                self.assertEqual(result['compute']['backend'],'cpu');self.assertFalse(result['compute']['gpu_execution_verified'])
                self.assertIn(error,result['compute']['unsupported'][0]['reason'])
                self.assertEqual(dispatch.call_count,int(platform_name=='Windows' and configured))
    def test_actual_backend_cache_misses_do_not_reach_generators_compilers_or_driver(self):
        import portable_backend as backend
        body={**self.fixture['body'],'compute_backend':'cuda_shared_detail'}
        for stage in ('generation','cubin'):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);sdk=root/'sdk';(sdk/'bin').mkdir(parents=True)
                for name in ('slangc','slangc.exe','nvrtc64_test.dll','nvrtc-builtins64_test.dll'):
                    (sdk/'bin'/name).write_bytes(b'identity only; must never execute')
                generation=root/'generation';generation.mkdir();cache=root/'compile';cache.mkdir()
                cuda=root/'never-compile.cu';cuda.write_bytes(b'// cache miss, no compiler allowed\n')
                env=dict(NIKKE_DETAIL_CAPTURE_ROOT=str(root/'captures'),NIKKE_SLANG_ROOT=str(sdk),CUDA_PATH=str(sdk),
                    NIKKE_SLANG_GENERATION_CACHE=str(generation),NIKKE_CUDA_COMPILE_CACHE=str(cache),
                    NIKKE_CUDA_CACHE_REQUIRED='0',NIKKE_SLANG_GENERATION_REQUIRED='0')
                windows=SimpleNamespace(name='nt',environ=os.environ,add_dll_directory=lambda _:nullcontext())
                build=patch.object(backend,'build',return_value=({'cuda':cuda},backend.source_hashes(product.SOURCE))) if stage=='cubin' else nullcontext()
                clean={k:v for k,v in os.environ.items() if not k.startswith('SLANG_') and k not in ('LD_LIBRARY_PATH','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH')}
                clean.update(env)
                with patch.dict(os.environ,clean,clear=True),patch.object(product.platform,'system',return_value='Windows'),\
                    patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
                    patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])),\
                    patch.object(backend,'_build_resident',side_effect=AssertionError('No Slang')) as generator,\
                    patch.object(backend,'_cuda_module',side_effect=AssertionError('No CUDA driver')) as driver,\
                    patch.object(backend.C,'WinDLL',create=True,side_effect=AssertionError('No NVRTC DLL')) as compiler,\
                    patch.object(backend,'resident_plan',return_value=None),patch.object(backend,'os',windows),build:
                    result=product.evaluate(body)
                    self.assertEqual(result['compute']['backend'],'cpu');self.assertFalse(result['compute']['gpu_execution_verified'])
                    self.assertIn('cache miss',result['compute']['unsupported'][0]['reason'].lower())
                    generator.assert_not_called();driver.assert_not_called();compiler.assert_not_called()
    def test_incomplete_or_wrong_execution_metadata_fails_closed(self):
        valid=dict(backend='cuda',gpu_execution_verified=True,input_sha256='0'*64,output_sha256='1'*64,
            transport=dict(device='mock',cases=1,command_status='completed',host_dispatch_seconds=.1))
        self.assertEqual(product.verified_transport(valid,'cuda')[1],'host_dispatch_seconds')
        variants=[None,{},dict(valid,backend='metal'),dict(valid,input_sha256='bad')]
        for key,value in [('device',None),('cases',True),('host_dispatch_seconds',float('nan'))]:
            item=copy.deepcopy(valid);item['transport'][key]=value;variants.append(item)
        for item in variants:
            with self.assertRaises(RuntimeError):product.verified_transport(item,'cuda')
    def test_real_multi_hit_uses_existing_native_group_wire_without_changing_effects(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        body=selected_profile_bodies(['벨로타'],0)[0][2]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            source,iw,ow,words,metadata=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(source,'gpu/product_group_battle_entry.slang')
        self.assertEqual((iw,ow,len(words)),(104408,1048576,104408))
        self.assertEqual(len(metadata['effects']),len(prepared['effects']))
        self.assertEqual(words[-8:-5],[0x41475331,2,1])
        event_rows=[i for i in range(words[1]) if words[L['EVENT_BASE']+i*L['EVENT_WORDS']]==62]
        self.assertTrue(event_rows)
        bad=copy.deepcopy(prepared)
        next(item['effect'] for item in bad['effects'] if any(t.startswith('multi_hit:') for t in item['effect']['trigger']['timing']))['trigger']['timing']=['multi_hit:0']
        with self.assertRaises(ValueError):product.compile_product(bad)
    def test_ordinary_periodic_stack_scaling_preserves_hit_count_not_dot_coefficient(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_periodic_specs import periodic_flags
        body=selected_profile_bodies(['마스트'],0)[0][2]
        prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
        _,_,_,words,metadata=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        row=metadata['effects'].index('폭풍')
        self.assertEqual(words[L['REFERENCE_DEFINITION_BASE']+row*4]&3,1)
        self.assertEqual(words[L['PERIODIC_DEFINITION_BASE']+row*2]&2,0)
        self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['PRESERVE']],0)
        dot=dict(type='damage',stat='dot_damage',tick_interval=1,scaling='stack_count',target='target')
        self.assertEqual(periodic_flags(dot,0)&2,2)
    def test_plain_body_keeps_all_original_target_modifier_carriers_and_axes(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        from destructible_damage_policy import modifier_axis
        for name in ['사쿠라','앵커','클레이','아스카','레이','마리','미사토']:
            body=selected_profile_bodies([name],0)[0][2]
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                source,iw,ow,words,metadata=product.compile_product(prepared)
            self.assertEqual(prepared,before)
            self.assertEqual((source,iw,ow,len(words)),('gpu/product_target_battle_entry.slang',110112,1048576,110112))
            self.assertEqual(words[104400+2320],0)
            self.assertEqual(words[104400+5680:104400+5686],[0x48534933,0,0,1,1,1])
            self.assertEqual(metadata['real_prepared_input']['target_modifier_carriers']['original_effects'],prepared['effects'])
            seen=[]
            for row,index in enumerate(metadata['binding_source_indices']):
                axis=modifier_axis(prepared['effects'][index]['effect'])
                if axis:
                    seen.append(axis);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                    self.assertEqual(words[at+F['KIND']],4)
                    self.assertEqual(words[104400+5168+row],axis)
                    self.assertNotEqual(words[at+F['VALUE']:at+F['VALUE']+2],[0,0])
            self.assertTrue(seen)
    def test_plain_body_modifier_input_cannot_discard_a_declared_world(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        body=selected_profile_bodies(['아스카'],0)[0][2]
        prepared,_=product.prepare(body)
        for key,value in [('patterns',[dict(id='wave',kind='summon',spec=dict(count=1,hp=100))]),
                          ('has_parts',True),('part_break_interval',1),('coord',{})]:
            case=copy.deepcopy(prepared);case['enemy'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'plain body'):product.compile_product(case)
        unknown=copy.deepcopy(prepared);unknown['enemy']['new_typed_targets']=[]
        with self.assertRaisesRegex(ValueError,'Unknown real enemy fields'):product.compile_product(unknown)
        grouped=copy.deepcopy(prepared);grouped['effects'][0]['effect']['trigger']['timing'].append('multi_hit:2')
        from portable_destructible_roster_input import compile_body_modifier_roster
        with self.assertRaisesRegex(ValueError,'group wire composition'):compile_body_modifier_roster(grouped)

    def test_original_modifier_and_multi_hit_composition_preserves_both_wires(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from detail_coverage import body_for
        from portable_destructible_roster_input import GROUP_SOURCE,GROUP_INPUT_WORDS
        from destructible_damage_policy import modifier_axis
        from portable_specs import LIMITS as L,FIELDS as F
        body=dict(body_for(['사쿠라','벨로타','미란다','도라','드레이크'],30),burst_gauge_mode='accumulate')
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
            prepared,_=product.prepare(body)
            before=copy.deepcopy(prepared)
            source,iw,ow,words,meta=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual((source,iw,ow),(GROUP_SOURCE,GROUP_INPUT_WORDS,1048576))
        from portable_backend import validate_composed_stride
        validate_composed_stride(source,iw,ow)
        with self.assertRaisesRegex(ValueError,'complete carrier'):validate_composed_stride(source,iw-1,ow)
        self.assertEqual(words[104400],0x41475331)
        axes=meta['real_prepared_input']['target_modifier_carriers']
        self.assertEqual(axes['original_effects'],prepared['effects'])
        self.assertEqual(axes['typed_targets'],0)
        self.assertEqual(words[104408:104416],[0x50474131,1,sum(bool(x) for x in axes['axis_rows']),0,0,0,0,0])
        self.assertEqual(words[104416:],axes['axis_rows'])
        for row,index in enumerate(meta['binding_source_indices']):
            axis=modifier_axis(prepared['effects'][index]['effect'])
            self.assertEqual(axes['axis_rows'][row],axis)
            if axis:self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']],4)
        bad=copy.deepcopy(prepared);bad['enemy']['patterns']=[{'id':'new','kind':'summon','spec':{'count':1,'hp':100}}]
        with self.assertRaisesRegex(ValueError,'plain body'):product.compile_product(bad)
        bad=copy.deepcopy(prepared)
        next(r['effect'] for r in bad['effects'] if modifier_axis(r['effect']))['trigger']['timing']=['multi_hit:2']
        with self.assertRaisesRegex(ValueError,'itself a multi_hit'):product.compile_product(bad)
    def test_modifier_world_composition_preserves_original_script_and_axis_wires(self):
        from detail_coverage import body_for
        from portable_specs import LIMITS as L
        from portable_world_schedule_specs import compile_schedule
        from portable_destructible_roster_input import product_body_world
        patterns=[{'id': 'armor', 'kind': 'buff', 'enemy': {'def_mult': 1.5}, 'until': {'time': 1.5}}, {'id': 'core', 'kind': 'core', 'delay': 0.3, 'core_px': 80, 'until': {'time': 1}}, {'id': 'volley', 'kind': 'attack', 'delay': 0.4, 'spec': {'coeff': 100, 'atk': 1000000, 'target': 'all', 'hits': 3, 'interval': 0.2, 'pierce': True}}]
        for names,source in [(['아스카','리타','모더니아','레드 후드','나가'],'gpu/product_fixed_target_battle_entry.slang'),
                            (['사쿠라','벨로타','미란다','도라','드레이크'],'gpu/product_fixed_group_target_battle_entry.slang')]:
            body=body_for(names,5);body.update(burst_gauge_mode='fixed');body['enemy']['patterns']=patterns;body['enemy']['parts']=[dict(name='modifier-part',hp=100,reach=1)]
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU schedule')):
                prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
                actual,iw,ow,words,meta=product.compile_product(prepared)
            self.assertEqual(actual,source);self.assertEqual(len(words),iw);self.assertEqual(prepared,before)
            graph,_=compile_schedule(dict(patterns=prepared['enemy']['patterns'],clock='accumulated',duration=5),notice_payload=True)
            base=L['WORLD_FRAME_INPUT_BASE'];self.assertEqual(words[base:base+len(graph)],graph)
            self.assertEqual(meta['real_prepared_input']['target_modifier_carriers']['original_effects'],prepared['effects'])
            self.assertEqual([p['id'] for p in meta['product_world']['nodes']],[p['id'] for p in prepared['enemy']['patterns']])
            self.assertFalse(meta['product_world']['cpu_schedule_or_state_supplied'])
            self.assertEqual(meta['product_parts'],[dict(name='modifier-part',slot=1,node=0)])
            for pattern in [dict(id='shield',kind='shield'),dict(id='wave',kind='summon',spec=dict(count=1,hp=100))]:
                bad=copy.deepcopy(prepared);bad['enemy']['patterns']=[pattern]
                with self.assertRaises(ValueError):product_body_world(bad)

    def test_nearby_selector_is_specialized_only_for_a_proved_single_body(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        body=selected_profile_bodies(['일레그'],0)[0][2]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            source,_,_,words,metadata=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        # The original Elegg also carries a target-specific modifier.
        self.assertEqual(source,'gpu/product_target_battle_entry.slang')
        self.assertEqual(metadata['real_prepared_input']['single_body_nearby']['rows'],[1])
        self.assertEqual(metadata['real_prepared_input']['single_body_nearby']['original_effects'],[prepared['effects'][1]])
        for enemy_change in [dict(patterns=[dict(id='wave',kind='summon',spec=dict(count=1,hp=100))]),
                             dict(coord={}),dict(has_parts=True),dict(part_break_interval=1)]:
            case=copy.deepcopy(prepared);case['enemy'].update(enemy_change)
            with self.subTest(change=enemy_change),self.assertRaisesRegex(ValueError,'one plain boss'):product.compile_product(case)
        for target in ['target_and_nearby:0','target_and_nearby:1.5','target_and_nearby:128']:
            case=copy.deepcopy(prepared);case['effects'][1]['effect']['target']=target
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,'recipient count'):product.compile_product(case)

class BossDotNativeContract(unittest.TestCase):
    """Observed CPU product rules for the pending shared boss-DoT consumer.

    These are native comparisons, not GPU coverage. The explicitly authorized
    clock correction preserves schedules while their carriers remain live.
    """
    def test_clock_install_is_idempotent_and_preserves_simulation_aliases(self):
        from boss_dot_clock_compat import install
        from calculator import timeline
        from runner import sim
        original=timeline.simulate
        install();install()
        self.assertIs(timeline.simulate,original)
        self.assertIs(sim.simulate,original)

    def test_clock_rewrite_rejects_changed_retirement_body(self):
        import ast
        from boss_dot_clock_compat import BossDotClock
        source='''def _boss_dots(t):
    if next_t > expires + 1e-9:
        del unrelated[uid]
    else:
        _dot_sched[uid][1] = next_t
'''
        with self.assertRaisesRegex(AssertionError,'retirement changed'):
            BossDotClock().visit(ast.parse(source))

    def native_case(self, *, character='미란다', sim_duration=3, until=None,
                    attack=None, **dot):
        from portable_original_identity_inventory import selected_profile_bodies
        from calculator.buff_manager import BuffManager
        body=selected_profile_bodies([character],0)[0][2]
        body.update(duration=sim_duration,burst_gauge_mode='fixed')
        pattern=dict(id='boss-dot',kind='attack',delay=.5,
            spec=dict(atk=150000,coeff=10,target='slot:1',
                debuffs=[dict(stat='dot',name='native-dot',**{'coeff':10,**dot})],**(attack or {})))
        if until is not None:pattern['until']=dict(time=until)
        body['enemy']['patterns']=[pattern]
        _,run=product.prepare(body)
        notices=[];native_notify=BuffManager.notify
        def observe(manager,event,t,*args,**kwargs):
            if event=='received_hit':notices.append(round(t,6))
            return native_notify(manager,event,t,*args,**kwargs)
        with patch.object(BuffManager,'notify',observe):
            result=product.engine_worker.sim.execute(run)
        return result,notices

    def test_native_finite_dot_includes_expiry_tick_without_received_hit(self):
        result,notices=self.native_case(interval=.5,duration=1)
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5,1.,1.5])
        self.assertEqual([h.damage for h in result.squad_hits],[13212.3]*3)
        self.assertEqual(notices,[.5])
        for hit in result.squad_hits:
            self.assertEqual((hit.hp,hit.shield,hit.cover,hit.decoy),(hit.damage,0,0,0))

    def test_native_refresh_ticks_before_reapplication_and_stacks_in_order(self):
        result,notices=self.native_case(interval=.5,duration=1,max_stack=3,
            attack=dict(hits=3,interval=.5))
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5,1.,1.,1.5,1.5,2.,2.5])
        unit=13212.3
        self.assertEqual([h.damage for h in result.squad_hits],
            [unit,unit,unit,unit*2,unit,unit*3,unit*3])
        self.assertEqual(notices,[.5,1.,1.5])

    def test_native_pattern_close_precedes_dot_on_the_same_frame(self):
        result,notices=self.native_case(interval=.5,until=.5)
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5])
        self.assertEqual([(round(e.t,6),e.event,e.outcome) for e in result.boss_log],
            [(.5,'start',''),(1.,'end','expired')])
        self.assertEqual(notices,[.5])

    def test_native_subframe_dot_drains_every_due_tick_at_current_frame(self):
        result,notices=self.native_case(interval=.01,duration=.05)
        self.assertEqual([round(h.t,6) for h in result.squad_hits],
            [.5,.516667,.533333,.533333,.55,.55])
        self.assertEqual([h.damage for h in result.squad_hits],[13212.3]*6)
        self.assertEqual(notices,[.5])

    def test_native_dot_hp_snapshot_includes_threshold_max_hp_grant(self):
        result,notices=self.native_case(character='목단',interval=.5,duration=2,coeff=1000)
        previous,current=result.squad_hits[2:4]
        self.assertEqual(round(current.t,6),2.)
        self.assertGreater(current.hp,0)
        self.assertGreater(current.hp_after,previous.hp_after)
        self.assertEqual(notices,[.5])

    def test_native_clock_keeps_exhausted_schedule_while_carrier_is_live(self):
        result,notices=self.native_case(character='노아',sim_duration=6,interval=3,duration=5)
        self.assertEqual([round(h.t,6) for h in result.squad_hits[1:]],[3.5])
        self.assertTrue(all(h.damage>0 and h.hp==0 for h in result.squad_hits[1:]))
        self.assertEqual(notices,[.5])

    def test_native_clock_longer_than_duration_never_fires(self):
        result,notices=self.native_case(sim_duration=6,interval=6,duration=5)
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5])
        self.assertEqual(notices,[.5])

    def test_native_clock_exact_expiry_fires_once(self):
        result,notices=self.native_case(sim_duration=6,interval=5,duration=5)
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5,5.5])
        self.assertEqual(notices,[.5])

    def test_native_clock_refresh_resets_exhausted_schedule(self):
        result,notices=self.native_case(sim_duration=8,interval=3,duration=5,
            attack=dict(hits=2,interval=4))
        self.assertEqual([round(h.t,6) for h in result.squad_hits],[.5,3.5,4.5,7.5])
        self.assertEqual(notices,[.5,4.5])

if __name__=='__main__':unittest.main()
