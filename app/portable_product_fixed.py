"""Literal fixed readiness header shared by product executor compositions."""
import copy
import math
import struct
from portable_runtime import UnsupportedPortable


def lower(prepared):
    mode=prepared['policies']['config'].get('burst_gauge_mode','fixed')
    if mode not in ('fixed','accumulate'):raise UnsupportedPortable('Unported burst gauge mode')
    if mode!='fixed':return prepared,None
    if any(a.get('action')=='cover' for c in prepared['chars'] for a in c.get('control',{}).get('sequence',[])):
        raise UnsupportedPortable('Fixed burst with manual cover needs a combined literal control header')
    first=prepared['policies']['config'].get('first_burst_time',3.)
    regen=[c.get('burst_regen_time',2.) for c in prepared['chars']]
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=180 for v in [first,*regen]):
        raise UnsupportedPortable('Fixed burst delays require finite binary64 seconds in [0,180]')
    lowered=copy.deepcopy(prepared)
    lowered['policies']['config']['burst_gauge_mode']='accumulate'
    return lowered,(first,regen)


def attach(words,metadata,original,values):
    if values is None:return
    from portable_specs import LIMITS
    first,regen=values;base=LIMITS['WORLD_CONTROL_INPUT_BASE']
    version=words[base+1];tap_mask=words[base+5] if version==2 else 0
    if version==3:
        # Coordinate automatic/tap controls without a cover event use the same
        # fixed readiness and tap consumer. No manual state can be discarded.
        if (not 0<=words[base+5]<32 or words[base+6]!=0xffffffff
                or words[base+7]!=0x4d435631 or any(words[base+8:base+16])):
            raise UnsupportedPortable('Fixed coordinate burst requires automatic/tap controls without a cover event')
        tap_mask=words[base+5];version=2 if tap_mask else 1
        words[base+1]=version;words[base+5:base+16]=[tap_mask]+[0]*10
    if (version not in (1,2) or version==1 and any(words[base+5:base+16])
            or version==2 and (not 0<tap_mask<32 or any(words[base+6:base+16]))):
        raise UnsupportedPortable('Fixed burst requires a canonical automatic or tap control header')
    words[base+1]=5 if tap_mask else 4
    if tap_mask:words[base+10]=tap_mask
    words[base+5:base+10]=[0x46424731,*struct.unpack('<II',struct.pack('<d',first)),*struct.unpack('<II',struct.pack('<d',max(regen)))]
    metadata['real_prepared_input']['policy']=copy.deepcopy(original['policies'])
    metadata['product_fixed_burst']=dict(first_seconds=first,member_regen_seconds=regen,
        readiness_regen_seconds=max(regen),CPU_state_or_schedule_as_input=False)
