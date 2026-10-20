"""Authored graph descriptors for the shared world scheduler component.

No battle is run here. Normal roster admission remains closed until world
payloads, actor lifecycles and the common frame executor are connected.
"""
import copy,math,struct
INPUT_WORDS=2320
OUTPUT_WORDS=65536
NODE_BASE=16
FRAME_BASE=2064
OUTCOMES={None:0,'cleared':1,'expired':2,'followed':3,'end':4}

def number(value):return list(struct.unpack('<II',struct.pack('<d',float(value))))

def compile_schedule(case):
 from calculator.boss_pattern import validate
 patterns=validate(copy.deepcopy(case['patterns']),squad_size=5)
 if not 1<=len(patterns)<=32:raise ValueError('World graph component supports1..32 nodes')
 names={p.id:i for i,p in enumerate(patterns)};names['start']=32
 words=[0]*INPUT_WORDS;mode=case.get('clock','manual')
 if mode not in ('manual','accumulated','rational'):raise ValueError('Unknown world clock')
 frames=case.get('frames',[]);finish=case.get('finish',True)
 if type(finish) is not bool or not isinstance(frames,list) or len(frames)>64 or mode!='manual' and frames:raise ValueError('Invalid world component frame policy')
 through=case.get('duration',frames[-1][0] if frames else 0)
 if type(through) not in (int,float) or not math.isfinite(through) or through<0 or mode!='manual' and through>180:raise ValueError('Invalid world duration')
 words[:8]=[0x57533031,len(patterns),len(frames),('manual','accumulated','rational').index(mode),int(finish),0,*number(through)]
 for p in patterns:
  if len(p.after)>8 or len(p.until_after)>8 or p.repeat>0x7fffffff:raise ValueError('World graph descriptor capacity exceeded')
  if p.summon is not None and p.summon.attack is not None:raise ValueError('Summon attack lifecycle is not connected to this scheduler component')
  hits=p.shots.hits if p.shots else 0;interval=p.shots.interval if p.shots else 0
  if hits>0x7fffffff:raise ValueError('World shot count exceeds exact integer descriptor range')
  at=NODE_BASE+p.idx*64
  words[at:at+12]=[p.repeat,int(p.until_time is not None)|int(p.until_cleared)<<1,*number(p.delay),*number(p.until_time or 0),hits,0,*number(interval),len(p.after),len(p.until_after)]
  for i,(node,outcome) in enumerate(p.after):words[at+16+i*2:at+18+i*2]=[names[node],OUTCOMES[outcome]]
  for i,(node,delay) in enumerate(p.until_after):words[at+32+i*3:at+35+i*3]=[names[node],*number(delay)]
 previous=0
 for i,frame in enumerate(frames):
  if not isinstance(frame,(list,tuple)) or len(frame)!=2:raise ValueError('World frame requires authored time and cleared-mask stimulus')
  time,mask=frame
  if type(time) not in (int,float) or not math.isfinite(time) or not previous<=time<=through or type(mask) is not int or not 0<=mask<1<<len(patterns):raise ValueError('Invalid world frame')
  if any(mask&(1<<p.idx) and not p.until_cleared for p in patterns):raise ValueError('Cleared stimulus needs an authored targets-cleared rule')
  words[FRAME_BASE+i*4:FRAME_BASE+i*4+4]=[*number(time),mask,0];previous=time
 return words,patterns
