#include "sha256_runtime.slang"
// Ordered named scalar readers, literal colliders, existing frozen queue.
uint nrbInput(inout Runtime s){return s.inputBase+NRB_BASE;}
uint nrbRule(inout Runtime s,uint row)
{
    uint p=nrbInput(s);for(uint i=0;i<commands[p+2];i++)if(commands[p+NRB_HEADER+i*NRB_ROW_WORDS]==row+1)return p+NRB_HEADER+i*NRB_ROW_WORDS;return 0;
}
bool initializeNamedRangeBattle(inout Runtime s)
{
    uint p=nrbInput(s),count=commands[p+2];
    if(commands[p]!=NRB_MAGIC||commands[p+1]!=1||
#ifndef PORTABLE_PRODUCT_TYPED_NEARBY
       count==0||
#endif
       count>NRB_ROWS||commands[p+3]!=actorPoolCount(s))return false;
    for(uint i=4;i<NRB_HEADER;i++)if(commands[p+i]!=0)return false;
    for(uint i=0;i<NRB_ROWS;i++)
    {
        uint at=p+NRB_HEADER+i*NRB_ROW_WORDS;
        if(i>=count){for(uint j=0;j<NRB_ROW_WORDS;j++)if(commands[at+j]!=0)return false;continue;}
        uint row=commands[at]-1,kind=commands[at+4];if(row>=s.count||commands[at+1]==0||commands[at+1]>128||kind!=1&&kind!=2||commands[at+5]>1)return false;
        for(uint j=0;j<i;j++)if(commands[p+NRB_HEADER+j*NRB_ROW_WORDS]==row+1)return false;
        if(commands[at+5]==1&&commands[at+1]<2)return false;
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind!=3||d.damageRoute!=6||d.damageCount!=commands[at+1]||d.damagePending!=0||d.damageHits!=1||d.damageNormal!=0||d.periodicFlags!=0||!f64Zero(d.interval)||(d.damageFlags&((commands[at+5]==0?H_SPLIT:0U)|H_PIERCE|H_EXPLOSION|65536U))!=0)return false;
        if(!f64Finite(cNumber(at+2))||f64Less(cNumber(at+2),0))return false;
        for(uint j=6;j<22;j+=2)if(!f64Finite(cNumber(at+j)))return false;
        uint64_t radius=cNumber(at+10),w=cNumber(at+12),h=cNumber(at+14);
        if(kind==1?!(f64Less(0,radius)&&f64Zero(w)&&f64Zero(h)):!(f64Zero(radius)&&f64Less(0,w)&&f64Less(0,h)))return false;
        uint64_t si=0,co=ONE;if(kind==2)coordinateSinCosDegrees(cNumber(at+16),si,co);
        if(cNumber(at+18)!=co||cNumber(at+20)!=si)return false;
        for(uint j=22;j<NRB_ROW_WORDS;j++)if(commands[at+j]!=0)return false;
    }
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);if(d.stat!=NRB_RANGE_STAT)continue;
        if(d.kind!=0||d.enemyBuff!=0||d.targetName<0||d.targetName>=int(P_DEFINITIONS)||d.lazyGroup!=0||d.queryResolve!=0||d.alliedFlags!=0||d.healthScaling!=0||d.quantityFlags!=0||d.damageFlags!=0||d.bulletDuration!=0||!f64Finite(d.value)||f64Less(d.value,HUNDRED^F64_SIGN)||!f64Zero(d.interval))return false;
        uint plan=s.inputBase+P_RECIPIENT_BASE+row*8;if(commands[plan]!=0&&commands[plan]!=1&&commands[plan]!=12)return false;
    }
    for(uint i=NRB_OUT;i<NRB_END;i++)results[s.resourceOutput+i]=0;
    results[s.resourceOutput+NRB_OUT]=NRB_MAGIC;results[s.resourceOutput+NRB_OUT+1]=1;return true;
}
bool namedRangeBattleRadius(inout Runtime s,Definition d,uint rule,uint64_t when,out uint64_t total,out uint64_t factor,out uint64_t radius)
{
    total=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition e=residentDefinition(s,slot);
        if(e.stat!=NRB_RANGE_STAT||e.targetName!=int(d.name)||s.alive[slot]==0||!f64Less(when,s.end[slot])||(s.activeRecipients[slot]&(1U<<d.owner))==0||!basicConditions(s,slot,when,true,d.owner))continue;
        total=f64Add(total,recipientValue(s,slot,d.owner));
    }
    factor=f64Add(ONE,f64Div(total,HUNDRED));radius=f64Mul(cNumber(rule+2),factor);
    return f64Finite(total)&&f64Finite(factor)&&f64Finite(radius)&&!f64Less(factor,0)&&!f64Less(radius,0);
}
// Reuse the captured immutable actor set as the temporary distance order.
// No new local128-element array or second actor/HP pool is introduced.
uint64_t namedRangeShapeDistance(inout Runtime s,uint rule,uint slot,uint64_t x,uint64_t y)
{
    if(slot==0)return coordinateShapeDistance(commands[rule+4],cNumber(rule+6),cNumber(rule+8),cNumber(rule+10),cNumber(rule+12),cNumber(rule+14),cNumber(rule+18),cNumber(rule+20),x,y);
    uint shape=lagShape(s,slot);if(shape==0){s.error=64;return 0;}
    uint64_t co=cNumber(shape+22),si=cNumber(shape+24);
#ifdef PORTABLE_ENEMY_MOVEMENT
    uint64_t sx=enemyMovementPosition(s,shape,0),sy=enemyMovementPosition(s,shape,1);
#else
    uint64_t sx=cNumber(shape+8),sy=cNumber(shape+10);
#endif
    return coordinateShapeDistance(commands[shape+6],sx,sy,cNumber(shape+12),cNumber(shape+14),cNumber(shape+16),co,si,x,y);
}
bool orderNearbyActors(inout Runtime s,uint rule,uint set,out uint64_t x,out uint64_t y)
{
    x=0;y=0;uint count=results[set];if(count==0)return false;
    uint primary=results[set+8];
    if(primary==0){x=cNumber(rule+6);y=cNumber(rule+8);}
    else
    {
        uint shape=lagShape(s,primary);if(shape==0)return false;
#ifdef PORTABLE_ENEMY_MOVEMENT
        x=enemyMovementPosition(s,shape,0);y=enemyMovementPosition(s,shape,1);
#else
        x=cNumber(shape+8);y=cNumber(shape+10);
#endif
    }
    for(uint i=0;i<count;i++)
    {
        uint entry=set+8+i*4;uint64_t distance=namedRangeShapeDistance(s,rule,results[entry],x,y);
        if(s.error!=0||!f64Finite(distance))return false;
        storeNumber(entry+2,distance);
    }
    // Index0 is always the primary. Equal distances retain the canonical
    // ADD birth/BODY tie order from actorSetCapture's nearest selection.
    for(uint i=2;i<count;i++)
    {
        uint entry=set+8+i*4,slot=results[entry],generation=results[entry+1],j=i;
        uint64_t distance=actorNumber(entry+2);
        while(j>1&&f64Less(distance,actorNumber(set+8+(j-1)*4+2)))
        {
            for(uint k=0;k<4;k++)results[set+8+j*4+k]=results[set+8+(j-1)*4+k];j--;
        }
        entry=set+8+j*4;results[entry]=slot;results[entry+1]=generation;storeNumber(entry+2,distance);
    }
    return true;
}
void nearbyRecipientDigest(inout Runtime s,uint snapshot,uint record)
{
    uint hash[8]={0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
    uint block[16];for(uint j=0;j<16;j++)block[j]=0;
    uint count=results[snapshot],body=results[snapshot+3],read=0,pending=0,total=count+uint(body!=0);
    for(uint i=0;i<total;i++)
    {
        uint slot,generation;
        if(body!=0&&i+1==body){slot=0;generation=1;}
        else {slot=coordinateSnapshotSlot(snapshot,read++);uint node=commands[actorBinding(s,slot)+3];generation=results[snapshot+4+node];}
        uint binding=actorBinding(s,slot);
        block[pending++]=sha256Swap(commands[binding]);block[pending++]=sha256Swap(commands[binding+1]);block[pending++]=sha256Swap(generation);block[pending++]=0;
        if(pending==16){sha256Block(hash,block);pending=0;}
    }
    block[pending++]=0x80000000U;while(pending<14)block[pending++]=0;block[14]=0;block[15]=total*128U;sha256Block(hash,block);
    for(uint i=0;i<8;i++)results[record+22+i]=hash[i];
}
void captureNamedRangeBattleCast(inout Runtime s,Definition d,uint depth,uint64_t when)
{
    uint rule=nrbRule(s,d._wireRow);if(rule==0){captureCoordinateAreaCast(s,d,depth,when);return;}
    if(depth>=CP_CASTS||!coordinateFrameReady(s)||results[actorPoolAt(s,0)]!=1){s.error=64;return;}
    uint64_t total,factor,radius,additional;uint capacity;
    if(!namedRangeBattleRadius(s,d,rule,when,total,factor,radius)||!namedTargetCountValue(s,d.owner,d.name,commands[rule+1],128,when,capacity,additional)){s.error=64;return;}
    uint h=s.resourceOutput+CP_BASE;uint64_t ax=actorNumber(h+8),ay=actorNumber(h+10);
    uint at=s.resourceOutput+CP_CAST+depth*CP_SNAPSHOT_WORDS;for(uint j=0;j<CP_SNAPSHOT_WORDS;j++)results[at+j]=0;
    results[at+1]=0x43505331U;results[at+2]=d._wireRow;
    uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0)index++;
    if(index==P_WORLD_ACTOR_SETS){s.error=64;return;}
    actorSetCapture(s,33,index,d.damageRoute,128,0,d.owner NAMED_ENEMY_ARGUMENT(d._wireRow));if(s.error!=0)return;
    uint set=actorPoolSet(s,index),selected=0,count=0;
    bool nearby=commands[rule+5]==1;
    if(nearby&&!orderNearbyActors(s,rule,set,ax,ay)){s.error=64;results[set+5]=0;results[actorPoolHead(s)+7]--;return;}
    for(uint i=0;i<results[set]&&s.error==0;i++)
    {
        uint slot=results[set+8+i*4],gen=results[set+9+i*4];bool inside=false;
        if(nearby)inside=i==0||coordinateShapeContains(actorNumber(set+8+i*4+2),radius);
        else if(slot==0)
        {
            uint64_t distance=coordinateShapeDistance(commands[rule+4],cNumber(rule+6),cNumber(rule+8),cNumber(rule+10),cNumber(rule+12),cNumber(rule+14),cNumber(rule+18),cNumber(rule+20),ax,ay);
            if(!f64Finite(distance)){s.error=64;break;}inside=coordinateShapeContains(distance,radius);
        }
        else {uint shape=lagShape(s,slot);if(shape==0){s.error=64;break;}inside=lagContains(s,shape,ax,ay,radius);}
        if(!inside||selected>=capacity)continue;
        if(slot==0)results[at+3]=selected+1;
        else
        {
            uint node=commands[actorBinding(s,slot)+3];if(node>=32||count>=127||results[at+4+node]!=0&&results[at+4+node]!=gen){s.error=64;break;}
            results[at+4+node]=gen;results[at+36+count/4]|=slot<<((count%4)*8);count++;
        }
        selected++;
    }
    if(nearby)for(uint i=0;i<results[set];i++)
    {
        uint entry=set+8+i*4,binding=actorBinding(s,results[entry]);
        results[entry+2]=commands[binding];results[entry+3]=commands[binding+1];
    }
    results[at]=count;results[set+5]=0;results[actorPoolHead(s)+7]--;
    if(s.error!=0)return;
    uint head=s.resourceOutput+NRB_OUT,n=results[head+2];if(n>=NRB_CASTS){s.error=64;return;}results[head+2]++;
    uint record=head+NRB_OUT_HEADER+n*NRB_CAST_WORDS;results[record]=d._wireRow;results[record+1]=d.owner;
    storeNumber(record+2,when);storeNumber(record+4,cNumber(rule+2));storeNumber(record+6,total);storeNumber(record+8,factor);storeNumber(record+10,radius);
    results[record+12]=commands[rule+1];results[record+13]=capacity;storeNumber(record+14,additional);results[record+16]=results[at+3];results[record+17]=count;
    storeNumber(record+18,ax);storeNumber(record+20,ay);
    if(nearby)nearbyRecipientDigest(s,at,record);
}
bool captureNamedRangeBattlePacket(inout Runtime s,LandingReceipt r,uint index)
{
    if(nrbRule(s,r.row)==0)return false;
    if(r.coordinatePacket==0||r.coordinatePacket>CP_PACKET_COUNT){s.error=64;return true;}
    uint from=s.resourceOutput+CP_PACKETS+(r.coordinatePacket-1)*CP_SNAPSHOT_WORDS,count=results[from],body=results[from+3];
    if(results[from+1]!=0x43505331U||results[from+2]!=r.row||count>127||body>count+1){s.error=64;return true;}
    uint at=actorPoolSet(s,index);if(results[at+5]!=0){s.error=64;return true;}for(uint j=0;j<P_WORLD_ACTOR_SET_WORDS;j++)results[at+j]=0;
    uint read=0,n=0;
    for(uint i=0;i<count+uint(body!=0);i++)
    {
        uint slot,gen;
        if(body!=0&&i+1==body){slot=0;gen=1;}
        else {slot=coordinateSnapshotSlot(from,read++);if(slot==0||slot>=actorPoolCount(s)||commands[actorBinding(s,slot)]!=5){s.error=64;return true;}uint node=commands[actorBinding(s,slot)+3];if(node>=32){s.error=64;return true;}gen=results[from+4+node];}
        uint state=actorPoolAt(s,slot);if(results[state]!=gen||results[state+1]==0)continue;
        uint target=at+8+n*4,b=actorBinding(s,slot);results[target]=slot;results[target+1]=gen;results[target+2]=commands[b];results[target+3]=commands[b+1];results[at+1+slot/32]|=1U<<(slot%32);n++;
    }
    results[at]=n;results[at+5]=1;results[actorPoolHead(s)+7]++;return true;
}
void deliverNamedRangeBattleParts(inout Runtime s,LandingReceipt r,uint64_t when,uint output
#ifdef PORTABLE_COORDINATE_LIVE_CORE
    ,uint traceSet
#endif
)
{
    if(nrbRule(s,r.row)!=0)return;
    deliverCoordinateAreaTargets(s,r,when,output
#ifdef PORTABLE_COORDINATE_LIVE_CORE
        ,traceSet
#endif
    );
}
