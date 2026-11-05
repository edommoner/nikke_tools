"""One typed completion-context fixture table and oracle for both GPU backends."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_counter_context_cases as cases
s=importlib.util.spec_from_file_location('context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/counter_context_entry.slang'
def fixtures():return cases.fixtures(physical)
def compile_case(case):
 return cases.compile_case(physical,case)
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];probe=len(rows[0]['effects'])-1;condition=L['CONDITION_BASE']+probe*L['CONDITION_WORDS']
 for name,at,value in [('unknown-context-mode',L['TARGET_COUNTER_INPUT_BASE']+6,4),('context-without-native-landings',L['LANDING_META_BASE'],0),('unknown-context-condition',condition,999),('predicate-nonzero-argument',condition+3,0x3ff00000),('counter-condition-not-yet-admitted',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['CONDITION_COUNT'],1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 named=next(p[0] for c,p in zip(rows,programs) if c['name']=='body-completion-versus-lifesteal-order-target_state:marker')
 w=list(named);w[condition+1]=256;bad.append(('context-name-overflow',w))
 for stat,kind,value in [('bonus_damage','damage',100),('received_dmg_pct','buff',10)]:
  c=copy.deepcopy(rows[0]);c['effects'].append(dict(name='unported-context-child',source='스킬1',type=kind,stat=stat,fixed_value=value,target='boss',duration=.3,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));c['owners'].append(0)
  bad.append(('unported-child-'+kind,compile_case(c)[0]))
 c=copy.deepcopy(rows[0]);c['effects'][-1].update(stat='max_hp_pct',duration=-1);c['effects'][-1]['trigger']['condition']=['target_state:marker'];bad.append(('unresolved-native-permanent-health-condition',compile_case(c)[0]))
 return rows,programs,bad
