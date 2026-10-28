"""Independent original percentage/flat handlers versus shared GPU arithmetic."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator import timeline
from portable_ammo_numeric_cases import fixtures
spec=importlib.util.spec_from_file_location('ammo_numeric_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/ammo_instant_numeric_probe.slang';STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=16,OUTPUT=8)


def native_reference(domain):
    c=domain[0];handlers={}
    class Manager:
        def register_instant_handler(self,name,fn):handlers[name]=fn
        def _resolve_target(self,target,caster):return ['resource']
        def notify(self,*args,**kw):pass
    state=SimpleNamespace(ammo=c['current'],_full_ammo=lambda bm,t:c['capacity'],_sim_log=None,reload_cancel_on_full=False,reloading_until=-1.)
    timeline._register_instant_handlers(Manager(),{'resource':state},None)
    try:handlers['ammo_charge_pct' if c['kind']==13 else 'ammo_charge_flat']({},'resource',0.,c['value'])
    except OverflowError:return dict(status=16,result=None)
    result=state.ammo
    return dict(status=0,result=result) if -2147483648<=result<=2147483647 else dict(status=16,result=None)


def prepare():
    rows=[]
    for c in fixtures():
        words=[0x414e5531,1,c['kind'],c['capacity'],c['current']&0xffffffff,0,*struct.unpack('<II',struct.pack('<d',c['value'])),*([0]*8)]
        rows.append((c['name'],words,(c,)))
    seed=rows[0][1]
    for name,at,value in [('magic',0,0),('version',1,2),('kind',2,12),('capacity',3,0),('current',4,2147483647),('reserved',5,1),('nonfinite',7,0x7ff00000),('tail',15,1)]:
        words=list(seed);words[at]=value;rows.append(('reject/ammo-numeric/'+name,words,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def compare(block,domain):
    n=native_reference(domain)
    expected=[0,0x414e5531,n['result']&0xffffffff,0,0,0,0,0] if n['status']==0 else [16,0,0,0,0,0,0,0]
    assert list(block)==expected,dict(case=domain[0]['name'],actual=list(block),expected=expected)
    return n


def validate_rejection(block,name):assert name.startswith('reject/ammo-numeric/') and list(block)==[64,0,0,0,0,0,0,0]
