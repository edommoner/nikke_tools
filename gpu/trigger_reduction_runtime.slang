// The canonical raw-timing/caster mask is immutable input. Runtime membership,
// expiry and literal accumulation use one resident walk for CUDA and Metal.
bool triggerReducer(inout Runtime s,uint row)
{ return (definition_quantityFlags(s.inputBase,row)&P_TRIGGER_REDUCTION_FLAG)!=0; }
uint triggerReductionMeta(inout Runtime s,uint row)
{ return s.inputBase+P_MODE_BASE+row*P_MODE_WORDS; }
bool triggerReductionEvent(uint event)
{ return event==7||event==8||event==11||event==12||event==20||event==22||event==23||event==40||event==49; }

[noinline]
bool validTriggerReductions(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind==2) { if(triggerReducer(s,row)) return false;continue; }
        uint meta=triggerReductionMeta(s,row);
        if(!triggerReducer(s,row))
        { for(uint field=P_TRIGGER_REDUCTION_OFFSET;field<P_TRIGGER_REDUCTION_END;field++) if(commands[meta+field]!=0) return false;continue; }
#ifndef PORTABLE_WORLD_ROSTER
        return false;
#else
        if(s.combat==0 || d.kind!=4 || d.stat!=0 || d.quantityFlags!=P_TRIGGER_REDUCTION_FLAG || d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 ||
           commands[meta+P_TRIGGER_REDUCTION_OFFSET]!=P_TRIGGER_REDUCTION_MAGIC) return false;
        uint64_t literal=loadNumber(meta+P_TRIGGER_REDUCTION_OFFSET+1);
        if(!f64Finite(literal)||f64Less(f64FromI64(100000000),f64Abs(literal))) return false;
        for(uint word=0;word<P_MASK_WORDS;word++)
        {
            uint bits=commands[meta+P_TRIGGER_REDUCTION_MASK+word];
            for(uint bit=0;bit<32;bit++) if((bits&(1U<<bit))!=0)
            { uint target=word*32+bit;if(target>=s.count || definition_owner(s.inputBase,target)!=d.owner) return false; }
        }
        s.quantityMask|=1024;
#endif
    }
    return true;
}

[noinline]
bool triggerReductionCountMatches(inout Runtime s,uint row,uint count,uint64_t threshold,uint mode,uint64_t when)
{
    uint64_t sum=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0 || !triggerReducer(s,definition) || !f64Less(when,s.end[slot])) continue;
        uint meta=triggerReductionMeta(s,definition);
        if((commands[meta+P_TRIGGER_REDUCTION_MASK+row/32]&(1U<<(row%32)))==0) continue;
        // Native ignores stacks, runtime predicates and selected recipients.
        sum=f64Add(sum,loadNumber(meta+P_TRIGGER_REDUCTION_OFFSET+1));
    }
    uint status;uint64_t reduction=f64ToI64(sum,1,status);
    if(status!=0) { s.error=2;return false; }
    // Bound512 *1e8 keeps the ordered sum and integer difference inside i64.
    // Negative reductions may exceed the32-bit event counter's horizon.
    if((reduction&(uint64_t(1)<<63))!=0) threshold+=uint64_t(0)-reduction;
    else threshold=reduction>=threshold ? 1 : threshold-reduction;
    return mode==2 ? uint64_t(count)>=threshold : mode==3 ? uint64_t(count)==threshold : uint64_t(count)%threshold==0;
}
