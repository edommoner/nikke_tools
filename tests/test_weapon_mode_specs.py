"""Shared mode toggle and equivalent-ammunition contract, not character copies."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
import engine_worker
import detail_gpu as g
from weapon_mode_specs import toggle_flag,extra_ammo_count,TOGGLE_FLAG,AMMO_EQUIVALENT
from test_target_counter_runtime import manager,NAMES

def effect(name,kind,stat,value,event='on_attack',**kw):
    return dict(dict(name=name,source='스킬1',type=kind,stat=stat,fixed_value=value,target='self',trigger=dict(timing=[event],condition=[])),**kw)
def mode(name='mode',event='on_attack',**kw):return effect(name,'weapon_change','',0,event,**dict(dict(weapon_type='SR',damage_coeff=100,max_ammo=6,toggle=True,duration=.3),**kw))
def chars():return [dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]

class WeaponModeSpecs(unittest.TestCase):
    def test_declarative_flags_and_ammo_rounding_bounds(self):
        self.assertEqual(toggle_flag(mode()),TOGGLE_FLAG);self.assertEqual(toggle_flag(mode(toggle=False)),0)
        for value,expected in ((-1,0),(0,0),(1,0),(1.9,0),(4.9,3),(40,39),(4096,4095)):
            self.assertEqual(extra_ammo_count(value),expected)
        for bad in (True,'4',float('inf'),4097):
            with self.assertRaises(ValueError):extra_ammo_count(bad)
        for bad in (mode(toggle=1),mode(name=''),effect('bad','buff','atk_pct',1,toggle=True)):
            with self.assertRaises(ValueError):toggle_flag(bad)

    def test_compiled_commands_reject_ambiguous_or_forged_metadata(self):
        stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES}
        es=[mode(),effect('ammo','instant','squad_ammo_consume_as',40)]
        p=g.compile_effects(chars(),[(e,NAMES[0]) for e in es])
        self.assertEqual(p['effects'][0][213],TOGGLE_FLAG);self.assertEqual(p['effects'][1][1],AMMO_EQUIVALENT)
        for index,field,value in ((0,35,0),(0,1,4),(1,4,1),(1,10,2),(1,6,4097),(1,213,TOGGLE_FLAG)):
            forged=copy.deepcopy(p);forged['effects'][index][field]=value
            with self.subTest(index=index,field=field),self.assertRaises(ValueError):g.run(None,[forged],[[0,2,0,0,-1,0,0,0]],[[0,0]],[stats])
        for changes in ({'scaling':'stack_count','scaling_ref':'x'},{'target':'all_allies'},{'fixed_value':4097}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):g.compile_effects(chars(),[({**es[1],**changes},NAMES[0])])

    def test_cpu_mode_toggle_and_expiry_use_the_same_end_notification(self):
        observer=effect('ended','buff','atk_pct',1,'event:state_end:mode',duration=-1,max_stack=100)
        bm=manager([mode(),observer]);seen=[];original=bm.notify
        def notify(event,t,caster,**kw):
            if event=='event:state_end:mode':seen.append(bm.weapon_change_name(caster))
            return original(event,t,caster,**kw)
        bm.notify=notify
        for at,expected in ((0,'mode'),(.1,''),(.2,'mode')):
            bm.tick(at);bm.notify('on_attack',at,NAMES[0]);self.assertEqual(bm.weapon_change_name(NAMES[0]),expected)
        bm.tick(.51);self.assertEqual(bm.weapon_change_name(NAMES[0]),'')
        self.assertEqual(seen,['','']);self.assertEqual(bm.get_buffs(NAMES[0],'__enemy__',.51)['atk_pct'],2)

    def test_cpu_nested_equivalent_notices_preserve_outer_remainder(self):
        es=[effect('outer','instant','squad_ammo_consume_as',8.9),effect('child','instant','squad_ammo_consume_as',3,'squad_ammo_consume:4',max_trigger=1),effect('all notices','buff','atk_pct',1,'squad_ammo_consume:1',duration=-1,max_stack=100),effect('every three','buff','atk_pct',1,'squad_ammo_consume:3',duration=-1,max_stack=100)]
        bm=manager(es,[0,2,3,1]);bm.state['ammo']={n:6 for n in NAMES}
        bm.notify('on_attack',0,NAMES[0]);bm.notify('squad_ammo_consume',0,NAMES[0])
        self.assertEqual(bm.get_buffs(NAMES[3],'__enemy__',0)['atk_pct'],10)
        self.assertEqual(bm.get_buffs(NAMES[1],'__enemy__',0)['atk_pct'],3)
        self.assertTrue(all(v==6 for v in bm.state['ammo'].values()))

if __name__=='__main__':unittest.main()
