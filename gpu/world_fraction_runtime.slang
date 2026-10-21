// One software-binary64 fractional event accumulator for CUDA and Metal.
// Per-shot rates are captured by the common physical damage calculation.
void initializeWorldFraction(inout Runtime s)
{
    WORLD_TEAM_INIT(s) if(!worldFractionEnabled(s)) return;
    uint clock=s.inputBase+P_WORLD_FRACTION_CLOCK_BASE;
    if(commands[clock]!=0x57464331||commands[clock+1]!=1||commands[clock+2]!=5||commands[clock+3]!=0||commands[clock+14]!=0||commands[clock+15]!=0) { s.error=64;return; }
    for(uint who=0;who<5;who++)
    {
        uint64_t delay=loadNumber(clock+4+who*2);
        if(!f64Finite(delay)||f64Less(delay,0)||f64Less(f64FromI64(180),delay)||commands[s.inputBase+P_WEAPON_BASE+who*P_WEAPON_WORDS+1]!=1&&!f64Zero(delay)) { s.error=64;return; }
    }
    for(uint i=P_WORLD_FRACTION_STATE_BASE;i<P_WORLD_FRACTION_TRACE_BASE+P_WORLD_FRACTION_TRACE_COUNT*8;i++) results[s.resourceOutput+i]=0;
    results[s.resourceOutput+P_WORLD_FRACTION_HEAD_BASE]=0x57465231;
}
void sampleWorldFraction(inout Runtime s,uint who,uint64_t critical,uint64_t core)
{
    uint at=s.resourceOutput+P_WORLD_FRACTION_STATE_BASE+who*8;
    storeNumber(at+4,critical);storeNumber(at+6,core);
}
void notifyWorldFraction(inout Runtime s,uint who,uint kind,uint64_t when,uint output)
{
    uint state=s.resourceOutput+P_WORLD_FRACTION_STATE_BASE+who*8,head=s.resourceOutput+P_WORLD_FRACTION_HEAD_BASE;
    uint64_t frac=actorNumber(state+4+kind*2),value=actorNumber(state+kind*2);bool fired=false;
    if(!f64Finite(frac)||f64Less(frac,0)||f64Less(ONE,frac)) { s.error=16;return; }
    if(!f64Less(frac,ONE)) fired=true;
    else if(f64Less(0,frac))
    {
        results[head+2]|=1U<<(who*2+kind);value=f64Add(value,frac);
        if(!f64Less(value,ONE)) { value=f64Add(value,ONE^F64_SIGN);fired=true; }
        storeNumber(state+kind*2,value);
    }
    uint count=results[head+1];if(count>=P_WORLD_FRACTION_TRACE_COUNT) { s.error=64;return; }
    uint at=s.resourceOutput+P_WORLD_FRACTION_TRACE_BASE+count*8;results[head+1]=count+1;
    results[at]=22+kind;results[at+1]=who|(uint(fired)<<3)|(((results[head+2]>>(who*2+kind))&1U)<<4);
    storeNumber(at+2,when);storeNumber(at+4,frac);storeNumber(at+6,value);
    if(fired) dispatch(s,0,22+kind,who,0,when,output);
}
