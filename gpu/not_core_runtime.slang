// Context is a tagged owner in the existing Frame.hitCrit word. Bit0 remains
// the hit-critical boolean. Each physical shot freezes its own averaged core.
#ifdef PORTABLE_NOT_CORE
bool notCoreEnabled(inout Runtime s) { return (s.incomingMask&512U)!=0; }
uint notCoreAddress(uint output,uint i)
{ return output+(i<P_NOT_CORE_CELLS0?P_NOT_CORE_BANK0_BASE+i*2:P_NOT_CORE_BANK1_BASE+(i-P_NOT_CORE_CELLS0)*2); }
void initializeNotCore(inout Runtime s)
{
    if(!notCoreEnabled(s)) return;
    for(uint i=0;i<P_NOT_CORE_CELLS;i++) storeNumber(notCoreAddress(s.resourceOutput,i),0);
    for(uint i=0;i<40;i++) results[s.resourceOutput+P_NOT_CORE_SEEN_BASE+i]=0;
    for(uint i=0;i<10;i++) results[s.resourceOutput+P_NOT_CORE_SHOT_BASE+i]=0;
}
void snapshotNotCore(inout Runtime s,uint who,uint pellets)
{
    if(!notCoreEnabled(s)) return;
    uint at=s.resourceOutput+P_WORLD_FRACTION_STATE_BASE+who*8;
    uint64_t core=actorNumber(at+6);Sum sum={};
    for(uint i=0;i<pellets;i++) addSum(sum,core);
    uint64_t mean=f64Div(f64Add(sum.total,sum.correction),f64FromI64(pellets));
    if(pellets==0||!f64Finite(mean)||f64Less(mean,0)||f64Less(ONE,mean)) { s.error=16;return; }
    storeNumber(s.resourceOutput+P_NOT_CORE_SHOT_BASE+who*2,mean);
}
uint notCoreContext(inout Runtime s,uint who) { return notCoreEnabled(s)?(who+1)<<8:0; }
bool notCorePredicate(inout Runtime s,uint definition,uint owner)
{
    uint tag=(s.triggerHitCrit>>8)&7U;
    if(tag>5) { s.error=64;return false; }
    uint64_t core=tag==0?uint64_t(0):actorNumber(s.resourceOutput+P_NOT_CORE_SHOT_BASE+(tag-1)*2);
    uint index=WORLD_TEAM_BUDGET(s,definition)*5+owner;
    if(index>=P_NOT_CORE_CELLS) { s.error=64;return false; }
    uint at=notCoreAddress(s.resourceOutput,index);
    uint64_t value=f64Add(actorNumber(at),f64Add(ONE,core^F64_SIGN));
    bool passed=!f64Less(value,ONE);if(passed) value=f64Add(value,ONE^F64_SIGN);
    storeNumber(at,value);results[s.resourceOutput+P_NOT_CORE_SEEN_BASE+index/32]|=1U<<(index%32);
    return passed;
}
#else
void initializeNotCore(inout Runtime s) {}
void snapshotNotCore(inout Runtime s,uint who,uint pellets) {}
uint notCoreContext(inout Runtime s,uint who) { return 0; }
bool notCorePredicate(inout Runtime s,uint definition,uint owner) { return false; }
#endif
