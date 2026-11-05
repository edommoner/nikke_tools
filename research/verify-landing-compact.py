"""Shared codec boundaries and full wide/compact representation equivalence.
No timing claim; the wide control uses identical physics and current ABI.
"""
import array,copy,hashlib,importlib.util,json,random,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime
from portable_backend import execute
from portable_specs import LIMITS as L

def codec_boundaries(backend):
 rng=random.Random(941)
 rows=[[0,0,0,0,0,0,0,0,1,1,1,0],[255,7,255,0x87654321,0xffffffff,0x7fefffff,1,0x80000000,256,256,32,0x7fffffff],[255,7,0xffffffff,0x12345678,1,0,0,0x3ff00000,1,256,32,0x7fffffff]]
 for _ in range(256):
  hits=rng.randint(1,256)
  rows.append([rng.randrange(256),rng.randrange(8),rng.choice([0xffffffff,rng.randrange(256)]),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.randint(1,hits),hits,rng.randint(1,32),rng.randrange(0x80000000)])
 good=len(rows)
 for offset,value in ((0,256),(1,8),(2,256),(2,0xfffffffe),(8,0),(8,257),(9,0),(9,257),(10,0),(10,33),(11,0x80000000)):
  row=rows[0].copy();row[offset]=value;rows.append(row)
 words=[len(rows)]+sum(rows,[]);packed=struct.pack('<'+'I'*len(words),*words)
 raw,evidence=execute('gpu/landing_codec_probe.slang','landingCodecProbe',packed,12,21,backend)
 out=struct.unpack('<'+'I'*(len(raw)//4),raw)
 for i,row in enumerate(rows):
  actual=out[i*21:(i+1)*21];assert actual[20]==int(i<good),(i,actual)
  if i<good:
   assert list(actual[8:20])==row,(i,row,actual)
   mask=256 if row[2]==0xffffffff else row[2]
   assert list(actual[:8])==[row[0]|row[1]<<8|mask<<11,row[3],*row[4:8],row[8]|row[9]<<9|row[10]<<18,row[11]]
 return dict(passed=True,valid_vectors=good,invalid_vectors=len(rows)-good,arbitrary_binary64_bits_preserved=True,**evidence)

def canonicalize(raw,count):
 wide=array.array('I');wide.frombytes(raw)
 if sys.byteorder!='little':wide.byteswap()
 compact=array.array('I',[0])*(count*L['OUTPUT_WORDS']);start=L['LANDING_STATE_BASE']
 for i in range(count):
  a=i*98304;b=i*L['OUTPUT_WORDS'];compact[b:b+start]=wide[a:a+start]
  for j in range(L['LANDINGS']):
   at=a+start+j*12;dst=b+start+j*8;r=wide[at:at+12];mask=256 if r[2]==0xffffffff else r[2]
   compact[dst:dst+8]=array.array('I',[r[0]|r[1]<<8|mask<<11,r[3],*r[4:8],r[8]|r[9]<<9|r[10]<<18,r[11]])
  wide_queue=a+start+L['LANDINGS']*12;dst=b+L['REMOVAL_QUEUE_BASE'];size=L['REMOVALS']//2
  compact[dst:dst+size]=wide[wide_queue:wide_queue+size]
  assert not any(wide[wide_queue+size:a+98304])
 if sys.byteorder!='little':compact.byteswap()
 return compact.tobytes()
