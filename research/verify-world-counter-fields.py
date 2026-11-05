"""One typed completion-field fixture table and oracle for both GPU backends."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_counter_field_cases as cases
s=importlib.util.spec_from_file_location('context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/counter_field_entry.slang'
def fixtures():return cases.fixtures(physical)
def compile_case(case):
 return cases.compile_case(physical,case)
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];field=len(rows[0]['effects'])-1;packet=L['DAMAGE_DEFINITION_BASE']+field*8;definition=L['DEFINITION_BASE']+field*L['DEFINITION_WORDS']
 for name,at,value in [('unknown-field-mode',L['TARGET_COUNTER_INPUT_BASE']+6,6),('fields-without-native-landings',L['LANDING_META_BASE'],0),('field-route-overflow',packet,10),('field-count-zero',packet+1,0),('field-count-overflow',packet+1,257),('field-stat-overflow',definition+F['STAT'],100),('field-damage-kind-not-yet-admitted',definition+F['KIND'],3),('counter-condition-not-yet-admitted',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['CONDITION_COUNT'],1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 c=copy.deepcopy(rows[0]);c['effects'].append(dict(name='unported-damage-child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,target='boss',trigger=dict(timing=['event:target_counter_complete:marker'],condition=[])));c['owners'].append(0);bad.append(('unported-queued-damage-child',compile_case(c)[0]))
 w=list(seed);w[definition+F['INTERVAL']:definition+F['INTERVAL']+2]=list(struct.unpack('<II',struct.pack('<d',.1)));bad.append(('unported-periodic-counter-field',w))
 return rows,programs,bad
