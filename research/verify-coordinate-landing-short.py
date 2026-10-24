"""Shared expected landing probe; strict full probability/cut output."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_numeric_v1 as n
import portable_coordinate_power_v1 as p
import portable_coordinate_quadrature_v1 as q
import portable_coordinate_landing_v1 as l
from portable_coordinate_landing_cases import fixtures
s=importlib.util.spec_from_file_location('landing_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_landing_probe.slang';INPUT_WORDS=l.INPUT;OUTPUT_WORDS=l.OUTPUT;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def words64(value):return [value&0xffffffff,value>>32]
def pack(case):
    w=[0]*l.INPUT;targets=case['targets'];w[:4]=[l.MAGIC,1,len(targets),int(case.get('core') is not None)]
    w[4:14]=[word for value in (*case['aim'],case['radius'],case['grow'],case['k']) for word in words64(n.bits(value))]
    for index,shape in [*enumerate(targets),*(([(l.TARGETS,case['core'])]) if case.get('core') is not None else [])]:
        at=l.HEADER+index*l.SHAPE_WORDS;w[at:at+14]=[shape[0],0]+[word for value in shape[1:] for word in words64(n.bits(value))]
    return w
def prepare():
    for module in (n,p,q,l):module.check_schema(ROOT)
    l.check_arc_references(ROOT)
    l.check_prepared_arcs(ROOT)
    rows=[('coordinate-landing/'+name,pack(case),case) for name,case in fixtures()]
    seed=next(w for name,w,d in rows if name=='coordinate-landing/center-target')
    for label,at,value in [('magic',0,0),('version',1,2),('count',2,128),('core-flag',3,2),('reserved',14,1),('nan-aim',5,0x7ff80000),('negative-grow',11,0xbff00000),('k-zero',13,0),('k-low',13,0x3eefffff),('k-high',13,0x41000000),('shape-kind',16,3),('shape-reserved',17,1),('shape-radius-zero',23,0),('unused-row',32,1)]:
        w=list(seed);w[at]=value
        if label=='k-zero':w[12]=0
        rows.append(('reject/coordinate-landing/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    from coordinate_landing_reference import landing
    return landing(domain)
def expected(domain):
    e=native_reference(domain);w=[0]*OUTPUT_WORDS;w[:4]=[0,l.MAGIC,1,len(domain['targets'])]
    w[4:6]=words64(n.bits(e['core_open']));w[6:8]=words64(n.bits(e['core_under']));w[8:13]=[len(e['cuts']),e['nodes'],e['near_count'],int(e['use_core']),e['fast_path']]
    for key,start in [('front',16),('reach',16+l.TARGETS*2)]:
        for i,value in enumerate(e[key]):w[start+i*2:start+i*2+2]=words64(n.bits(value))
    for i,value in enumerate(e['cuts']):w[l.CUT_OFFSET+i*2:l.CUT_OFFSET+i*2+2]=words64(n.bits(value))
    if e['fast_path']==0:
        from coordinate_landing_reference import prepared_cache
        from coordinate_geometry_reference import evaluate as geometry
        R=max(domain['radius'],1e-9)
        selected=[(i,shape) for i,shape in enumerate(domain['targets']) if geometry((*shape,*domain['aim'],0.,0.))['distance']<=R+domain['grow']]
        if e['use_core']:selected.append((l.TARGETS,domain['core']))
        for index,shape in selected:
            for lane,value in enumerate(prepared_cache(shape,domain['aim'])):
                at=l.PREP_OFFSET+index*l.PREP_WORDS+lane*2;w[at:at+2]=words64(n.bits(value))
    return w,e
def compare(block,domain):
    w,e=expected(domain);assert list(block)==w,('landing bits',next((i for i,(a,b) in enumerate(zip(block,w)) if a!=b),None));return e
def validate_rejection(block,name):assert name.startswith('reject/coordinate-landing/') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
