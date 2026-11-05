// Typed storage only: caller owns hit construction, factors, world clocks and
// notification dispatch. The record preserves immutable identity and tombstone
// generation. All scalar math is existing software binary64 on both backends.
static const uint DT_WORDS=14U,DT_NONE=0xffffffffU;
uint64_t dtNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
void dtStore(uint at,uint64_t value) { results[at]=uint(value);results[at+1]=uint(value>>32); }
bool dtQuantity(uint64_t x) { return f64Finite(x) && !f64Less(x,0) && !f64Less((uint64_t(0x46293e59U)<<32)|uint64_t(0x39a08ceaU),x); }
bool dtKind(uint kind) { return kind>=2 && kind<=4; }
uint dtAt(uint base,uint slot) { return base+slot*DT_WORDS; }
void dtAdvance(uint base,uint capacity,uint64_t when,uint64_t previous,out uint status)
{
    status=0;if(!f64Finite(when)||f64Less(when,previous)) { status=64;return; }
    for(uint i=0;i<capacity;i++)
    { uint at=dtAt(base,i);uint64_t expires=dtNumber(at+8);if(results[at+3]!=0&&!f64Less(expires,0)&&!f64Less(when,expires)) results[at+3]=0; }
}
void dtSpawn(uint base,uint count,uint slot,uint kind,uint identity,uint generation,uint64_t capacity,uint64_t expires,uint ownerKind,uint ownerId,uint ownerGeneration,uint64_t when,out uint status)
{
    status=0;
    if(slot>=count||!dtKind(kind)||identity>=0x10000000U||generation==0||generation>=0x80000000U || !dtQuantity(capacity)||!f64Less(0,capacity)||!f64Finite(expires)||!f64Equal(expires,f64FromI64(1)^F64_SIGN)&&!f64Less(when,expires)) { status=64;return; }
    if(ownerKind!=DT_NONE && (ownerKind!=0&&ownerKind!=5 || ownerId>=0x10000000U||ownerGeneration==0||ownerGeneration>=0x80000000U) || ownerKind==DT_NONE&&(ownerId!=0||ownerGeneration!=0)) { status=64;return; }
    if(kind==4)
    { uint conversion;uint64_t integer=f64ToI64(capacity,1,conversion);if(conversion!=0||integer>0x7fffffffU||!f64Equal(capacity,f64FromI64(integer))) { status=64;return; } }
    uint at=dtAt(base,slot),old=results[at+2];
    if(results[at+3]!=0 || old!=0&&(results[at]!=kind||results[at+1]!=identity) || generation!=old+1) { status=64;return; }
    for(uint i=0;i<count;i++) if(i!=slot)
    { uint p=dtAt(base,i);if(results[p+2]!=0&&results[p]==kind&&results[p+1]==identity) { status=64;return; } }
    results[at]=kind;results[at+1]=identity;results[at+2]=generation;results[at+3]=1;
    dtStore(at+4,capacity);dtStore(at+6,capacity);dtStore(at+8,expires);
    results[at+10]=ownerKind;results[at+11]=ownerId;results[at+12]=ownerGeneration;results[at+13]=0;
}
bool dtMatches(uint at,uint kind,uint identity,uint generation)
{ return results[at+3]!=0&&results[at]==kind&&results[at+1]==identity&&results[at+2]==generation; }
uint64_t dtHit(uint base,uint count,uint slot,uint kind,uint identity,uint generation,uint outcome,uint64_t amount,uint64_t credit,out bool delivered,out bool broken,out uint status)
{
    status=0;delivered=false;broken=false;
    if(slot>=count||!dtKind(kind)||identity>=0x10000000U||generation==0||generation>=0x80000000U||outcome>2||!dtQuantity(amount)||!dtQuantity(credit)||outcome!=2&&!f64Zero(amount)||outcome==0&&!f64Zero(credit)) { status=64;return 0; }
    uint at=dtAt(base,slot);if(!dtMatches(at,kind,identity,generation)) return 0;
    uint64_t value=kind==4?credit:amount,remaining=dtNumber(at+4),took=f64Less(value,remaining)?value:remaining;
    remaining=f64Add(remaining,took^F64_SIGN);dtStore(at+4,remaining);delivered=true;broken=f64Zero(remaining);
    if(broken) results[at+3]=0;return took;
}
bool dtRetire(uint base,uint count,uint slot,uint kind,uint identity,uint generation,out uint status)
{
    status=0;if(slot>=count||!dtKind(kind)||identity>=0x10000000U||generation==0||generation>=0x80000000U) { status=64;return false; }
    uint at=dtAt(base,slot);bool matched=dtMatches(at,kind,identity,generation);if(matched) results[at+3]=0;return matched;
}
void dtSelect(uint base,uint count,uint kinds,uint answer,out uint status)
{
    status=0;if(kinds==0||(kinds&~28U)!=0) { status=64;return; }
    for(uint i=0;i<4;i++) results[answer+i]=0;
    for(uint i=0;i<count;i++) { uint at=dtAt(base,i);if(results[at+3]!=0&&(kinds&(1U<<results[at]))!=0) results[answer+i/32]|=1U<<(i%32); }
}
