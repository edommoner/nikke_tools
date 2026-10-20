"""Typed landing stimuli and actual native pool/registry observations."""
import copy,struct
from types import SimpleNamespace
from calculator.boss_pattern import BossScript,BOSS_EVENTS,validate
from calculator.sim_result import HitEvent
from world_actor_runtime import registry_for
from impact_specs import ActorHandle
from world_actor_pool_native import summary,query_pool,bits,actor_bindings

def fixtures(base):
 rows=[]
 part=lambda **kw:dict(id='parts',kind='parts',targets=[dict(name='right',hp=3,score=7,emit_on_destroy=['event:part_destroy','event:target_spawn']),dict(name='left',hp=0)],**kw)
 wave=lambda **kw:dict(id='wave',kind='summon',spec=dict(count=3,hp=3),**kw)
 def add(name,patterns,actions,duration=.5):
  c=copy.deepcopy(base);c.update(name=name,patterns=patterns,actions=actions,duration=duration)
  for w in c['combat']['weapons']:w['enabled']=False
  rows.append(c)
 # action: time,op,args(5),amount. Advance24 precedes every action.
 land=lambda t,k,i,g,r,a:(t,34,[0,k,i,g,r],a)
 query=lambda t,k,i,g,q:(t,37,[k,i,g,q,0],0)
 capture=lambda t,m,s:(t,35,[m,s,0,0,0],0)
 landset=lambda t,s,r,a:(t,36,[0,s,r,0,0],a)
 add('part-overkill-death-notices-and-score',[part()], [land(0,1,0,1,0,10),land(0,1,0,1,1,10),query(.1,1,0,1,0),land(.1,1,1,1,2,1e16),land(.1,1,1,1,3,1),query(.1,1,1,1,1)])
 add('add-hp-clipped-and-dead-overkill',[wave()], [land(0,5,0,1,0,10),land(0,5,0,1,1,10),query(.1,5,0,1,0)])
 p=wave();p['spec']=dict(count=1,hit_hp=2)
 add('add-hit-hp-zero-amount',[p],[land(0,5,0,1,0,0),query(0,5,0,1,0),land(0,5,0,1,1,0),query(.1,5,0,1,1)])
 add('typed-set-body-parts-adds',[part(),wave()],[capture(0,35,0),landset(0,0,0,5),query(.1,1,0,1,0),query(.1,5,0,1,1)])
 p=wave(after=['start','wave'],repeat=0,until=dict(time=.1))
 add('frozen-set-rejects-reopened-generation',[p],[capture(0,32,0),landset(.25,0,0,5),query(.25,5,0,3,0),land(.25,5,0,1,1,5)])
 p=part(after=['start','parts'],repeat=0,until=dict(targets_cleared=True))
 add('part-cleared-reopens-unbreakable-excluded',[p],[land(0,1,0,1,0,10),query(.1,1,0,2,0),land(.1,1,0,1,1,10)])
 p=wave(until=dict(time=.1));add('expired-same-generation-overkill',[p],[capture(0,32,0),landset(.25,0,0,5),query(.25,5,0,1,0)])
 p=wave();p['spec']['count']=127
 add('128bit-set-captures-and-lands-all128',[p],[capture(0,33,0),landset(0,0,0,5),query(.1,5,126,1,0)])
 a=wave(delay=.2);a['id']='late';z=wave();z['id']='early'
 add('set-add-order-follows-birth-not-id',[a,z],[capture(.25,32,0),landset(.25,0,0,5)])
 add('query-unknown-notspawned-stale',[wave(delay=.2)],[query(0,5,0,1,0),query(.25,5,0,2,1),query(.25,5,99,1,2),query(.25,0,0,1,3)])
 return rows

