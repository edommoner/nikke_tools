"""Full-native B3 pending timing and batch snapshots; no GPU execution."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from target_counter_cases import marker
s=importlib.util.spec_from_file_location('pending_skill_native','research/verify-world-skills.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
def buff(name,stat,value,target='self',timing='burst_cast'):
 return dict(name=name,source='스킬3',type='buff',stat=stat,fixed_value=value,target=target,duration=-1,trigger=dict(timing=[timing],condition=[]))
def fixtures():
 c=copy.deepcopy(suite.fixtures()[0]);c.update(name='pending-baseline',duration=1,observe_authored_effect_lookup=True);c['patterns'][0]['until']={'time':1}
 for i,w in enumerate(c['combat']['weapons']):w.update(stage=[3,1,2,0,0][i],gauge=0,cooldown=40,interval=10)
 c['effects']=[dict(name='start-gauge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])),dict(name='pending',source='스킬3',type='damage',stat='bonus_damage',fixed_value=25,target='boss',trigger=dict(timing=['burst_cast'],condition=[]))];c['owners']=[0,0];rows=[c]
 for before in (False,True):
  q=copy.deepcopy(c);q['name']='pending-'+('before' if before else 'after')+'-attack-buff'
  at=1 if before else 2;q['effects'].insert(at,buff('cast-attack','atk_pct',100));q['owners'].insert(at,0);rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-body-enemy-field';q['effects'].append(buff('body-received','received_dmg_pct',25,'boss','battle_start'));q['owners'].append(0);rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-normal-only-modifier';q['effects'].append(buff('normal-only','normal_atk_dmg_pct',50,'self','battle_start'));q['owners'].append(0);rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-all-three-recipients';q['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=2,hp=10000)));q['effects'][1]['target']='all_enemies';rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-two-amounts-before-first-counter-child'
 counter=marker(name='pending-counter',threshold=1,actor=dict(kind='body',identity=0,generation=1),families=['skill']);counter['target']='boss';counter['trigger']['timing']=['battle_start']
 q['effects'].append(copy.deepcopy(q['effects'][1]));q['effects'][-1]['name']='pending-second';q['effects'].extend([counter,buff('received-after-first','received_dmg_pct',50,'boss','event:target_counter_complete:pending-counter')]);q['owners'].extend([0,0,0]);rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-zero-coefficient';q['effects'][1]['fixed_value']=0;rows.append(q)
 q=copy.deepcopy(c);q['name']='pending-precedes-explicit-normal-formula';q['effects'][1]['damage_formula']='normal_attack';q['effects'].append(buff('normal-only','normal_atk_dmg_pct',50,'self','battle_start'));q['owners'].append(0);rows.append(q)
 return rows
