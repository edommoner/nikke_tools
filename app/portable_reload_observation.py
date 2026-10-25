"""One reload wire reader for ordinary and coordinate shared GPU suites."""
import struct
from portable_specs import LIMITS as L

def readback(block,meta):
 h=L['WORLD_RELOAD_HEAD_BASE'];assert block[h]==0x57524c31 and block[h+1]<=L['WORLD_RELOAD_TRACE_COUNT'] and not any(block[h+2:h+4]) and not any(block[h+14:h+16])
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0];names={v:k for k,v in meta['states'].items()};events=[]
 for i in range(block[h+1]):
  at=L['WORLD_RELOAD_TRACE_BASE']+i*16;kind,who=block[at:at+2];assert kind<3 and who<5 and not any(block[at+12:at+16])
  if kind==0:
   assert not any(block[at+5:at+12]);events.append(dict(kind='force',owner=who,time=number(at+2),name=names[block[at+4]]))
  else:
   assert block[at+7]<3;ammo=block[at+6];events.append(dict(kind=('start','finish')[kind-1],owner=who,time=number(at+2),until=number(at+4),ammo=ammo if ammo<0x80000000 else ammo-0x100000000,phase=('ready','charging','post_delay')[block[at+7]],full_time=number(at+8),release_time=number(at+10)))
 return dict(reload_events=events,reload_until=[number(h+4+who*2) for who in range(5)])
