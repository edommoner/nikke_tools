"""NRB1 literal effect bindings; no battle values, HP or selected actors."""
import copy,struct
from pathlib import Path
from named_range_battle import normalize
from effect_range_policy import validate_effect as validate_range
from effect_target_count_policy import validate_effect as validate_count
from portable_specs import LIMITS as L,FIELDS as F
from portable_coordinate_matrix_specs import coefficients
from types import SimpleNamespace
SOURCE='gpu/world_named_range_battle_entry.slang'
BASE=115680;HEADER=32;ROWS=16;ROW_WORDS=32;WORDS=HEADER+ROWS*ROW_WORDS;INPUT=BASE+WORDS
OUTPUT=2032000;OUT=1867648;OUT_HEADER=16;CASTS=512;CAST_WORDS=32;END=OUT+OUT_HEADER+CASTS*CAST_WORDS
MAGIC=0x4e524231;RANGE_STAT=94;COUNT_STAT=93

def bits(x):return list(struct.unpack('<II',struct.pack('<d',float(x))))
def shader_schema():
    return '// Generated from portable_named_range_battle_wire; literal inputs only.\n'+''.join('static const uint NRB_'+k+'='+str(v)+'U;\n' for k,v in dict(BASE=BASE,HEADER=HEADER,ROWS=ROWS,ROW_WORDS=ROW_WORDS,WORDS=WORDS,INPUT=INPUT,OUTPUT=OUTPUT,OUT=OUT,OUT_HEADER=OUT_HEADER,CASTS=CASTS,CAST_WORDS=CAST_WORDS,END=END,MAGIC=MAGIC,RANGE_STAT=RANGE_STAT).items())
def check_schema(root=None):
    path=Path(root or Path(__file__).resolve().parents[1])/'gpu/named_range_battle_layout.slang'
    if path.read_text()!=shader_schema():raise ValueError('Named range battle schema drift')

def compile_battle(prepared,geometry,rules):
    from portable_logical_geometry_wire import compile_logical_geometry
    normalized,_=normalize(rules,geometry);source=copy.deepcopy(prepared);lowered=copy.deepcopy(prepared);domains={}
    for i,item in enumerate(source['effects']):
        e=item['effect']
        if validate_range(e):domains[i]=RANGE_STAT
        elif validate_count(e,allow_marked_allies=True):domains[i]=COUNT_STAT
        if i in domains:lowered['effects'][i]['effect']['stat']=''
    if not domains or RANGE_STAT not in domains.values():raise ValueError('Original named range definitions required')
    w,m,bindings,scene=compile_logical_geometry(lowered,geometry)
    if len(w)!=BASE or prepared!=source:raise ValueError('Named range prefix identity changed')
    def symbol(name):
        if name not in m['states']:
            if len(m['states'])>=256:raise ValueError('Named range symbol capacity')
            m['states'][name]=len(m['states'])
        return m['states'][name]
    for original,stat in domains.items():
        row=m['binding_source_indices'].index(original);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];e=source['effects'][original]['effect']
        w[at+F['KIND']]=0;w[at+F['STAT']]=stat;w[at+F['TARGET_NAME']]=symbol(e['target_effect'])
    tail=[0]*WORDS;tail[:4]=[MAGIC,1,len(normalized),len(bindings)];bound=[]
    for index,rule in enumerate(normalized):
        found=[i for i,item in enumerate(source['effects']) if item['owner']==rule['owner'] and item['effect'].get('name')==rule['effect']]
        if len(found)!=1:raise ValueError('Exact original owner/effect binding required')
        original=found[0];e=source['effects'][original]['effect']
        if e.get('type')!='damage' or e.get('stat')!='damage' or e.get('target')!='enemies_nearest:'+str(rule['base_count']) or e.get('tick_interval') or e.get('hits_parts'):raise ValueError('Plain original nearest damage binding required')
        row=m['binding_source_indices'].index(original);shape=rule['body_shape'];kind=1 if shape['r']>0 else 2;co,si=coefficients(SimpleNamespace(rot=shape['rot'],is_circle=kind==1))
        at=HEADER+index*ROW_WORDS;tail[at:at+6]=[row+1,rule['base_count'],*bits(rule['base_radius']),kind,0]
        for j,v in enumerate([shape[k] for k in ('x','y','r','w','h','rot')]+[co,si]):tail[at+6+j*2:at+8+j*2]=bits(v)
        bound.append(dict(row=row,source_row=original,owner=rule['owner'],effect=rule['effect']))
    m['named_range_battle']=dict(model='named-radial-frozen-logical-battle-v1',rules=copy.deepcopy(normalized),bindings=bound,domains=domains,input_words=INPUT,gpu_admitted=False)
    return w+tail,m,bindings,scene
