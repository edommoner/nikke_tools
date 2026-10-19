import importlib.util,math,struct,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from portable_stack_specs import plan,value,META_MAGIC
from portable_specs import LIMITS as L,FIELDS as F
from test_target_counter_runtime import manager,NAMES
s=importlib.util.spec_from_file_location('stack_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def buff(stat='atk_pct'):
    return dict(name='seed',source='스킬1',type='buff',stat=stat,fixed_value=10,target='self',duration=2,max_stack=5,trigger=dict(timing=['event:full_reload'],condition=[]))
def operation(stat='buff_stack_add'):
    return dict(name='operation',source='스킬1',type='instant',stat=stat,fixed_value=2,target='self',target_effect='seed',trigger=dict(timing=['on_attack'],condition=[]))
def case(effects):return dict(name='unit',effects=effects,script=[[0,0,19,0,0,-1,0,0],[1,0,7,0,0,-1,0,0],[1,2,0,0,-1,0,0,0]])

class StackContracts(unittest.TestCase):
    def test_cpu_hp_boundary_preserves_stack_child_before_hp_crossing(self):
        seed=buff('max_hp_pct');op=operation();child=buff();child.update(name='stack child',trigger=dict(timing=['stack_reach:seed:3'],condition=[]))
        hp=buff();hp.update(name='hp child',trigger=dict(timing=['hp_below:95'],condition=[]))
        bm=manager([seed,op,child,hp]);bm.state.update(hp={n:10000 for n in NAMES},hp_pct={n:100 for n in NAMES});bm.notify('event:full_reload',0,NAMES[0]);self.assertEqual(bm.state['hp_pct'][NAMES[0]],100)
        seen=[];activate=bm._activate
        def record(e,c,t,*args,**kwargs):
            seen.append((e['name'],bm.state['hp_pct'][NAMES[0]]));return activate(e,c,t,*args,**kwargs)
        bm._activate=record;bm.notify('on_attack',1,NAMES[0])
        self.assertEqual([n for n,_ in seen],['operation','stack child','hp child'])
        self.assertEqual(seen[1][1],100)
        self.assertAlmostEqual(bm.state['hp_pct'][NAMES[0]],11000/13000*100)
        self.assertEqual(bm.state['hp'][NAMES[0]],11000)
    def test_literal_duration_and_first_init_binding_share_nonweapon_union(self):
        seed=buff();seed.update(duration=None,duration_values={'10':2})
        words,meta=v.compile_case(case([seed,operation('buff_stack_init')]))
        self.assertEqual(words[L['MODE_BASE']:L['MODE_BASE']+5],[META_MAGIC,1,0,0x7ff00000,0])
        self.assertEqual(words[L['MODE_BASE']+L['MODE_WORDS']+4],1)
        self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[L['DEFINITION_BASE']+F['DURATION']:L['DEFINITION_BASE']+F['DURATION']+2]))[0],2)
    def test_initialized_runtime_policy_differs_from_normal_duration_values(self):
        seed=buff();seed.update(duration=None,duration_values={'10':2},trigger=dict(timing=['event:full_reload'],condition=['self_state:gate']))
        words,_=v.compile_case(case([seed,operation('buff_stack_init')]))
        self.assertEqual(words[L['MODE_BASE']+5],1)
        self.assertEqual(words[L['DEFINITION_BASE']+F['FLAGS']]&2,2) # Potential predicate; finite normal lifetime still suppresses re-evaluation.
        normal=manager([seed,operation('buff_stack_init')]);normal._activate(normal._effects[0][0],NAMES[0],0)
        initialized=manager([seed,operation('buff_stack_init')]);initialized.notify('on_attack',0,NAMES[0])
        self.assertFalse(normal._active[0].has_runtime_conditions)
        self.assertTrue(initialized._active[0].has_runtime_conditions)
    def test_same_name_stack_instants_are_independent_definitions(self):
        a=operation();b=operation('buff_stack_remove');words,_=v.compile_case(case([buff(),a,b]))
        self.assertEqual([words[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['KIND']] for i in range(3)],[0,16,17])
    def test_generic_debuff_name_and_zero_reference_are_explicit(self):
        e=operation('debuff_stack_add');e.update(target_effect='',scaling='stack_count',scaling_ref='zero')
        words,meta=v.compile_case(case([buff(),e]));at=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
        self.assertEqual(words[at+F['TARGET_NAME']],0xffffffff)
        self.assertEqual(words[L['REFERENCE_DEFINITION_BASE']+4]&3,1)
        self.assertEqual(words[at+F['FLAGS']]&4,0)
        self.assertIn('zero',meta['resource_names'])
    def test_malformed_stack_definitions_fail_before_any_gpu(self):
        for update in [dict(type='buff'),dict(target=[]),dict(target_effect=7),dict(scaling='lost_hp_pct'),dict(scaling='stack_count',scaling_ref='bad:ref')]:
            with self.subTest(update=update),self.assertRaises(ValueError):plan(dict(operation(),**update))
        e=operation('buff_max_stack_add');e['type']='buff';e['fixed_value']=2**53+1
        with self.assertRaises(ValueError):value(e,{})
        e['fixed_value']=10**400
        with self.assertRaises(ValueError):value(e,{})
    def test_cpu_single_layer_zero_keeps_value_and_can_refresh(self):
        seed=buff();seed['max_stack']=1;e=operation('debuff_stack_remove');e['fixed_value']=1
        bm=manager([seed,e]);bm.notify('event:full_reload',0,NAMES[0]);bm.notify('on_attack',.5,NAMES[0]);bm.notify('event:full_reload',1,NAMES[0])
        self.assertEqual(bm._active[0].stack,0);self.assertEqual(bm._active[0].expires_at,3)
        self.assertEqual(bm.get_buffs(NAMES[0],'__enemy__',1)['atk_pct'],10)

if __name__=='__main__':unittest.main()
