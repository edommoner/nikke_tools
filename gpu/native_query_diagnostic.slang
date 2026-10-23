#if defined(PORTABLE_NATIVE_QUERY_DIAGNOSTIC) && defined(PORTABLE_HEAL_SHARE_DIAGNOSTIC)
#error Native-query and heal-share diagnostic logs require separate entries
#endif
#ifndef PORTABLE_QUERY_WINDOW_LOWER
#define PORTABLE_QUERY_WINDOW_LOWER ((uint64_t(0x402a9999U)<<32)|0x9999999aU)
#define PORTABLE_QUERY_WINDOW_UPPER ((uint64_t(0x402abd70U)<<32)|0xa3d70a3dU)
#endif
// Read-only semantic observation in a separate compile-time diagnostic entry.
// No additional buff/recipient query, invalidation or arithmetic is performed.
void initializeNativeQueryDiagnostic(inout Runtime s)
{
#ifdef PORTABLE_NATIVE_QUERY_DIAGNOSTIC
    uint head=s.resourceOutput+P_NATIVE_DIAG_BASE;
    for(uint i=0;i<P_NATIVE_DIAG_WORDS;i++) results[head+i]=0;
#ifdef PORTABLE_NATIVE_QUERY_CENSUS
    results[head]=0x4e514331U;results[head+8]=2;results[head+9]=2048;
#else
    results[head]=0x4e514431U;results[head+8]=16;results[head+9]=256;
    storeNumber(head+4,PORTABLE_QUERY_WINDOW_LOWER); // default13.3
    storeNumber(head+6,PORTABLE_QUERY_WINDOW_UPPER); // default13.37
#endif
#endif
}
void recordNativeQueryDiagnostic(inout Runtime s,uint who,uint target,uint exclusion,uint epoch,uint64_t when,bool hit,uint64_t values[64])
{
#ifdef PORTABLE_NATIVE_QUERY_DIAGNOSTIC
#ifdef PORTABLE_QUERY_MISSES_ONLY
    if(hit) return;
#endif
#ifdef PORTABLE_NATIVE_QUERY_CENSUS
    if(hit || who!=0) return;
    uint head=s.resourceOutput+P_NATIVE_DIAG_BASE;
    if(results[head+2]!=0 && (uint64_t(results[head+6]) | uint64_t(results[head+7])<<32)==when) return;
    uint index=results[head+2]++;
    if(index==0) storeNumber(head+4,when);
    storeNumber(head+6,when);
    if(index>=2048) { results[head+3]++;return; }
    results[head+1]++;
    results[head+16+index*2]=results[s.resourceOutput+P_REVIVAL_BASE+6];
    results[head+17+index*2]=results[s.resourceOutput+P_REVIVAL_RNG_BASE];
#else
    uint64_t lower=PORTABLE_QUERY_WINDOW_LOWER,upper=PORTABLE_QUERY_WINDOW_UPPER;
    if(f64Less(when,lower) || f64Less(upper,when)) return;
    uint head=s.resourceOutput+P_NATIVE_DIAG_BASE,index=results[head+2]++;
    if(index>=256) { results[head+3]++;return; }
    uint at=head+16+index*16;results[head+1]++;
    results[at]=hit ? 1U : 2U;results[at+1]=who;results[at+2]=target;
    results[at+3]=exclusion;results[at+4]=epoch;results[at+5]=s.phase;
    storeNumber(at+6,when);storeNumber(at+8,values[S_atk_flat]);storeNumber(at+10,values[S_atk_pct]);
    results[at+12]=results[s.resourceOutput+P_REVIVAL_RNG_BASE];
    results[at+13]=results[s.resourceOutput+P_REVIVAL_BASE+6];
#endif
#endif
}
