"""Shared state-operation proof; not battle timing, ATK capture or GPU admission."""
import array,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_damage_accum_core_cases import fixtures,NONE
suite=types.SimpleNamespace(INPUT=512)
spec=importlib.util.spec_from_file_location('damage_core_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
def words(v):return list(struct.unpack('<II',struct.pack('<d',float(v))))
def bits(v):return struct.pack('<d',float(v)).hex()
def prepare():
    rows=[];packed=array.array('I',[len(fixtures())])
    for c in fixtures():
        w=[0]*512;w[:2]=[c['capacity'],len(c['ops'])]
        for i,(op,slot,policy,name,owner,value,stack,hp) in enumerate(c['ops']):
            at=2+i*20;w[at:at+11]=[op,slot,policy,name,owner,*words(value),stack,0,*words(hp)]
        rows.append((('reject/' if c['reject'] else '')+c['name'],w,None if c['reject'] else c));packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(c):
    import engine_worker
    from calculator.buff_manager import BuffManager,ActiveBuff
    manager=BuffManager([]);log=[];order=0;original=manager.notify;full=[]
    def named(n):return '' if n==NONE else 'n'+str(n)
    def notice(event,t,caster,*a,**kw):
        if event.startswith('event:accum_full:'):full.append([int(event.split(':')[-1][1:]),int(caster)])
        return original(event,t,caster,*a,**kw)
    manager.notify=notice
    for step,(op,slot,policy,name,owner,value,stack,hp) in enumerate(c['ops']):
        answer=dict(op=op);old=next((p for p in manager._active if p.effect['_slot']==slot),None)
        if op in (0,1):
            if old is not None:manager._active.remove(old)
            order+=1
            effect=dict(type='buff',stat={81:'dmg_accum_dealt_atk_pct',82:'dmg_accum_received_atk_pct'}.get(policy,'dmg_accum_rate_pct') if op==0 else 'dmg_accum_rate_pct',name=named(name) if op==0 else 'rate'+str(slot),_slot=slot,_order=order)
            if op==1:
                if policy&1:effect['fixed_value']=value
                if policy&2:effect['target_effect']=named(name)
                if policy&4:effect['scaling']='lost_hp_pct'
                if policy&8:effect['max_stack']=max(2,stack)
                manager.state.setdefault('hp_pct',{})[str(owner)]=hp
            ab=ActiveBuff(effect,str(owner),None,0.,100.,stack=stack,accum_cap=value if op==0 else 0.)
            manager._active.append(ab)
            if op==0 and name!=NONE:manager._accum_last[named(name)]=0.
            manager._stat_index.clear()
        elif op==2:
            full.clear();manager.accumulate_damage(str(slot),float(value),float(step));answer['full']=list(full)
            answer['done']=sum(1<<p.effect['_slot'] for p in manager._active if p.effect['stat'] in manager._ACCUM_STATS and p.accum_done)
        elif op==3:
            amount=manager.accum_discharge(named(name),float(step));answer.update(value=bits(amount),emit=amount>0,integer=int(amount*(1.+float(value)/100.)) if amount>0 else 0)
        elif op==4:
            assert old is not None;manager._active.remove(old);manager._stat_index.clear()
        elif op==5:
            assert old is not None;answer['value']=bits(manager._accum_rate(old))
        elif op==6:manager.state.setdefault('hp_pct',{})[str(slot)]=value
        else:raise AssertionError(op)
        log.append(answer)
    pools=[]
    for ab in manager._active:
        if ab.effect['stat'] not in manager._ACCUM_STATS:continue
        pools.append(dict(slot=ab.effect['_slot'],name=NONE if not ab.effect['name'] else int(ab.effect['name'][1:]),owner=int(ab.caster),cap=bits(ab.accum_cap),current=bits(ab.accum),done=ab.accum_done,order=ab.effect['_order']))
    return dict(scope='native_scalar_state_operations_only',operations=log,pools=sorted(pools,key=lambda p:p['order']),archive={k:bits(v) for k,v in sorted(manager._accum_last.items())})
def decode(block,c):
    assert block[0]==0,(c['name'],block[0]);assert block[1]==len(c['ops'])
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    bit=lambda at:struct.pack('<II',*block[at:at+2]).hex()
    log=[]
    for i,op in enumerate(c['ops']):
        at=1024+i*32;assert block[at]==op[0] and block[at+1]==0;answer=dict(op=op[0])
        if op[0]==2:answer.update(full=[list(block[at+6+j*2:at+8+j*2]) for j in range(block[at+5])],done=block[at+22])
        elif op[0]==3:answer.update(value=bit(at+2),emit=bool(block[at+4]),integer=struct.unpack('<q',struct.pack('<II',*block[at+24:at+26]))[0])
        elif op[0]==5:answer['value']=bit(at+2)
        log.append(answer)
    # Inspect the actual linked arena, including rates and reused slots.
    active=[i for i in range(c['capacity']) if block[16+i*24+22]&512]
    chain=[];link=block[8];previous=0
    while link:
        obj=link-1;assert obj in active and obj not in chain
        at=16+obj*24;assert block[at+8]==previous;chain.append(obj);previous=link;link=block[at+7]
    assert block[9]==previous and set(chain)==set(active)
    assert [block[16+i*24+20] for i in chain]==sorted(block[16+i*24+20] for i in active)
    pools=[];archive={}
    for i in range(c['capacity']):
        at=16+i*24;flags=block[at+22];kind=flags&255
        if kind in (13,16):pools.append(dict(slot=block[at+6],name=block[at+4],owner=(flags>>10)&7,cap=bit(at+2),current=bit(at),done=bool(flags&262144),order=block[at+20]))
        elif kind==14:archive['n'+str(block[at+4])]=bit(at)
    return dict(scope='native_scalar_state_operations_only',operations=log,pools=sorted(pools,key=lambda p:p['order']),archive=archive)
def compare(block,domain):
    expected=native_reference(domain);actual=decode(block,domain);assert actual==expected,(domain['name'],actual,expected);return expected
def validate_rejection(block,name):
    expected=16 if name.rsplit('/',1)[-1] in ('nan-credit','infinite-rate','emission-int64-overflow') else 64
    assert name.startswith('reject/damage-accum-core/') and block[0]==64 and block[2]==expected,(name,block[0],block[2])
