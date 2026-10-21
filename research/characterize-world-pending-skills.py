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
def main():
 rows=[]
 for case in fixtures():
  native,trace=suite.inspect_native(case);words,_,_=suite.compile_case(case);pending=[i for i,e in enumerate(case['effects']) if e.get('type')=='damage']
  assert all(words[suite.L['DAMAGE_DEFINITION_BASE']+i*8+6]==1 for i in pending)
  assert all(r['created']==r['landed'] and r['created']>0 for r in trace)
  rows.append(dict(name=case['name'],case=case,native=native,skill_trace=trace))
 by={r['name']:r['skill_trace'] for r in rows};base=by['pending-baseline'][0]['amount'];assert base==354
 assert by['pending-after-attack-buff'][0]['amount']==base and by['pending-before-attack-buff'][0]['amount']>base
 assert by['pending-body-enemy-field'][0]['amount']>base and by['pending-normal-only-modifier'][0]['amount']==base
 assert by['pending-all-three-recipients'][0]['recipients']==[0,1,2]
 assert [r['amount'] for r in by['pending-two-amounts-before-first-counter-child']]==[base,base]
 assert not by['pending-zero-coefficient']
 assert by['pending-precedes-explicit-normal-formula'][0]['amount']==base
 legacy=copy.deepcopy(next(c for c in fixtures() if c['name']=='pending-after-attack-buff'));legacy['observe_authored_effect_lookup']=False
 _,legacy_trace=suite.inspect_native(legacy);assert legacy_trace[0]['amount']==748 and by[legacy['name']][0]['amount']==354
 result=dict(passed=True,cases=rows,full_native_battles=9,gpu_calls=0,gpu_pending_connected=False,actual_typed_pending_admission='Rejected by current common admission;GPU not executed in this characterization',authored_effect_lookup_native_guard=dict(with_original_catalog=legacy_trace[0]['amount'],with_literal_catalog=by[legacy['name']][0]['amount']),authored_effect_lookup_observer_finding='RESOLVED opt-in literal char_effects catalog; initial wrong later-buff inclusion retained in initial native report',pending_precedes_explicit_normal_formula=True,same_frame_pending_landing=True,amount_batch_captured_before_first_landing=True,later_cast_buff_excluded=True,earlier_cast_buff_included=True,ordinary_skill_queue_next_frame_is_different=True,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('app/portable_runtime.py','research/characterize-world-pending-skills.py','research/world_frame_native.py','research/world_skill_native.py','gpu/world_skill_runtime.slang')},full_goal_complete=False)
 (ROOT/'research/portable-world-pending-skill-native-contract.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Pending native9:same-frame drain,batch snapshot,later-buff exclusion;GPU0')
if __name__=='__main__':main()
