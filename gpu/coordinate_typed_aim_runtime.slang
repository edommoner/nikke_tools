// Frame-frozen typed aim candidates, sharing the existing world/target clock.
// 0 BODY, 1..127 canonical, 128 core, 129..256 typed slots.
static const uint CTA_MAGIC=0x43544131U;
uint ctaHead(inout Runtime s){return DT_OUTPUT(s.resourceOutput,220224);}
bool typedAimEnabled(inout Runtime s){return commands[DF_EXTRA(s)+14]==1;}
bool typedAimValidSlot(inout Runtime s,uint slot)
{return typedAimEnabled(s)&&coordinateTypedWeapons(s)&&slot>=129&&slot<129+commands[DF_EXTRA(s)+2];}
void ctaHash(inout Runtime s,uint word)
{
    uint h=ctaHead(s);uint64_t a=actorNumber(h+8),b=actorNumber(h+10);
    storeNumber(h+8,(a^uint64_t(word))*uint64_t(0x100000001b3));
    storeNumber(h+10,((b<<7)|(b>>57))^uint64_t(word)*uint64_t(0x9e3779b185ebca87));
}
void typedAimSnapshot(inout Runtime s,uint64_t when)
{
    if(!typedAimEnabled(s))return;
    uint h=ctaHead(s),p=DF_EXTRA(s),n=0;
    if(results[h]==0)
    {
        results[h]=CTA_MAGIC;results[h+1]=1;
        storeNumber(h+8,uint64_t(0xcbf29ce484222325));storeNumber(h+10,uint64_t(0x84222325cbf29ce4));
    }
    if(results[h]!=CTA_MAGIC||results[h+1]!=1){s.error=64;return;}
    if(results[h+2]!=0&&f64Equal(actorNumber(h+4),when))return;
    for(uint i=0;i<512;i++)results[h+32+i]=0;
#ifdef PORTABLE_MOVING_TYPED
    for(uint i=0;i<TMR_AIM_WORDS;i++)results[s.resourceOutput+TMR_AIM_BASE+i]=0;
#endif
    WorldSchedule clock=frameSchedule(s);
    for(uint slot=0;slot<commands[p+2];slot++)
    {
        uint state=dtAt(DF_BASE(s.resourceOutput),slot),node=commands[p+2328+slot*12],live=wsState(clock,node);
        if(results[state+3]==0)continue;
#ifdef PORTABLE_MOVING_TYPED
        if(!movingTypedVisible(s,slot))continue;
        movingTypedAimStore(s,slot);
#endif
        if(results[live]==0||results[live+1]!=results[state+2]){s.error=64;return;}
        uint j=n;
        while(j>0&&typedGeometryBefore(s,slot,results[h+32+(j-1)*4]-129))
        {for(uint k=0;k<4;k++)results[h+32+j*4+k]=results[h+32+(j-1)*4+k];j--;}
        uint row=h+32+j*4;results[row]=129+slot;results[row+1]=results[state+2];results[row+2]=node;results[row+3]=results[state+1];n++;
    }
    results[h+2]++;results[h+3]=n==0?0:results[h+32];storeNumber(h+4,when);results[h+6]=n;
    results[h+7]=uint(focusFirstAdd(s)!=0);
    ctaHash(s,uint(when));ctaHash(s,uint(when>>32));ctaHash(s,n);ctaHash(s,results[h+7]);
    for(uint i=0;i<n*4;i++)ctaHash(s,results[h+32+i]);
}
uint typedAimCandidate(inout Runtime s){return typedAimEnabled(s)?results[ctaHead(s)+3]:0;}
bool typedAimHasAdds(inout Runtime s){return results[ctaHead(s)+7]!=0;}
bool typedAimCenter(inout Runtime s,uint slot,out uint64_t ax,out uint64_t ay)
{
    ax=0;ay=0;if(!typedAimValidSlot(s,slot))return false;
    uint h=ctaHead(s);for(uint i=0;i<results[h+6];i++)if(results[h+32+i*4]==slot)
    {
#ifdef PORTABLE_MOVING_TYPED
        uint at=s.resourceOutput+TMR_AIM_BASE+(slot-129)*4;ax=actorNumber(at);ay=actorNumber(at+2);return true;
#else
        uint row=DF_EXTRA(s)+16+(slot-129)*18;ax=cNumber(row+2);ay=cNumber(row+4);return true;
#endif
    }
    return false;
}
