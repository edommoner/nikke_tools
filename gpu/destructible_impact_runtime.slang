// Resolved typed receipt -> existing collector/DFS child executor. No duplicate
// credit or completion loop. Packet scratch is caller owned; receipt is by value.
void dwPublishImpact(inout Runtime s,DWReceipt r,uint scratch,uint who,uint family,uint outcome,uint attackId,uint kind,uint identity,uint generation,uint64_t amount,uint64_t credit,uint64_t when,uint output)
{
    if(r.delivered==0||s.error!=0) return;
    for(uint i=0;i<16;i++) results[scratch+i]=0;
    results[scratch]=3;dtStore(scratch+1,when);results[scratch+3]=who;
    results[scratch+4]=kind;results[scratch+5]=identity;results[scratch+6]=generation;
    results[scratch+7]=family;results[scratch+8]=outcome;dtStore(scratch+9,amount);dtStore(scratch+11,credit);results[scratch+13]=attackId;
    uint owned=scratch|0x80000000U,start=collectTargetCounters(s,owned,when);
    if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
    if(r.broken!=0&&s.error==0)
    {
        // Threshold children may have refreshed a marker. Retire that exact
        // dead generation only after its immutable threshold completion ends.
        results[scratch]=4;start=collectTargetCounters(s,owned,when);
        if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
    }
}
