"""Product payload parity and fail-closed paths, without a GPU or CPU replay."""
from cpu_reference_guard import forbid_execution
import array,copy,hashlib,json,os,struct,sys,tempfile,unittest
from contextlib import nullcontext,contextmanager
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as product
from portable_projectile_roster_input import compile_projectile_battle

from historical_engine_reference import historical_reference

class PortableDetail(unittest.TestCase):
    @staticmethod
    def synthetic_stationary_readback(words):
        # Transport fixtures model the scheduler's mandatory root-start marker;
        # they remain synthetic bytes, never real GPU calculation evidence.
        from portable_specs import LIMITS as L
        block=array.array('I',[0])*words;head=L['WORLD_FRAME_OUTPUT_BASE']
        block[head+1]=1;block[head+784]=32
        return block.tobytes()

    def test_product_keeps_all_equipment_rows_and_uses_native_carrier_lifecycle(self):
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        body=selected_profile_bodies(['N102'],0)[0][2]
        body.update(duration=15,burst_gauge_mode='accumulate')
        body['profile']['chars']['N102']['equip_skills']['charge_speed_pct']=[4.3,6.2]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU state as input')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            _,_,_,actual,metadata=product.compile_product(prepared)
            standalone,oldmeta=compile_projectile_battle(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(metadata['effects'],oldmeta['effects'])
        self.assertEqual(metadata['real_prepared_input']['equipment_quantity_carriers'],'native-named-state-v1')
        rows=[i for i,r in enumerate(prepared['effects']) if r['owner']=='N102' and r['effect'].get('stat')=='charge_speed_pct' and r['effect'].get('_source_tag')=='equipment']
        self.assertEqual(len(rows),2)
        changed={i for i,(a,b) in enumerate(zip(actual,standalone)) if a!=b}
        self.assertEqual(changed,{L['RECIPIENT_BASE']+i*8+7 for i in rows})
        for i in rows:
            at=L['RECIPIENT_BASE']+i*8+7
            self.assertEqual(standalone[at]&3,0);self.assertEqual(actual[at]&3,3)
        self.assertEqual(len(actual),len(standalone))

    def test_product_burst_pattern_literals_share_policy_and_never_pack_cpu_state(self):
        from portable_burst_control_specs import product_patterns
        from portable_specs import LIMITS as L
        names=[c['name'] for c in self.prepared['chars']]
        for pattern,word in [('every:3',(1<<11)|(3<<13)),([1,3,5,9,11,14],(2<<11)|(0x2515<<13)),(None,3<<11),([],2<<11)]:
            with self.subTest(pattern=pattern):
                self.assertEqual(product_patterns(names,{names[0]:pattern}),[word,0,0,0,0])
                changed=copy.deepcopy(self.prepared)
                changed['policies']['config']['burst_pattern']={names[0]:pattern}
                changed['chars'][0].setdefault('control',{})['burst']={'pattern':pattern}
                changed['policies']['controls'][names[0]]=copy.deepcopy(changed['chars'][0]['control'])
                before=copy.deepcopy(changed)
                with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                    _,iw,ow,words,meta=product.compile_product(changed)
                self.assertEqual(changed,before)
                self.assertFalse(meta['product_burst_patterns']['cpu_schedule_or_state_supplied'])
                _,oiw,oow,original,_=product.compile_product(self.prepared)
                expected=list(original);expected[L['WEAPON_BASE']+3]|=word
                self.assertEqual(words,expected);self.assertEqual((iw,ow),(oiw,oow))
        for pattern in ('every:0','every:524288',[20],[512],True):
            with self.subTest(pattern=pattern),self.assertRaises(ValueError):product_patterns(names,{names[0]:pattern})
        with self.assertRaises(ValueError):product_patterns(names,{'unknown':'every:3'})

    def test_product_burst_cycle_readback_is_validated_without_click_controls(self):
        from portable_world_result import read_product_control_log
        from portable_specs import LIMITS as L
        block=array.array('I',[0])*786432;h=L['WORLD_CONTROL_HEAD_BASE']
        block[h]=0x57434831;block[h+14]=2;block[h+15]=0x50425031;block[8]=30
        meta=dict(product_burst_patterns=dict(encoded=[1<<11]),product_control_labels=[[],[],[],[],[]])
        trace=[dict(event=5),dict(event=3),dict(event=5)]
        self.assertIsNone(read_product_control_log(block,meta,['a','b','c','d','e'],1.,burst_trace=trace))
        for offset,value in [(h,0),(h+15,0),(h+14,1),(h+14,31)]:
            bad=array.array('I',block);bad[offset]=value
            with self.subTest(offset=offset,value=value),self.assertRaises(product.UnsupportedPortable):
                read_product_control_log(bad,meta,['a','b','c','d','e'],1.,burst_trace=trace)

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
        block[head+1]=1;block[head+784]=32
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
        for name,stat in [('얀','force_move'),('유니','enemy_movement_disable'),('스노우 화이트 : 헤비암즈','lock_on')]:
            body=selected_profile_bodies([name],0)[0][2];body.update(burst_gauge_mode='fixed',compute_backend='native_detail')
            body['enemy']['patterns']=[dict(id='future-target',kind='summon',delay=5.,spec=dict(count=1,hp=1e8))]
            if stat=='lock_on':
                # Ordinary ADD markers are supported; the declared magazine/lock
                # composition still requires its own connected consumer.
                body['reference_models']={'enemy_ammo':[dict(label='__enemy__',capacity=16,initial=16,reload_seconds=1.,cancel_on_full=True)]}
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
            actual=product.decode_payload(body,self.prepared,self.prepared_run,self.metadata,[0])
        expected=[row for row in self.fixture['cpu_payload']['burst_timeline']
                  if not row['event'].startswith(('카메라 초점:','게이지 만충'))]
        self.assertEqual(actual['burst_timeline'],expected)
        self.assertEqual(actual['burst_gauge_mode'],'fixed')











    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/'tests/fixtures/portable-detail-product-v1.json').read_text(encoding='utf-8'));cls.fixture['body']['compute_backend']='native_detail'
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('Preparation must not run a battle')):
            cls.prepared,cls.prepared_run=product.prepare(cls.fixture['body'])
            cls.words,cls.metadata=compile_projectile_battle(cls.prepared)
    @historical_reference
    def test_saved_actual_gpu_projection_reconstructs_complete_original_product_payload(self):
        with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
            payload=product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[0])
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
                    product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[0])
    def test_declared_warning_precedes_policy_and_hypothetical_notices(self):
        from product_reference_models import WARNING
        model=dict(schema=1,evidence='declared-model-not-game-verification',
            declarations={'enemy_healing':[{'node':'heal'}]},enemy_healing={'receipts':[]})
        body=copy.deepcopy(self.fixture['body'])
        body.update(burst_policy='mast3',stat_deltas={body['squad'][0]:{'atk':100}})
        run=copy.copy(self.prepared_run);run._portable_detail_model_warnings=['effect model']
        metadata=dict(self.metadata,product_enemy_healing=True)
        with patch.object(product,'decode',return_value=self.fixture['gpu_projection']),\
             patch('portable_product_healing.read_result',return_value=model),\
             patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
            payload=product.decode_payload(body,self.prepared,run,metadata,[0])
        self.assertEqual(payload['app_warnings'],[
            self.fixture['cpu_payload']['app_warnings'][0],'effect model',WARNING,
            'マスト：ロマンチックメイドがいないため、3の倍数指定は適用せず全員オートで計算しました。',
            '仮ステータスを含みます。ゲーム内で可能な育成を示すものではありません。'])

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
                payload=product.decode_payload(body,prepared,run,self.metadata,[0])
            self.assertEqual(payload['app_warnings'],[self.fixture['cpu_payload']['app_warnings'][0],warning])
    def test_backend_failure_preserves_cpu_label_and_strips_internal_request_flags(self):
        body={**self.fixture['body'],'compute_backend':'native_detail','_compile_detail':True}
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
                self.assertEqual(result['compute']['requested'],'native_detail')
                self.assertFalse(result['compute']['gpu_execution_verified'])
                self.assertNotIn('_compile_detail',calls[0])
                self.assertEqual(len(list(Path(folder).glob('*/result.json'))),1)
                record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                self.assertEqual(record['error_type'],type(error).__name__)
                self.assertEqual(record['error'],str(error))
                self.assertNotIn('audit metadata incomplete',record['error'])
    def test_invalid_product_parts_fall_back_before_any_gpu_dispatch(self):
        body=copy.deepcopy(self.fixture['body']);body['compute_backend']='native_detail';body['enemy']['parts']=[dict(id='example')]
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),\
             patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
             patch.object(product,'execute',side_effect=AssertionError('No dispatch')),\
             patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
            result=product.evaluate(body)
            self.assertEqual(result['compute']['backend'],'cpu')
            self.assertIn('パーツ',result['compute']['unsupported'][0]['reason'])
    @historical_reference
    def test_both_backends_use_identical_inputs_decoder_and_post_readback_cpu_check(self):
        wires=[]
        for requested,backend in ((k,v) for k,v in product.BACKENDS.items() if v!="browser"):
            body={**self.fixture['body'],'compute_backend':requested}
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in input')):
                prepared,run=product.prepare(body)
            expected=copy.deepcopy(self.fixture['cpu_payload']);expected['evaluator']=product.engine_worker.sim.evaluator()
            events=[]
            def execute(source,entry,packed,iw,ow,actual_backend,*,readback_path):
                self.assertEqual(actual_backend,backend);wires.append(packed);events.append('gpu')
                raw=self.synthetic_stationary_readback(ow);readback_path.write_bytes(raw)
                return None,dict(backend=backend,gpu_execution_verified=backend!='native',native_execution_verified=backend=='native',input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),
                    transport=dict(device='mock transport; not GPU evidence',cases=1,command_status='completed',**{'host_seconds' if backend=='native' else 'host_seconds' if backend=='native' else 'host_dispatch_seconds':.1}))
            def cpu(request):
                self.assertEqual(events,['gpu']);events.append('cpu');return copy.deepcopy(expected)
            with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,dict(NIKKE_DETAIL_CAPTURE_ROOT=folder,NIKKE_SLANG_GENERATION_CACHE=folder,NIKKE_CUDA_COMPILE_CACHE=folder,
                NIKKE_CUDA_ARTIFACT='ptx',NIKKE_CUDA_CACHE_REQUIRED='0',NIKKE_CUDA_PTXAS_OPT_LEVEL='3',NIKKE_SLANG_GENERATION_REQUIRED='0')),\
                patch.object(product.platform,'system',return_value='Windows'),patch('portable_native.availability',return_value={'available':True}),patch.object(product,'prepare',return_value=(prepared,run)),\
                patch.object(product,'decode',return_value=self.fixture['gpu_projection']),patch.object(product,'execute',side_effect=execute),patch.object(product.engine_worker,'evaluate',side_effect=cpu):
                result=product.evaluate(body);self.assertEqual(events,['gpu','cpu'])
                self.assertEqual(result['compute']['backend'],requested);self.assertTrue(result['compute']['cpu_verification']['matched'])
                self.assertIn('host_seconds' if backend=='native' else 'host_seconds' if backend=='native' else 'host_dispatch_seconds',result['compute'])
                self.assertNotIn('host_dispatch_seconds' if backend=='native' else 'host_seconds',result['compute'])
                record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                self.assertEqual(len(record['request_sha256']),64)
                self.assertEqual(record['capture_id'],result['compute']['capture_id'])
        self.assertEqual(len(wires),1)
        self.assertTrue(all(wire==wires[0] for wire in wires))
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
        for key,value in [('has_parts',True),('part_break_interval',1),('coord',{})]:
            case=copy.deepcopy(prepared);case['enemy'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'plain body'):product.compile_product(case)
        finite=copy.deepcopy(prepared);finite['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(count=1,hp=100))]
        source,iw,ow,words,meta=product.compile_product(finite)
        self.assertEqual(source,'gpu/product_add_target_battle_entry.slang')
        self.assertEqual(meta['product_world']['nodes'],[dict(id='wave',kind='summon')])
        self.assertEqual(meta['real_prepared_input']['target_modifier_carriers']['original_effects'],prepared['effects'])
        self.assertEqual(meta['product_add_attacks']['source_nodes'],[-1,0])
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
        source,iw,ow,words,meta=product.compile_product(bad)
        self.assertEqual(source,'gpu/product_add_group_target_battle_entry.slang')
        self.assertEqual(meta['product_world']['nodes'],[dict(id='new',kind='summon')])
        self.assertEqual(meta['real_prepared_input']['target_modifier_carriers'],axes)
        self.assertEqual(meta['product_add_attacks']['source_nodes'],[-1,0])
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


class ProductBatchProtocol(unittest.TestCase):
    """Protocol/fault injection only; mock transport is never GPU evidence."""

    @contextmanager
    def harness(self,folder,*,corrupt=False,fail=False,other_source=False,backend='native'):
        events=[];calls=[]
        def prepare(body):
            if body.get('invalid'):raise ValueError('declared invalid row')
            return dict(marker=body['seed']),None
        def compile_product(prepared):
            marker=prepared['marker'];source='gpu/second-entry.slang' if other_source and marker==1 else 'gpu/first-entry.slang'
            return source,2,4,[marker,777],{}
        def execute(source,entry,packed,iw,ow,actual_backend,*,readback_path):
            count=struct.unpack_from('<I',packed)[0];events.append('gpu');calls.append((source,count,packed))
            if fail:raise RuntimeError('transport failed; no retry')
            words=array.array('I')
            for index in range(count):
                marker=struct.unpack_from('<I',packed,4+index*iw*4)[0]
                words.extend([0,999 if corrupt and index==1 else marker,0,0])
            raw=words.tobytes();readback_path.write_bytes(raw)
            return None,dict(backend=backend,gpu_execution_verified=backend!='native',native_execution_verified=backend=='native',input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),
                transport=dict(device='mock protocol transport; no hardware',cases=count,command_status='completed',**{'host_seconds' if backend=='native' else 'gpu_seconds' if backend=='metal' else 'host_dispatch_seconds':.1}))
        def cpu(body):events.append(('cpu',body['seed']));return dict(marker=body['seed'])
        with patch.dict(os.environ,{'NIKKE_DETAIL_CAPTURE_ROOT':str(folder)}),patch.object(product,'execution_environment',return_value={}),\
             patch.object(product,'prepare',side_effect=prepare),patch.object(product,'compile_product',side_effect=compile_product),\
             patch.object(product,'execute',side_effect=execute),patch.object(product,'decode_payload',side_effect=lambda body,pre,run,meta,block:dict(marker=block[1])),\
             patch.object(product.engine_worker,'evaluate',side_effect=cpu),\
             patch('portable_capture_storage.space_status',side_effect=lambda path,needed:dict(passed=True,required_bytes=needed,reserve_bytes=0,free_bytes=needed+1)):
            yield calls,events

    def bodies(self,n=3,backend='native_detail'):
        return [dict(seed=i,compute_backend=backend,verify_detail=True,enemy={}) for i in range(n)]

    def test_compatible_cases_share_one_real_framing_and_preserve_individual_views(self):
        for backend,requested in [('native','native_detail')]:
            with self.subTest(backend=backend),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend=backend) as (calls,events):
                rows=product.evaluate_many(self.bodies(3,requested))
                self.assertEqual([r['result']['marker'] for r in rows],[0,1,2]);self.assertEqual(len(calls),1)
                self.assertEqual(calls[0][1],3);self.assertEqual(events,['gpu',('cpu',0),('cpu',1),('cpu',2)])
                batch_ids={r['result']['compute']['batch']['capture_id'] for r in rows};self.assertEqual(len(batch_ids),1)
                parent=Path(folder)/batch_ids.pop();physical=(parent/'input.bin').read_bytes()
                self.assertEqual(struct.unpack_from('<I',physical)[0],3)
                evidence=json.loads((parent/'evidence.json').read_text());self.assertEqual(evidence['transport']['cases'],3)
                self.assertEqual(evidence['input_sha256'],hashlib.sha256(physical).hexdigest())
                for index,row in enumerate(rows):
                    c=row['result']['compute'];member=c['batch'];case=Path(folder)/c['capture_id']
                    self.assertEqual((member['index'],member['cases']),(index,3))
                    self.assertEqual(c['input_sha256'],hashlib.sha256((case/'input.bin').read_bytes()).hexdigest())
                    self.assertEqual(c['output_sha256'],hashlib.sha256((case/'readback.bin').read_bytes()).hexdigest())
                    self.assertEqual(member['transport_input_sha256'],evidence['input_sha256'])
                    self.assertNotEqual(c['input_sha256'],member['transport_input_sha256'])
                    self.assertEqual(c['cpu_verification'],dict(matched=True,differing_fields=[]))

    def test_mismatching_case_rejects_only_its_own_gpu_payload_without_redispatch(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder,corrupt=True) as (calls,events):
            rows=product.evaluate_many(self.bodies())
            self.assertEqual(len(calls),1);self.assertEqual([r['result']['marker'] for r in rows],[0,1,2])
            self.assertEqual([r['result']['compute']['backend'] for r in rows],['native_detail','cpu','native_detail'])
            self.assertTrue(rows[1]['result']['compute']['gpu_result_rejected'])


    def test_incompatible_sources_are_not_packed_into_one_dispatch(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder,other_source=True) as (calls,_):
            rows=product.evaluate_many(self.bodies())
            self.assertEqual(sorted(n for _,n,_ in calls),[1,2]);self.assertEqual([r['result']['marker'] for r in rows],[0,1,2])
            self.assertTrue(all(r['result']['compute']['backend']=='native_detail' for r in rows))

    def test_bad_row_and_shared_failure_keep_all_indices_and_never_retry(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (calls,_):
            bodies=self.bodies();bodies[1]['invalid']=True;rows=product.evaluate_many(bodies)
            self.assertEqual(len(calls),1);self.assertEqual(calls[0][1],2)
            self.assertEqual([r['result']['marker'] for r in rows],[0,1,2]);self.assertEqual(rows[1]['result']['compute']['backend'],'cpu')
        with tempfile.TemporaryDirectory() as folder,self.harness(folder,fail=True) as (calls,_):
            rows=product.evaluate_many(self.bodies());self.assertEqual(len(calls),1)
            self.assertTrue(all(r['result']['compute']['backend']=='cpu' for r in rows))
        for bodies in ([],self.bodies(33),{}):
            with self.assertRaises(ValueError):product.evaluate_many(bodies)

    def test_storage_shortage_stops_before_gpu_instead_of_shrinking_the_batch(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (calls,_),\
             patch('portable_capture_storage.space_status',return_value=dict(passed=False)):
            rows=product.evaluate_many(self.bodies())
            self.assertEqual(calls,[])
            self.assertTrue(all(r['result']['compute']['backend']=='cpu' for r in rows))
            self.assertTrue(all('Insufficient space' in r['result']['compute']['unsupported'][0]['reason'] for r in rows))

    def test_real_static_preparation_restores_aliases_between_different_cases(self):
        from portable_product_programs import body_for_program
        from calculator import timeline
        from runner import spec
        from calculator.buff_manager import BuffManager
        a=body_for_program(ROOT,'fixed');b=body_for_program(ROOT,'healing-cover-fixed')
        b['stat_deltas']={b['squad'][0]:dict(atk=12345)}
        before=(spec.calc_base_stats,timeline.calc_base_stats,BuffManager._make_cube_effects)
        def packed(body):
            pre,_=product.prepare(body);_,_,_,words,_=product.compile_product(pre)
            return array.array('I',[1,*words]).tobytes()
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in batch static preparation')):
            first=packed(a);packed(b);last=packed(a)
        self.assertEqual(first,last)
        self.assertEqual(before,(spec.calc_base_stats,timeline.calc_base_stats,BuffManager._make_cube_effects))

    def test_gpu_stage_exceptions_fall_back_once_with_stage_and_traceback(self):
        import subprocess
        for backend,requested in [('native','native_detail')]:
            for function,stage in [('prepare','prepare'),('compile_product','compile'),('execute','transport'),('decode_payload','decode')]:
                for error in (AttributeError('attribute fault'),IndexError('index fault'),subprocess.TimeoutExpired('mock transport',1)):
                    with self.subTest(backend=backend,function=function,error=type(error).__name__),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend=backend) as (_,events),patch.object(product,function,side_effect=error):
                        result=product.evaluate(self.bodies(1,requested)[0]);compute=result['compute']
                        self.assertEqual(result['marker'],0);self.assertEqual(compute['backend'],'cpu')
                        self.assertEqual(compute['fallback_stage'],stage);self.assertEqual(events.count(('cpu',0)),1)
                        self.assertEqual(compute['unsupported'][0]['reason'],str(error))
                        record=json.loads((Path(folder)/compute['capture_id']/'result.json').read_text())
                        self.assertEqual(record['stage'],stage);self.assertEqual(record['error_type'],type(error).__name__)
                        self.assertIn(type(error).__name__,record['traceback']);self.assertNotIn('cpu_error',record)

    def test_cpu_exception_is_recorded_and_propagated_without_second_evaluation(self):
        for gpu_failure in (False,True):
            for error in (ValueError('CPU input rejected'),IndexError('CPU index fault')):
                with self.subTest(gpu_failure=gpu_failure,error=type(error).__name__),tempfile.TemporaryDirectory() as folder,self.harness(folder),patch.object(product.engine_worker,'evaluate',side_effect=error) as cpu:
                    with (patch.object(product,'compile_product',side_effect=AttributeError('GPU compile fault')) if gpu_failure else nullcontext()):
                        with self.assertRaises(type(error)) as caught:product.evaluate(self.bodies(1)[0])
                    self.assertIs(caught.exception,error);cpu.assert_called_once()
                    record=json.loads(next(Path(folder).glob('*/result.json')).read_text())
                    self.assertEqual(record['cpu_error']['error_type'],type(error).__name__)
                    self.assertEqual(record['cpu_error']['stage'],'cpu');self.assertIn(str(error),record['cpu_error']['traceback'])
                    self.assertEqual('unsupported' in record,gpu_failure)
                    self.assertFalse(record['gpu_execution_verified'])
                    self.assertEqual(record['native_execution_verified'],not gpu_failure)

    def test_base_exceptions_are_not_converted_to_fallback_or_batch_error(self):
        for function in ('prepare','compile_product','execute','decode_payload'):
            for error in (KeyboardInterrupt('cancel'),SystemExit(7)):
                for batch in (False,True):
                    with self.subTest(function=function,error=type(error).__name__,batch=batch),tempfile.TemporaryDirectory() as folder,self.harness(folder) as (_,events),patch.object(product,function,side_effect=error):
                        with self.assertRaises(type(error)) as caught:
                            if batch:product.evaluate_many(self.bodies(1))
                            else:product.evaluate(self.bodies(1)[0])
                        self.assertIs(caught.exception,error)
                        self.assertFalse(any(isinstance(event,tuple) and event[0]=='cpu' for event in events))

    def test_one_batch_decode_exception_does_not_change_other_rows_or_retry(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (calls,events):
            def decode(body,pre,run,metadata,block):
                if pre['marker']==1:raise IndexError('one decoder failed')
                return dict(marker=block[1])
            with patch.object(product,'decode_payload',side_effect=decode):rows=product.evaluate_many(self.bodies())
            self.assertEqual(len(calls),1);self.assertEqual([row['result']['marker'] for row in rows],[0,1,2])
            self.assertEqual([row['result']['compute']['backend'] for row in rows],['native_detail','cpu','native_detail'])
            self.assertEqual(events,['gpu',('cpu',0),('cpu',1),('cpu',2)])
            self.assertEqual(rows[1]['result']['compute']['fallback_stage'],'decode')
            for i in (0,2):self.assertEqual(rows[i]['result']['compute']['cpu_verification'],dict(matched=True,differing_fields=[]))

    def test_inconsistent_ammo_metadata_is_explicitly_rejected_and_falls_back(self):
        original_decode=product.decode_payload
        with self.assertRaisesRegex(product.UnsupportedPortable,'inconsistent_ammo_metadata'):
            original_decode({},None,None,dict(product_ammo_cover=True),[])
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (_,events):
            def decode(body,pre,run,metadata,block):return original_decode(body,pre,run,dict(product_ammo_cover=True),block)
            with patch.object(product,'decode_payload',side_effect=decode):result=product.evaluate(self.bodies(1)[0])
            self.assertEqual(result['compute']['backend'],'cpu');self.assertEqual(events.count(('cpu',0)),1)
            self.assertEqual(result['compute']['unsupported'][0]['reason'],'inconsistent_ammo_metadata')

    def test_one_batch_cpu_exception_keeps_other_rows_and_evaluates_each_once(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (calls,events):
            def cpu(body):
                events.append(('cpu',body['seed']))
                if body['seed']==1:raise IndexError('one CPU row failed')
                return dict(marker=body['seed'])
            with patch.object(product.engine_worker,'evaluate',side_effect=cpu):rows=product.evaluate_many(self.bodies())
            self.assertEqual(rows[1],dict(error='one CPU row failed'));self.assertEqual(len(calls),1)
            self.assertEqual(events,['gpu',('cpu',0),('cpu',1),('cpu',2)])
            for i in (0,2):
                self.assertEqual(rows[i]['result']['compute']['backend'],'native_detail')
                self.assertEqual(rows[i]['result']['compute']['cpu_verification'],dict(matched=True,differing_fields=[]))
            records=[json.loads(p.read_text()) for p in Path(folder).glob('*/result.json')]
            errors=[r for r in records if 'cpu_error' in r];self.assertEqual(len(errors),1)
            self.assertEqual(errors[0]['cpu_error']['error_type'],'IndexError');self.assertNotIn('unsupported',errors[0])


    def test_native_32_members_each_receive_fresh_full_cpu_verification(self):
        for corrupt in (False,True):
            with self.subTest(corrupt=corrupt),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend='native',corrupt=corrupt) as (calls,events):
                bodies=self.bodies(32,'native_detail')
                # Verification remains mandatory even when the request says false.
                for body in bodies:body['verify_detail']=False
                rows=product.evaluate_many(bodies)
                self.assertEqual(len(calls),1);self.assertEqual(calls[0][1],32)
                self.assertEqual(events,['gpu']+[('cpu',i) for i in range(32)])
                self.assertEqual([r['result']['marker'] for r in rows],list(range(32)))
                for index,row in enumerate(rows):
                    c=row['result']['compute']
                    if corrupt and index==1:
                        self.assertEqual(c['backend'],'cpu');self.assertTrue(c['gpu_result_rejected'])
                    else:
                        self.assertEqual(c['backend'],'native_detail');self.assertTrue(c['native_execution_verified'])
                        self.assertFalse(c['gpu_execution_verified']);self.assertTrue(c['cpu_verification']['matched'])
                        self.assertEqual(c['host_seconds'],.1)
                record=json.loads((Path(folder)/rows[0]['result']['compute']['batch']['capture_id']/'result.json').read_text())
                self.assertFalse(record['gpu_execution_verified']);self.assertTrue(record['native_execution_verified'])
        with self.assertRaises(ValueError):product.evaluate_many(self.bodies(33,'native_detail'))
