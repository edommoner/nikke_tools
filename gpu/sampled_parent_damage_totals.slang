// Persistent exact main damage uses the unused tail after the physical MT.
// Only BODY/PART credits call this; ADD capping and INTERRUPT stay separate.
static const uint CSP_TOTALS=919704U;
static const uint CSP_TOTALS_WORDS=29U;
void initializeSampledParentDamage(inout Runtime s)
{
    if((s.quantityMask&0x01000000U)==0)return;
    uint head=s.resourceOutput+CSP_TOTALS;
    results[head]=0x43504431U;results[head+1]=1;results[head+2]=5;
}
void recordSampledParentDamage(inout Runtime s,uint who,uint64_t amount)
{
    if((s.quantityMask&0x01000000U)==0)return;
    if(who>=5){s.error=16;return;}
    uint head=s.resourceOutput+CSP_TOTALS,at=head+4+who*5;
    results[head]=0x43504431U;results[head+1]=1;results[head+2]=5;
    PacketIntegerSum value;value.low=actorNumber(at);value.high=actorNumber(at+2);
    PacketIntegerSum before=value;
    if(!packetIntegerAddAmount(value,amount)||value.high<before.high||results[at+4]==0xffffffffU){s.error=16;return;}
    storeNumber(at,value.low);storeNumber(at+2,value.high);results[at+4]++;
}
