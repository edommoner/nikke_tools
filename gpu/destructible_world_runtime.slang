// Existing WS graph owns node transitions; DT owns typed target quantities.
// No CPU-computed open/close/spawn list or cleared-mask enters this adapter.
static const uint DW_BIND_WORDS=12U;
bool dwValidate(WorldSchedule w,uint bindings,uint count,uint base)
{
    if(count==0||count>128) return false;
    for(uint slot=0;slot<count;slot++)
    {
        uint d=bindings+slot*DW_BIND_WORDS,node=commands[d],status;
        if(node>=w.count) return false;
        for(uint i=8;i<12;i++) if(commands[d+i]!=0) return false;
        // Admit through the same core initializer, then discard admission state.
        dtSpawn(base,count,slot,commands[d+1],commands[d+2],1,wsLoad(d+3),f64FromI64(1)^F64_SIGN,commands[d+5],commands[d+6],commands[d+7],0,status);
        if(status!=0) return false;
    }
#ifndef PORTABLE_DESTRUCTIBLE_BATTLE
    // The standalone typed clock owns these aggregate clear conditions.
    // An attached battle instead keeps ordinary clear nodes in actorPools;
    // its entry separately rejects bindings to those canonical clear nodes.
    for(uint n=0;n<w.count;n++) if((commands[wsNode(w,n)+1]&2)!=0)
    { bool any=false;for(uint i=0;i<count;i++) if(commands[bindings+i*DW_BIND_WORDS]==n) any=true;if(!any) return false; }
#endif
    for(uint i=count*DW_BIND_WORDS;i<128*DW_BIND_WORDS;i++) if(commands[bindings+i]!=0) return false;
    for(uint i=0;i<128*DT_WORDS;i++) results[base+i]=0;
    return true;
}
uint dwCleared(WorldSchedule w,uint bindings,uint count,uint base)
{
    uint mask=0;
    for(uint n=0;n<w.count;n++)
    {
        uint s=wsState(w,n);if(results[s]==0||(commands[wsNode(w,n)+1]&2)==0) continue;
        bool any=false,clear=true;
        for(uint slot=0;slot<count;slot++) if(commands[bindings+slot*DW_BIND_WORDS]==n)
        { any=true;uint at=dtAt(base,slot);if(results[at+2]!=results[s+1]||results[at+3]!=0) clear=false; }
        if(any&&clear) mask|=1U<<n;
    }
    return mask;
}
void dwSync(inout WorldSchedule w,uint bindings,uint count,uint base,uint64_t when)
{
    for(uint slot=0;slot<count&&w.error==0;slot++)
    {
        uint d=bindings+slot*DW_BIND_WORDS,s=wsState(w,commands[d]),at=dtAt(base,slot),generation=results[s+1],status;
        if(generation==0) continue;
        if(results[at+2]!=0&&(results[s]==0||results[at+2]!=generation))
            dtRetire(base,count,slot,results[at],results[at+1],results[at+2],status);
        if(results[s]!=0&&results[at+2]!=generation)
        { dtSpawn(base,count,slot,commands[d+1],commands[d+2],generation,wsLoad(d+3),f64FromI64(1)^F64_SIGN,commands[d+5],commands[d+6],commands[d+7],when,status);if(status!=0) w.error=status; }
    }
}
bool dwBegin(inout WorldSchedule w,uint bindings,uint count,uint base,uint header,uint64_t when)
{
    if(results[header+3]!=0) { w.error=64;return false; }
    uint status;dtAdvance(base,count,when,dtNumber(header),status);if(status!=0) { w.error=status;return false; }
    if(results[header+2]!=0&&f64Equal(when,dtNumber(header))) return false;
    wsBegin(w,when,dwCleared(w,bindings,count,base));if(w.error!=0) return false;
    dwSync(w,bindings,count,base,when);dtStore(header,when);results[header+2]=1;return true;
}
void dwFinish(inout WorldSchedule w,uint bindings,uint count,uint base,uint header,uint64_t when)
{
    if(results[header+3]!=0) { w.error=64;return; }
    uint status;dtAdvance(base,count,when,dtNumber(header),status);if(status!=0) { w.error=status;return; }
    wsFinish(w,when);if(w.error==0) dwSync(w,bindings,count,base,when);
    dtStore(header,when);results[header+3]=1;
}
struct DWReceipt
{
    uint delivered,broken,kind,identity,generation,ownerKind,ownerId,ownerGeneration;
    uint64_t took,when;
};
DWReceipt dwLand(inout WorldSchedule w,uint base,uint count,uint header,uint slot,uint kind,uint identity,uint generation,uint outcome,uint64_t amount,uint64_t credit,uint64_t when)
{
    DWReceipt r;r.delivered=0;r.broken=0;r.kind=0;r.identity=0;r.generation=0;r.ownerKind=DT_NONE;r.ownerId=0;r.ownerGeneration=0;r.took=0;r.when=0;
    if(results[header+2]==0||results[header+3]!=0||!f64Equal(dtNumber(header),when)) { w.error=64;return r; }
    bool delivered,broken;uint status;r.took=dtHit(base,count,slot,kind,identity,generation,outcome,amount,credit,delivered,broken,status);w.error=status;
    r.delivered=uint(delivered);r.broken=uint(broken);
    if(broken)
    { uint at=dtAt(base,slot);r.kind=kind;r.identity=identity;r.generation=generation;r.ownerKind=results[at+10];r.ownerId=results[at+11];r.ownerGeneration=results[at+12];r.when=when; }
    return r;
}
