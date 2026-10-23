// Shared scalar state operations. The battle adapter owns carrier allocation,
// retirement, ATK snapshots, packet timing and the notification continuation.
// Uses the existing24-word protection-object representation, no Runtime arrays.
static const uint DA_WORDS=24,DA_NONE=0xffffffffU;
static const uint DA_DEALT=13,DA_ARCHIVE=14,DA_RATE=15,DA_RECEIVED=16;
static const uint DA_ACTIVE=512U,DA_RESERVED=65536U,DA_DONE=262144U;
uint64_t daNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
void daStore(uint at,uint64_t value) { results[at]=uint(value);results[at+1]=uint(value>>32); }
uint daAt(uint base,uint object) { return base+object*DA_WORDS; }
bool daPool(uint flags) { return (flags&255U)==DA_DEALT || (flags&255U)==DA_RECEIVED; }
// Two explicit caller-owned header words hold head/tail links. They need not
// precede the arena (the production shield-selection area must stay separate).
// Records7/8 are next/previous object+1. Archive objects never join this list.
// Stable insertion moves sorting to mutation; collection/rate lookup then walk
// native active order directly, without repeated capacity-wide selection scans.
void daUnlink(uint base,uint header,uint object)
{
    uint at=daAt(base,object);if((results[at+22]&DA_ACTIVE)==0) return;
    uint next=results[at+7],previous=results[at+8];
    if(previous==0) results[header]=next;else results[daAt(base,previous-1)+7]=next;
    if(next==0) results[header+1]=previous;else results[daAt(base,next-1)+8]=previous;
    results[at+7]=0;results[at+8]=0;
}
void daLink(uint base,uint header,uint capacity,uint object)
{
    uint at=daAt(base,object),order=results[at+20],next=results[header],previous=0;
    for(uint pass=0;pass<capacity && next!=0;pass++)
    { if(results[daAt(base,next-1)+20]>order) break;previous=next;next=results[daAt(base,next-1)+7]; }
    results[at+7]=next;results[at+8]=previous;
    if(previous==0) results[header]=object+1;else results[daAt(base,previous-1)+7]=object+1;
    if(next==0) results[header+1]=object+1;else results[daAt(base,next-1)+8]=object+1;
}
uint daFree(uint base,uint capacity)
{
    for(uint i=0;i<capacity;i++) if(results[daAt(base,i)+22]==0) return i;
    return DA_NONE;
}
uint daArchive(uint base,uint capacity,uint name,bool create,out uint status)
{
    status=0;
    for(uint i=0;i<capacity;i++) { uint at=daAt(base,i);if((results[at+22]&255U)==DA_ARCHIVE && results[at+4]==name) return i; }
    if(!create) return DA_NONE;
    uint object=daFree(base,capacity);if(object==DA_NONE) { status=64;return object; }
    uint at=daAt(base,object);for(uint w=0;w<DA_WORDS;w++) results[at+w]=0;
    results[at+4]=name;results[at+22]=DA_ARCHIVE|DA_RESERVED;return object;
}
void daRemember(uint base,uint capacity,uint name,uint64_t value,out uint status)
{
    uint object=daArchive(base,capacity,name,true,status);if(status==0) daStore(daAt(base,object),value);
}
// A name of DA_NONE represents an absent/empty authored pool name.
void daInitializePool(uint base,uint capacity,uint header,uint object,uint name,uint owner,uint stat,uint order,uint slot,uint64_t cap,out uint status)
{
    status=0;
    if(object>=capacity || owner>=5 || (stat!=81 && stat!=82) || order==0 || !f64Finite(cap)) { status=64;return; }
    uint at=daAt(base,object);daUnlink(base,header,object);for(uint w=0;w<DA_WORDS;w++) results[at+w]=0;
    daStore(at+2,cap);results[at+4]=name;results[at+20]=order;results[at+21]=slot;
    results[at+22]=(stat==81 ? DA_DEALT : DA_RECEIVED)|DA_ACTIVE|DA_RESERVED|(owner<<10);
    daLink(base,header,capacity,object);
    if(name!=DA_NONE) daRemember(base,capacity,name,0,status);
}
// The adapter refreshes query-time caster HP; it is not an activation snapshot.
void daUpdateOwnerHP(uint base,uint capacity,uint owner,uint64_t hp,out uint status)
{
    status=0;if(owner>=5 || !f64Finite(hp)) { status=64;return; }
    for(uint i=0;i<capacity;i++)
    { uint at=daAt(base,i),flags=results[at+22];if((flags&255U)==DA_RATE && ((flags>>10)&7U)==owner) daStore(at+2,hp); }
}
void daInitializeRate(uint base,uint capacity,uint header,uint object,uint name,uint owner,uint order,uint policy,uint64_t value,uint stack,uint64_t hp,out uint status)
{
    status=0;if(object>=capacity || owner>=5 || order==0 || policy>15) { status=64;return; }
    if(!f64Finite(value) || !f64Finite(hp)) { status=16;return; }
    uint at=daAt(base,object);daUnlink(base,header,object);for(uint w=0;w<DA_WORDS;w++) results[at+w]=0;
    daStore(at,value);results[at+4]=name;results[at+5]=policy;results[at+20]=order;results[at+21]=stack;
    results[at+22]=DA_RATE|DA_ACTIVE|DA_RESERVED|(owner<<10);
    daLink(base,header,capacity,object);daUpdateOwnerHP(base,capacity,owner,hp,status);
}
// Removed carriers do not destroy the name-global fallback ledger.
void daRetire(uint base,uint header,uint object) { daUnlink(base,header,object);results[daAt(base,object)+22]=0; }
uint64_t daRate(uint base,uint capacity,uint header,uint pool,out uint status)
{
    status=0;uint p=daAt(base,pool),owner=(results[p+22]>>10)&7U,name=results[p+4];
    uint64_t baseline=0,add=0;bool present=false;uint next=results[header];
    for(uint pass=0;pass<capacity && next!=0;pass++)
    {
        uint at=daAt(base,next-1),flags=results[at+22];next=results[at+7];
        if((flags&255U)!=DA_RATE || ((flags>>10)&7U)!=owner) continue;
        uint policy=results[at+5];
        if((policy&1U)==0) continue;uint64_t value=daNumber(at);
        if((policy&4U)!=0)
        {
            uint64_t lost=f64Add(f64FromI64(100),daNumber(at+2)^F64_SIGN);
            value=f64Mul(value,f64Less(lost,0) ? uint64_t(0) : lost);
        }
        else if((policy&8U)!=0) value=f64Mul(value,f64FromI64(results[at+21]));
        if(!f64Finite(value)) { status=16;return 0; }
        if((policy&2U)==0) { baseline=f64Add(f64Zero(baseline) ? uint64_t(0) : baseline,value);present=true; }
        else if(results[at+4]==name) add=f64Add(add,value);
    }
    uint64_t rate=f64Add(present ? baseline : f64FromI64(100),add);
    if(!f64Finite(rate)) status=16;return rate;
}
// Queue is caller-owned, so nested notification dispatch cannot overwrite an
// ancestor's captured notices. All pool updates precede the first callback.
uint daCollect(uint base,uint capacity,uint header,uint owner,uint64_t damage,uint queue,uint queueCapacity,out uint status)
{
    status=0;uint count=0;if(!f64Finite(damage)) { status=16;return 0; }
    if(!f64Less(0,damage)) return 0;
    for(uint group=0;group<2;group++)
    {
        uint next=results[header],kind=group==0 ? DA_DEALT : DA_RECEIVED;
        for(uint pass=0;pass<capacity && next!=0;pass++)
        {
            uint chosen=next-1,at=daAt(base,chosen),flags=results[at+22];next=results[at+7];
            if((flags&255U)!=kind) continue;uint caster=(flags>>10)&7U;
            uint64_t cap=daNumber(at+2);if((flags&DA_DONE)!=0 || !f64Less(0,cap) || kind==DA_DEALT && caster!=owner) continue;
            uint64_t rate=daRate(base,capacity,header,chosen,status);if(status!=0) return count;
            uint64_t current=f64Add(daNumber(at),f64Div(f64Mul(damage,rate),f64FromI64(100)));
            if(f64Less(cap,current)) current=cap;
            if(!f64Finite(current)) { status=16;return count; }daStore(at,current);
            uint name=results[at+4];if(name!=DA_NONE) { daRemember(base,capacity,name,current,status);if(status!=0) return count; }
            uint64_t epsilon=(uint64_t(0x3e112e0bU)<<32)|uint64_t(0xe826d695U); // exact binary64 1e-9
            if(!f64Less(current,f64Add(cap,epsilon^F64_SIGN)))
            {
                results[at+22]|=DA_DONE;
                if(name!=DA_NONE)
                {
                    if(count>=queueCapacity) { status=64;return count; }
                    results[queue+count*2]=name;results[queue+count*2+1]=caster;count++;
                }
            }
        }
    }
    return count;
}
uint64_t daTake(uint base,uint capacity,uint header,uint name,out uint status)
{
    status=0;uint chosen=DA_NONE,next=results[header];uint64_t value=0;
    for(uint pass=0;pass<capacity && next!=0;pass++)
    {
        uint object=next-1,at=daAt(base,object),flags=results[at+22];next=results[at+7];
        if(daPool(flags) && results[at+4]==name) { chosen=object;break; }
    }
    if(chosen!=DA_NONE)
    { uint at=daAt(base,chosen);value=daNumber(at);daStore(at,0);results[at+22]|=DA_DONE; }
    else { uint object=daArchive(base,capacity,name,false,status);if(object!=DA_NONE) value=daNumber(daAt(base,object)); }
    daRemember(base,capacity,name,0,status);return value;
}
uint64_t daEmission(uint64_t amount,uint64_t split,out bool emit,out uint status)
{
    emit=false;status=0;if(!f64Finite(amount) || !f64Finite(split)) { status=16;return 0; }
    if(!f64Less(0,amount)) return 0;emit=true;
    uint64_t value=f64Mul(amount,f64Add(f64FromI64(1),f64Div(split,f64FromI64(100))));
    uint conversion;uint64_t integer=f64ToI64(value,1,conversion);
    if(conversion!=0) { status=16;return 0; }return integer;
}
