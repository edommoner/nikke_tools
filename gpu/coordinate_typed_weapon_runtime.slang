// Typed physical recipients reuse the actual sampled shot and common scalar.
// Scratch is exclusive to the weapon-only descriptor (all skill routes zero).
static const uint CTW_MAGIC=0x43545731U,CTW_KEEP=2048U,CTW_WORDS=24U;
bool coordinateTypedWeapons(inout Runtime s){return commands[DF_EXTRA(s)]==0x54474731U&&commands[DF_EXTRA(s)+13]==1;}
uint ctwHead(inout Runtime s){return DT_OUTPUT(s.resourceOutput,170976);}
uint ctwPellet(inout Runtime s,uint hit){return DF_SCRATCH(s.resourceOutput,0)+hit*8;}
uint ctwGenerations(inout Runtime s){return DF_SCRATCH(s.resourceOutput,0)+8192;}
void ctwCompress(uint h)
{
    uint hash[8],block[16];for(uint i=0;i<8;i++)hash[i]=results[h+8+i];for(uint i=0;i<16;i++)block[i]=results[h+16+i];
    sha256Block(hash,block);for(uint i=0;i<8;i++)results[h+8+i]=hash[i];
}
void ctwInitialize(inout Runtime s)
{
    uint h=ctwHead(s);if(results[h]!=0)return;
    results[h]=CTW_MAGIC;results[h+1]=1;results[h+4]=CTW_KEEP;results[h+5]=CTW_WORDS;
    results[h+8]=0x6a09e667U;results[h+9]=0xbb67ae85U;results[h+10]=0x3c6ef372U;results[h+11]=0xa54ff53aU;
    results[h+12]=0x510e527fU;results[h+13]=0x9b05688cU;results[h+14]=0x1f83d9abU;results[h+15]=0x5be0cd19U;
}
void ctwSnapshot(inout Runtime s,uint who,Weapon w,uint64_t coefficient,uint64_t when)
{
    if(!coordinateTypedWeapons(s))return;ctwInitialize(s);
    uint h=csMeta(s),p=DF_EXTRA(s),count=commands[p+2],n=0;
    storeNumber(h+48,f64Div(coefficient,f64FromI64(w.pellets)));results[h+55]=uint(!WORLD_PACKET_NORMAL(s,who));
    storeNumber(h+56,destructibleModifierQuantity(s,DT_INPUT(s,5168),who,2,when));
    storeNumber(h+58,destructibleModifierQuantity(s,DT_INPUT(s,5168),who,3,when));
    WorldSchedule clock=frameSchedule(s);
    for(uint slot=0;slot<count;slot++)
    {
        uint state=dtAt(DF_BASE(s.resourceOutput),slot),node=commands[p+2328+slot*12],live=wsState(clock,node);
        results[ctwGenerations(s)+slot]=results[state+2];
        if(results[state+3]==0)continue;
#ifdef PORTABLE_MOVING_TYPED
        if(!movingTypedVisible(s,slot))continue;
#endif
        if(results[live]==0||results[live+1]!=results[state+2]){s.error=64;return;}
        uint j=n;while(j>0&&typedGeometryBefore(s,slot,results[h+640+j-1])){results[h+640+j]=results[h+640+j-1];j--;}
        results[h+640+j]=slot;n++;
    }
    results[h+64]=n;results[h+65]=++results[ctwHead(s)+6];
}
bool ctwContains(inout Runtime s,uint slot,uint64_t x,uint64_t y,uint64_t grow)
{
    uint row=DF_EXTRA(s)+16+slot*18;uint64_t co=ONE,si=0;
    if(commands[row]==2)coordinateSinCosDegrees(cNumber(row+12),si,co);
#ifdef PORTABLE_MOVING_TYPED
    uint64_t d=coordinateShapeDistance(commands[row],movingTypedCenter(s,slot,0),movingTypedCenter(s,slot,1),cNumber(row+6),cNumber(row+8),cNumber(row+10),co,si,x,y);
#else
    uint64_t d=coordinateShapeDistance(commands[row],cNumber(row+2),cNumber(row+4),cNumber(row+6),cNumber(row+8),cNumber(row+10),co,si,x,y);
#endif
    if(!f64Finite(d)){s.error=16;return false;}return coordinateShapeContains(d,grow);
}
bool ctwBeforeCanonical(inout Runtime s,uint typed,uint canonical)
{
    if(canonical==0)return true;
    uint p=DF_EXTRA(s),a=p+16+typed*18,node=commands[p+2328+typed*12];
#ifdef PORTABLE_MOVING_TYPED
    uint logical=lagActive(s)?lagShape(s,canonical):0;
    if(logical!=0)
    {
        uint64_t az=cNumber(a+14),bz=cNumber(logical+20);if(!f64Equal(az,bz))return f64Less(bz,az);
        WorldSchedule clock=frameSchedule(s);uint64_t at=wsRead(wsState(clock,node)+2),bt=actorNumber(actorPoolAt(s,canonical)+8);
        if(!f64Equal(at,bt))return f64Less(bt,at);
        uint binding=actorBinding(s,canonical);
        if(node!=commands[binding+3])return node>commands[binding+3];
        // Both authored typed and logical shapes use the same stable subdomain.
        return typed>commands[binding+4];
    }
#endif
    CoordinateScene scene=coordinatePoolView(s);uint b=cRow(scene,commands[coordinateAreaRow(s,canonical)]-1);
    uint64_t az=cNumber(a+14),bz=cNumber(b+18);if(!f64Equal(az,bz))return f64Less(bz,az);
    WorldSchedule clock=frameSchedule(s);uint64_t at=wsRead(wsState(clock,node)+2),bt=actorNumber(cState(scene,commands[coordinateAreaRow(s,canonical)]-1)+scene.poolStart);
    if(!f64Equal(at,bt))return f64Less(bt,at);
    if(node!=commands[b+2])return node>commands[b+2];
    // Canonical ordinal and authored typed slot have separate stable domains.
    return typed>=commands[b+3];
}
uint ctwSelectPellet(inout Runtime s,uint hit,uint canonical,uint64_t x,uint64_t y,uint64_t grow)
{
    uint scratch=ctwPellet(s,hit);for(uint i=0;i<8;i++)results[scratch+i]=0;
    uint h=csMeta(s),front=0xffffffffU;
    for(uint i=0;i<results[h+64];i++)
    {
        uint slot=results[h+640+i];
        if(front==0xffffffffU&&ctwContains(s,slot,x,y,0))front=slot;
        if(f64Less(0,grow)&&ctwContains(s,slot,x,y,grow))results[scratch+2+slot/32]|=1U<<(slot%32);
    }
    bool chosen=front!=0xffffffffU&&ctwBeforeCanonical(s,front,canonical);
    results[scratch]=chosen?front+1:0;
    if(chosen)results[scratch+1]=results[ctwGenerations(s)+front];
    return chosen?0xffffffffU:canonical;
}
uint ctwReachCount(inout Runtime s,uint hit)
{
    uint count=0;for(uint i=0;i<4;i++)count+=countbits(results[ctwPellet(s,hit)+2+i]);return count;
}
void ctwSampleAmount(inout Runtime s,uint hit,bool critical,bool reach)
{
    uint scratch=ctwPellet(s,hit);if(results[scratch]==0&&(!reach||ctwReachCount(s,hit)==0))return;
    uint h=csMeta(s),kind=commands[DF_EXTRA(s)+3];uint64_t factors[9];for(uint i=0;i<9;i++)factors[i]=actorNumber(h+20+i*2);
    factors[2]=sampledCoordinateF3(s,critical,false);
    factors[4]=f64Add(factors[4],f64Div(actorNumber(h+(kind==2?56:58)),HUNDRED));
    storeNumber(scratch+6,damageFromFactors(s,factors,false));
}
void ctwParentAdd(inout Runtime s,uint hit,bool reach,inout PacketIntegerSum total)
{
    uint scratch=ctwPellet(s,hit),count=reach?ctwReachCount(s,hit):uint(results[scratch]!=0);
    for(uint i=0;i<count;i++)if(!packetIntegerAddAmount(total,actorNumber(scratch+6))){s.error=16;return;}
}
void ctwNotify(inout Runtime s,uint who,uint slot,uint generation,uint identity,uint family,uint attack,uint64_t amount,uint64_t when,DWReceipt r)
{
    if(r.delivered==0)return;
    uint packet=ctwGenerations(s)+128;for(uint i=0;i<16;i++)results[packet+i]=0;
    results[packet]=3;storeNumber(packet+1,when);results[packet+3]=who;results[packet+4]=commands[DF_EXTRA(s)+3];results[packet+5]=identity;results[packet+6]=generation;
    results[packet+7]=family;results[packet+8]=2;storeNumber(packet+9,amount);storeNumber(packet+11,ONE);results[packet+13]=attack;
    uint start=collectTargetCounters(s,packet|0x80000000U,when);
    if(s.error==0&&results[counterHead(s)+4]>start)dispatch(s,26,0,0,int(start),when,s.resourceOutput);
    if(r.broken!=0&&s.error==0)
    {
        results[packet]=4;start=collectTargetCounters(s,packet|0x80000000U,when);
        if(s.error==0&&results[counterHead(s)+4]>start)dispatch(s,26,0,0,int(start),when,s.resourceOutput);
    }
}
void ctwLand(inout Runtime s,uint who,uint hit,uint slot,bool extra,uint64_t when)
{
    uint h=ctwHead(s),count=results[h+2];if(count>=0x7fffffU){s.error=64;return;}
    uint scratch=ctwPellet(s,hit),kind=commands[DF_EXTRA(s)+3],identity=commands[DF_EXTRA(s)+2328+slot*12+2];
    uint generation=results[ctwGenerations(s)+slot],attack=0x800000U+count+1,meta=csMeta(s);uint64_t amount=actorNumber(scratch+6);
    WorldSchedule clock=frameSchedule(s);DWReceipt r=dwLand(clock,DF_BASE(s.resourceOutput),commands[DF_EXTRA(s)+2320],DF_HEADER(s.resourceOutput),slot,kind,identity,generation,2,amount,ONE,when);
    if(clock.error!=0){s.error=clock.error;return;}
    uint at=h+64+min(count,CTW_KEEP)*CTW_WORDS;for(uint i=0;i<CTW_WORDS;i++)results[at+i]=0;
    results[at]=attack;results[at+1]=who;results[at+2]=kind;results[at+3]=identity;results[at+4]=generation;results[at+5]=slot;
    storeNumber(at+6,when);storeNumber(at+8,actorNumber(meta+48));storeNumber(at+10,amount);storeNumber(at+12,r.took);
    results[at+14]=r.delivered;results[at+15]=r.broken;results[at+16]=0;results[at+17]=uint(extra);results[at+18]=results[csRow(s,hit)+1]&1;
    results[at+19]=results[meta+55];results[at+20]=results[meta+65];results[at+21]=hit;
    uint pending=results[h+7];for(uint i=0;i<CTW_WORDS;i++){results[h+16+pending++]=sha256Swap(results[at+i]);if(pending==16){ctwCompress(h);pending=0;}}
    results[h+7]=pending;results[h+2]=count+1;results[h+3]=min(count+1,CTW_KEEP);
    if(count>=CTW_KEEP)for(uint i=0;i<CTW_WORDS;i++)results[at+i]=0;
    ctwNotify(s,who,slot,generation,identity,0,attack,amount,when,r);
}
uint64_t ctwDeliverTargets(inout Runtime s,uint who,uint hit,bool reach,uint64_t when
#ifdef PORTABLE_MOVING_TYPED
    ,bool grouped
#endif
)
{
    uint h=csMeta(s),at=csRow(s,hit),scratch=ctwPellet(s,hit),normal=0,typed=0,n=results[h+3],tn=results[h+64];
    // Merge the two frozen orders. BODY precedes every reach extra exactly as
    // in the canonical producer; normal target delivery retains all consumers.
    while((normal<n||typed<tn)&&s.error==0)
    {
        uint canonical=normal<n?results[h+CS_FRAME+normal*4]:0;
        uint slot=typed<tn?results[h+640+typed]:0xffffffffU;
        if(slot!=0xffffffffU&&(normal>=n||ctwBeforeCanonical(s,slot,canonical)))
        {
            typed++;if(reach?(results[scratch+2+slot/32]&(1U<<(slot%32)))!=0:results[scratch]==slot+1)ctwLand(s,who,hit,slot,reach,when);
        }
        else
        {
            uint e=h+CS_FRAME+normal*4;normal++;uint targetKind=results[e+1];
            if(!(reach?(results[at+8+canonical/32]&(1U<<(canonical%32)))!=0:canonical==results[at]))continue;
#ifdef PORTABLE_MOVING_TYPED
            if(lagActive(s)&&targetKind==5)
            {
                coordinateGroupDirectPacket(s,who,canonical,results[e+3],lagAmount(s,hit,5),when,reach,grouped);continue;
            }
#endif
            uint slot=canonical,gen=coordinateLandingGeneration(s,slot,results[e+3]);uint64_t amount=actorNumber(at+(targetKind==1?4:6));bool extra=reach;uint64_t legacy=0;
#define CF_PACKET_EXTRA extra
#include "coordinate_physical_target_delivery.slang"
#undef CF_PACKET_EXTRA
        }
    }
    return 0;
}
bool finishCoordinateTypedWeaponHistory(inout Runtime s)
{
    if(!coordinateTypedWeapons(s))return true;ctwInitialize(s);uint h=ctwHead(s),count=results[h+2],pending=results[h+7];
    if(results[h]!=CTW_MAGIC||results[h+40]!=0||count>0x7fffffU||pending!=(count*CTW_WORDS)%16)return false;
    results[h+16+pending++]=0x80000000U;
    if(pending>14){while(pending<16)results[h+16+pending++]=0;ctwCompress(h);pending=0;}
    while(pending<14)results[h+16+pending++]=0;
    uint64_t bits=uint64_t(count)*uint64_t(CTW_WORDS)*32;results[h+30]=uint(bits>>32);results[h+31]=uint(bits);ctwCompress(h);
    for(uint i=0;i<8;i++)results[h+32+i]=results[h+8+i];results[h+40]=1;return true;
}
