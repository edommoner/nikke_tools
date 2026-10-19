// GPU-owned periodic populations. Immutable slot lifetimes remain input data;
// refresh time plus lifetime reproduces each native binary64 expiry exactly.
uint sourceAddress(inout Runtime s, uint slot) { return s.resourceOutput+P_SOURCE_STATE_BASE+slot*P_SOURCE_STATE_WORDS; }
uint sourceLookup(inout Runtime s, uint owner, uint name) { return results[s.resourceOutput+P_SOURCE_LOOKUP_BASE+owner*P_DEFINITIONS+name]; }
uint sourceDescriptor(inout Runtime s, uint row) { return s.inputBase+P_SOURCE_DEFINITION_BASE+row*P_SOURCE_DEFINITION_WORDS; }
uint64_t sourceNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
[noinline]
uint sourceLiveCount(inout Runtime s, uint slot, uint64_t when)
{
    uint record=sourceAddress(s,slot), row=results[record]-1, at=sourceDescriptor(s,row), count=0;
#ifndef PORTABLE_SOURCE_COUNT_NO_CACHE
    if (results[record+10]==results[record+1] && sourceNumber(record+8)==when) return results[record+3];
#endif
    uint64_t start=sourceNumber(record+4);
    for (uint i=0; i<commands[at+1]; i++)
    { uint64_t life=loadNumber(at+8+2*i); if (f64Less(life,0) || f64Less(when,f64Add(start,life))) count++; }
    results[record+3]=count; results[record+10]=results[record+1]; storeNumber(record+8,when);
    return count;
}
uint64_t sourceInterval(inout Runtime s, uint row, uint count)
{
    uint at=sourceDescriptor(s,row);
    return f64Mul(loadNumber(at+4),f64Add(ONE,f64Mul(f64Div(loadNumber(at+6),HUNDRED),f64FromI64(count-1))^F64_SIGN));
}
[noinline]
void registerSource(inout Runtime s, uint row, uint64_t when)
{
    uint at=sourceDescriptor(s,row), owner=s.defs[row].owner, name=commands[at];
    uint encoded=sourceLookup(s,owner,name), header=s.resourceOutput+P_SOURCE_HEADER_BASE, slot;
    if (encoded==0)
    {
        slot=results[header]; if (slot>=P_SOURCES) { s.error=2; return; }
        results[header]=slot+1; results[s.resourceOutput+P_SOURCE_LOOKUP_BASE+owner*P_DEFINITIONS+name]=slot+1;
        bool found=false; for (uint i=0; i<results[header+1]; i++) if (results[header+2+i]==owner) found=true;
        if (!found) { uint i=results[header+1]; results[header+2+i]=owner; results[header+1]=i+1; }
    }
    else slot=encoded-1;
    uint record=sourceAddress(s,slot);
    if (results[record+1]==0x7fffffff) { s.error=2; return; }
    results[record]=row+1; results[record+1]++; results[record+2]=1;
    storeNumber(record+4,when); storeNumber(record+6,f64Add(when,sourceInterval(s,row,commands[at+1])));
    results[record+3]=sourceLiveCount(s,slot,when);
}
[noinline]
bool initializeSources(inout Runtime s)
{
    for (uint i=0; i<8; i++) results[s.resourceOutput+P_SOURCE_HEADER_BASE+i]=0;
    for (uint i=0; i<5*P_DEFINITIONS; i++) results[s.resourceOutput+P_SOURCE_LOOKUP_BASE+i]=0;
    for (uint i=0; i<P_SOURCES*P_SOURCE_STATE_WORDS; i++) results[s.resourceOutput+P_SOURCE_STATE_BASE+i]=0;
    uint unique=0;
    for (uint row=0; row<s.count; row++)
    {
        uint at=sourceDescriptor(s,row); Definition d=s.defs[row];
        if (d.kind!=35)
        { for (uint i=0; i<P_SOURCE_DEFINITION_WORDS; i++) if (commands[at+i]!=0) return false; continue; }
        s.sourceEnabled=1;
        if (commands[at]>=P_DEFINITIONS || commands[at+1]==0 || commands[at+1]>P_SOURCE_SLOTS || commands[at+2]>1 || commands[at+3]!=0 || !f64Zero(d.interval) || !f64Zero(d.value) || !f64Equal(d.duration,ONE|F64_SIGN)) return false;
        uint64_t base=loadNumber(at+4), reduction=loadNumber(at+6), bound=f64Mul(f64Div(reduction,HUNDRED),f64FromI64(commands[at+1]-1));
        if (!f64Finite(base) || !f64Less(0,base) || f64Less(f64FromI64(3600),base) || !f64Finite(reduction) || f64Less(reduction,0) || f64Less(HUNDRED,reduction) || !f64Less(bound,ONE)) return false;
        for (uint i=0; i<P_SOURCE_SLOTS; i++)
        {
            uint64_t life=loadNumber(at+8+2*i);
            if (i>=commands[at+1]) { if (!f64Zero(life)) return false; }
            else if (!f64Finite(life) || f64Less(life,0) && !f64Equal(life,ONE|F64_SIGN) || f64Less(f64FromI64(86400),life)) return false;
        }
        bool first=true;
        for (uint other=0; other<row; other++)
            if (s.defs[other].kind==35 && s.defs[other].owner==d.owner && commands[sourceDescriptor(s,other)]==commands[at]) first=false;
        if (first && ++unique>P_SOURCES) return false;
    }
    return true;
}
void writeSourceQuery(inout Runtime s, uint owner, uint name, uint index, uint64_t when)
{
    uint outAt=s.resourceOutput+P_SOURCE_QUERY_BASE+index*8, encoded=sourceLookup(s,owner,name);
    for (uint i=0; i<8; i++) results[outAt+i]=0;
    if (encoded==0) return;
    uint record=sourceAddress(s,encoded-1);
    results[outAt]=1; results[outAt+1]=sourceLiveCount(s,encoded-1,when); results[outAt+2]=results[record+1]; results[outAt+3]=results[record+2];
    storeNumber(outAt+4,sourceNumber(record+6));
}
void finishSourceCounts(inout Runtime s, uint64_t when)
{ for (uint slot=0; slot<results[s.resourceOutput+P_SOURCE_HEADER_BASE]; slot++) results[sourceAddress(s,slot)+3]=sourceLiveCount(s,slot,when); }
