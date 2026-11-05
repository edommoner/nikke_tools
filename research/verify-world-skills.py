"""One full-native late-routing skill table and oracle for both GPU backends."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
import world_skill_cases as cases
from world_skill_native import inspect as inspect_native
s=importlib.util.spec_from_file_location('context_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/world_skill_entry.slang'
def fixtures():return cases.fixtures(physical)
def compile_case(case):
 return cases.compile_case(physical,case)
from portable_skill_history import decode_prefix as skill_trace
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];skill=next(i for i,e in enumerate(rows[0]['effects']) if e.get('type')=='damage');definition=L['DEFINITION_BASE']+skill*L['DEFINITION_WORDS'];packet=L['DAMAGE_DEFINITION_BASE']+skill*8
 for name,at,value in [('unknown-skill-mode',L['TARGET_COUNTER_INPUT_BASE']+6,8),('skill-without-native-landings',L['LANDING_META_BASE'],0),('skill-route-overflow',packet,10),('skill-recipient-zero',packet+1,0),('skill-recipient-overflow',packet+1,129),('skill-hit-overflow',packet+2,257),('skill-explicit-parts-unported',definition+F['DAMAGE_FLAGS'],65536),('skill-dot-unported',definition+F['DAMAGE_FLAGS'],128),('skill-flags-overflow',definition+F['DAMAGE_FLAGS'],0x80000000)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 w=list(seed);w[definition+F['INTERVAL']:definition+F['INTERVAL']+2]=list(struct.unpack('<II',struct.pack('<d',.1)));bad.append(('skill-periodic-unported',w))
 return rows,programs,bad
