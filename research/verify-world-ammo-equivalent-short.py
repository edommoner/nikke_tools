"""Bounded ammo-equivalent admission and full-native battle comparison."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('ammo_equivalent_battle_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_ammo_equivalent_cases import fixtures as main_fixtures
from portable_ammo_equivalent_geometry_cases import fixtures as geometry_fixtures
from world_ammo_equivalent_native import observe
from portable_ammo_equivalent_contracts import verify
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import double_words

def fixtures():return main_fixtures()+geometry_fixtures()


def prepare():
    return prepare_cases(fixtures())

def prepare_cases(cases,*,reject=True):
    entries=[]
    for case in cases:
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];d=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];h=L['HEALTH_DEFINITION_BASE']+L['HEALTH_DEFINITION_WORDS'];q=L['DEFINITION_EXTRA_BASE']+L['DEFINITION_EXTRA_WORDS'];p=L['RECIPIENT_BASE']+8
    edits=[('no-combat',[(3,0)]),('stat',[(d+F['STAT'],38)]),('target',[(d+F['TARGET'],1)]),('mask',[(d+F['RECIPIENTS'],31)]),('owner',[(d+F['OWNER'],5)]),('enemy',[(h+3,1)]),('health',[(h,1)]),('allied',[(h+1,1)]),('damage-flags',[(d+F['DAMAGE_FLAGS'],1)]),('quantity',[(q+3,1)]),('flags',[(d+F['FLAGS'],128)]),('recipient',[(p,1)]),('query-resolve',[(p+7,seed[p+7]|4)])]
    for label,value in [('too-positive',4096.5),('too-negative',-4096.5),('nan',float('nan')),('infinite',float('inf'))]:
        edits.append((label,list(zip((d+F['VALUE'],d+F['VALUE']+1),struct.unpack('<II',struct.pack('<d',value))))))
    for label,changes in edits if reject else []:
        words=list(seed)
        for at,value in changes:words[at]=value
        entries.append(('reject/ammo-equivalent-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('ammo_equivalent')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/ammo-equivalent-') and block[0]==64
