"""Independent host binary64 ordered products for the shared factor kernel."""
import array,importlib.util,math,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('factor_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=18,OUTPUT=786432)
# Slots0..6 are the original seven factors;7/8 replace critical/part factors.
# Distinct values at every position catch ordering and mistaken substitutions.
CASES=[
 ('identity',[100.,1.,1.,1.,1.,1.,1.,1.,1.]),
 ('core-and-part',[100.,1000.,2.5,1.,1.,1.,1.,1.5,3.]),
 ('part-replaces-main',[150.,101.,1.8,2.,7.,1.3,1.1,1.2,4.]),
 ('ordered-decimals',[190.8,23.9,278.6,293.6,288.2,200.5,174.7,218.3,11.1]),
 ('no-core',[99.9,777.,1.25,1.,1.,1.,1.,1.25,1.]),
 ('zero-main-core',[100.,100.,0.,1.,1.,1.,1.,1.,2.]),
 ('zero-main-additive',[100.,100.,1.,1.,0.,1.,1.,1.,2.]),
 ('zero-part-core',[100.,100.,2.,1.,1.,1.,1.,0.,2.]),
 ('zero-part-additive',[100.,100.,2.,1.,1.,1.,1.,1.,0.]),
 ('minimum-subnormal',[100.,math.ulp(0.),1.,1.,1.,1.,1.,1.,2.]),
 ('gradual-underflow',[100.,sys.float_info.min,.5,.5,1.,1.,1.,1.,2.]),
 ('integer-tie',[100.,1.,2.5,1.,1.,1.,1.,1.5,1.]),
 ('integer-boundary',[100.,2.**52,math.nextafter(1.,2.),1.,1.,1.,1.,1.,1.]),
 ('large-finite',[100.,2.**500,1.7,2.,3.,.5,1.1,1.1,2.]),
 ('tiny-coefficient',[math.ulp(0.),1.,1.,1.,1.,1.,1.,1.,2.]),
 ('negative-additive',[100.,123.,1.3,1.,-2.,1.,1.,1.1,-3.]),
]
def bits(value):return list(struct.unpack('<II',struct.pack('<d',value)))
def native_reference(domain):
    _,f=domain;values=[0]
    for part in (False,True):
        value=(f[0]/100.)*f[1]
        for factor in (f[7] if part else f[2],f[3],f[8] if part else f[4],f[5],f[6]):value*=factor
        values.extend(bits(value))
    return values
def prepare():
    entries=[];packed=array.array('I',[len(CASES)])
    for domain in CASES:
        words=[word for value in domain[1] for word in bits(value)]
        entries.append(('damage-factors-'+domain[0],words,domain));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):
    expected=native_reference(domain)
    if list(block[:5])!=expected or any(block[5:]):raise AssertionError((domain[0],list(block[:5]),expected))
    return expected