def native(case,L):
 enemy={'def':0,'core_px':0};patterns=validate(copy.deepcopy(case['patterns']),squad_size=5);notices=[0]*4;deaths=0
 class Boss(BossScript):
  def _destroy(self,*args,**kwargs):
   nonlocal deaths
   deaths+=1;return super()._destroy(*args,**kwargs)
  def _retire(self,run,add,why,*args,**kwargs):
   nonlocal deaths
   deaths+=int(why!='퇴장');return super()._retire(run,add,why,*args,**kwargs)
 boss=Boss(patterns,enemy,lambda *_:False);reg=registry_for(SimpleNamespace(),boss);bindings=actor_bindings(boss);time=0.;body_hits=[];queries={};receipts={};sets={};owned=set()
 def advance(through):
  nonlocal time
  while time<=through:
   for e in boss._carry:notices[BOSS_EVENTS.index(e)]+=1
   boss.begin_frame(time,enemy);time+=1/60
 def land(kind,id,gen,amount,t):
  try:snap=reg.exact(ActorHandle(kind,id,gen))
  except ValueError as e:return (3 if 'Stale' in str(e) else 2 if 'not spawned' in str(e) else 1),0,0,0.,0.
  b=next(b for b in bindings if int(b.kind)==kind and b.identity==id);ev=HitEvent(t,'pool-test',amount,False,'normal');before=deaths;over=boss.add_overkill;took=amount;accepted=1
  if kind==0:body_hits.append(ev)
  elif kind==1:
   ev.target=b.label;boss.hit_target(ev,t);accepted=int(snap.alive);took=amount if accepted else 0.
  else:
   record=[];boss._typed_add_callback=lambda ev,label,generation,amount,killed,t:record.append(amount)
   accepted=int(boss.hit_add(ev,b.label,t));took=record[0] if record else 0.
  return 0,accepted,deaths-before,took,boss.add_overkill-over
 for t,op,args,amount in case['actions']:
  advance(t)
  if op==34:
   who,k,id,gen,index=args;status,accepted,killed,took,over=land(k,id,gen,amount,t);receipts[index]=[status,1,accepted,killed,*bits(took),*bits(over)]
  elif op==37:
   k,id,gen,index,_=args;queries[index]=query_pool(reg,boss,k,id,gen,body_hits)
  elif op==35:
   mask,index,*_=args;live=[]
   for slot,b in enumerate(bindings):
    if not(mask&(1<<int(b.kind))):continue
    try:snap=reg.view(b.kind,b.label)
    except ValueError:continue
    if snap.alive:live.append((slot,snap,b))
   live.sort(key=lambda x:(int(x[2].kind),boss._runs[x[2].run].adds[x[2].slot].order if int(x[2].kind)==5 else x[2].identity))
   row=[0]*L['WORLD_ACTOR_SET_WORDS'];row[0]=len(live);row[5]=1
   for i,(slot,snap,b) in enumerate(live):row[1+slot//32]|=1<<(slot%32);row[8+i*4:12+i*4]=[slot,snap.handle.generation,int(b.kind),b.identity]
   sets[index]=row;owned.add(index)
  elif op==36:
   who,index,out,*_=args;row=sets[index];accepted=killed=0;took=over=0.
   for i in range(row[0]):
    slot,gen,k,id=row[8+i*4:12+i*4];status,a,d,tkn,ov=land(k,id,gen,amount,t)
    if status:continue
    accepted+=a;killed+=d;took+=tkn;over+=ov
   receipts[out]=[0,row[0],accepted,killed,*bits(took),*bits(over)];row[5]=0;owned.remove(index)
  elif op==38:sets[args[0]][5]=0;owned.remove(args[0])
 advance(case['duration']);boss.finish(case['duration'])
 return dict(actor_pools=summary(boss,body_hits,notices,deaths),queries=queries,receipts=receipts,sets=sets,owned=len(owned))

def decoded(block,case,L,bindings):
 from world_actor_pool_native import bits
 h=L['WORLD_ACTOR_POOL_OUTPUT_BASE'];p=L['WORLD_ACTOR_POOL_STATE_BASE'];num=lambda a:struct.unpack('<d',struct.pack('<II',*block[a:a+2]))[0]
 queries={a[1][3]:list(block[L['WORLD_ACTOR_POOL_QUERY_BASE']+a[1][3]*16:L['WORLD_ACTOR_POOL_QUERY_BASE']+(a[1][3]+1)*16]) for a in [(op,args) for _,op,args,_ in case['actions']] if a[0]==37}
 receipts={args[4] if op==34 else args[2]:None for _,op,args,_ in case['actions'] if op in (34,36)}
 for i in receipts:at=L['WORLD_ACTOR_RECEIPT_BASE']+i*8;receipts[i]=list(block[at:at+8])
 sets={args[1]:list(block[L['WORLD_ACTOR_SET_BASE']+args[1]*L['WORLD_ACTOR_SET_WORDS']:L['WORLD_ACTOR_SET_BASE']+(args[1]+1)*L['WORLD_ACTOR_SET_WORDS']]) for _,op,args,_ in case['actions'] if op==35}
 return dict(actor_pools=dict(pools=[list(block[p+i*16:p+(i+1)*16]) for i in range(len(bindings))],score=block[h+8]+(block[h+9]<<32),spawned=block[h+4],overkill=num(h+16),notice_counts=list(block[h+10:h+14]),pending_notices=block[h+5],deaths=block[h+14]),queries=queries,receipts=receipts,sets=sets,owned=block[h+7])
