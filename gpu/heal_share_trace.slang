// Diagnostic-only append log. It neither samples conditions nor drives replay.
void traceHealShare(inout Runtime s,uint kind,uint who,uint64_t when,uint64_t amount,uint64_t weights=0,uint source=0xffffffff)
{
#ifdef PORTABLE_HEAL_SHARE_DIAGNOSTIC
    uint head=s.resourceOutput+771072,count=results[head+1];
    if(count>=512) { results[head+2]=1;s.error=64;return; }
    results[head]=0x48534831;results[head+1]=count+1;
    uint at=head+8+count*20;
    results[at]=kind;results[at+1]=who;results[at+2]=source;
    storeNumber(at+3,when);storeNumber(at+5,amount);storeNumber(at+7,weights);
    if(kind==1 || kind==5) for(uint member=0;member<5;member++) storeNumber(at+9+member*2,s.hp[member]);
#endif
}
