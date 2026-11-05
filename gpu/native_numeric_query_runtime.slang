// Shared dictionary-query cache. Enabled only for late random numeric readers.
bool nativeNumericEnabled(inout Runtime s)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    return (s.incomingMask&256U)!=0;
#else
    return false;
#endif
}
bool nativeNumericBusy(inout Runtime s)
{ return nativeNumericEnabled(s) && (results[s.resourceOutput+P_NATIVE_QUERY_BASE+4]!=0 || results[s.resourceOutput+P_NATIVE_QUERY_BASE+9]!=0); }
bool nativeNumericDiagnostic(inout Runtime s)
{ return nativeNumericEnabled(s) && results[s.resourceOutput+P_NATIVE_QUERY_BASE+9]!=0; }
void markNativeNumericLanded(inout Runtime s,uint who)
{
    if(!nativeNumericEnabled(s) || (s.normalLandedMask&(1U<<who))!=0) return;
    s.normalLandedMask|=1U<<who;invalidateNativeNumeric(s);
}
bool initializeNativeNumeric(inout Runtime s)
{
    bool expected=false;
    for(uint row=0;row<s.count;row++)
        expected |= definition_kind(s.inputBase,row)==0 &&
            (definition_stat(s.inputBase,row)==S_atk_caster_based_pct || definition_stat(s.inputBase,row)==S_atk_from_hp_pct) &&
            commands[s.inputBase+P_RECIPIENT_BASE+row*8]==19 && commands[s.inputBase+P_RECIPIENT_BASE+row*8+1]!=0;
    bool enabled=commands[s.inputBase+P_RECIPIENT_META_BASE+5]==0x4e515231U;
    if(enabled!=expected) return false;
#ifdef PORTABLE_WORLD_PROJECTILE
    if(!enabled) return true;
    if(s.landingPolicy==0) return false;
    for(uint i=0;i<P_NATIVE_QUERY_HEADER_WORDS;i++) results[s.resourceOutput+P_NATIVE_QUERY_BASE+i]=0;
    for(uint i=0;i<P_NATIVE_QUERY_COUNT;i++) for(uint j=0;j<P_NATIVE_QUERY_CELL_WORDS;j++) results[nativeNumericCell(s.resourceOutput,i)+j]=0;
    s.incomingMask|=256U;s.quantityMask|=256U;
    // Native landing reads the numeric dictionary even when lifesteal is0.
    // Reuse that same reader/continuation so post-hit mutations consume RNG.
    s.healthMask|=64U;
    results[s.resourceOutput+P_NATIVE_QUERY_BASE]=0x4e515231U;
    initializeNativeQueryDiagnostic(s);
#else
    if(enabled) return false;
#endif
    return true;
}
void invalidateNativeNumeric(inout Runtime s)
{
    if(!nativeNumericEnabled(s)) return;
    uint at=s.resourceOutput+P_NATIVE_QUERY_BASE;
    if(results[at+1]==0xffffffffU) { s.error=2;return; }
    results[at+1]++;results[at+2]=0;
}
// Explicit native sync_hp observes the first synchronization even at full HP.
// Seen mask and five exact values use previously reserved cache-header words.
void observeNativeNumericHP(inout Runtime s,uint who)
{
    if(!nativeNumericEnabled(s)) return;
    uint head=s.resourceOutput+P_NATIVE_QUERY_BASE,bit=1U<<who,at=head+12+who*2;
    uint64_t previous=uint64_t(results[at])|(uint64_t(results[at+1])<<32);
    if((results[head+10]&bit)==0 || !f64Equal(previous,s.hp[who])) invalidateNativeNumeric(s);
    results[head+10]|=bit;storeNumber(at,s.hp[who]);
}
uint nativeNumericTarget(inout Runtime s)
{
    uint target=s.target;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    if((target&ACTOR_REF)!=0) target&=127U;
#endif
    return target;
}
bool loadNativeNumeric(inout Runtime s,uint who,uint64_t when,out uint64_t values[64],out uint slot,out uint epoch)
{
    uint head=s.resourceOutput+P_NATIVE_QUERY_BASE;
    epoch=results[head+1];slot=0xffffffffU;
    uint64_t time=uint64_t(results[head+5])|(uint64_t(results[head+6])<<32);
    if(results[head+3]==0 || !f64Equal(time,when))
    { results[head+2]=0;results[head+3]=1;storeNumber(head+5,when); }
    uint count=results[head+2],target=nativeNumericTarget(s);
    for(uint i=0;i<count;i++)
    {
        uint at=nativeNumericCell(s.resourceOutput,i);
        if(results[at]==who && results[at+1]==target && results[at+2]==s.damageExclusion && results[at+3]==epoch && results[at+4]!=0)
        {
            for(uint k=0;k<64;k++) values[k]=uint64_t(results[at+8+k*2])|(uint64_t(results[at+9+k*2])<<32);
            recordNativeQueryDiagnostic(s,who,target,s.damageExclusion,epoch,when,true,values);
            results[head+8]++;return true;
        }
    }
    if(count==P_NATIVE_QUERY_COUNT) { s.error=64;return false; }
    slot=nativeNumericCell(s.resourceOutput,count);results[head+2]=count+1;
    results[slot]=who;results[slot+1]=target;results[slot+2]=s.damageExclusion;results[slot+3]=epoch;results[slot+4]=0;
    results[head+4]=1;results[head+7]++;return false;
}
void storeNativeNumeric(inout Runtime s,uint slot,uint epoch,uint64_t values[64])
{
    uint head=s.resourceOutput+P_NATIVE_QUERY_BASE;results[head+4]=0;
    if(s.error==0 && slot!=0xffffffffU)
        recordNativeQueryDiagnostic(s,results[slot],results[slot+1],results[slot+2],epoch,
            uint64_t(results[head+5])|(uint64_t(results[head+6])<<32),false,values);
    if(s.error!=0 || slot==0xffffffffU || results[head+1]!=epoch) return;
    for(uint k=0;k<64;k++) storeNumber(slot+8+k*2,values[k]);
    results[slot+4]=1;
}
void ensureNativeNumeric(inout Runtime s,uint who,uint64_t when)
{
    if(!nativeNumericEnabled(s) || nativeNumericBusy(s)) return;
    uint64_t ignored[64];collectStats(s,who,when,ignored);
}
