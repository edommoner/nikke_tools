"""One native oracle and literal input suite for CUDA/Metal enemy attack fields."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from world_frame_native import observe
import world_enemy_attack_cases as cases
s=importlib.util.spec_from_file_location('enemy_attack_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/world_enemy_attack_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
def compile_case(case):
 w,m,b=physical.pack.compile_case(case,allow_no_counter=True);w[0]=L['WORLD_ENEMY_ATTACK_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=13;return w,m,b
def decoded(block,meta,case,bindings):
 r=physical.decoded(block,meta,case,bindings);r['enemy_attack_fields']=[dict(kind=int(b.kind),identity=b.identity,flat=struct.unpack('<d',struct.pack('<II',*block[L['WORLD_ENEMY_ATTACK_BASE']+i*2:L['WORLD_ENEMY_ATTACK_BASE']+(i+1)*2]))[0]) for i,b in enumerate(bindings)];return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[1][0];bad=[];d=L['DEFINITION_BASE']
 for name,at,value in [('enemy-attack-old-mode11',L['TARGET_COUNTER_INPUT_BASE']+6,11),('enemy-attack-unknown-mode14',L['TARGET_COUNTER_INPUT_BASE']+6,14),('enemy-attack-stat-overflow',d+F['STAT'],100),('enemy-attack-recipient-overflow',L['DAMAGE_DEFINITION_BASE']+1,257),('enemy-attack-route-overflow',L['DAMAGE_DEFINITION_BASE'],10),('enemy-attack-without-landings',L['LANDING_META_BASE'],0),('enemy-attack-with-bullet-duration',L['BULLET_DEFINITION_BASE'],1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 w=list(programs[14][0]);w[L['CONDITION_BASE']+3]=0x7ff80000;bad.append(('enemy-attack-nan-hp-condition',w))
 w=list(programs[14][0]);w[L['CONDITION_BASE']+1]=1;bad.append(('enemy-attack-hp-condition-reserved-name',w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
