#include "coordinate_scene.slang"
#include "coordinate_packet_layout.slang"
CoordinateScene coordinatePoolView(inout Runtime s)
{
    CoordinateScene c;c.input=s.inputBase+P_INPUT_WORDS;c.output=s.resourceOutput+CP_BASE;c.count=commands[c.input+2];c.state=actorPoolAt(s,0);c.error=0;c.poolStride=16;c.poolBySlot=1;c.poolStart=8;return c;
}
bool coordinateFrameReady(inout Runtime s) {return results[s.resourceOutput+CP_BASE+1]!=0;}
void coordinateFrameSnapshot(inout Runtime s,uint64_t when)
{
    uint at=s.resourceOutput+CP_FRAME;for(uint i=0;i<CP_FRAME_WORDS;i++)results[at+i]=0;
    cCapture(coordinatePoolView(s),at,when);results[s.resourceOutput+CP_BASE+1]=1;
}
bool validCoordinateSkillDefinition(inout Runtime s,Definition d)
{
    // Ordinary radius selection and delayed/DoT coordinate packets are not connected.
    return d.damagePending==0&&d.periodicFlags==0&&f64Zero(d.interval)&&(d.damageFlags&H_DOT)==0&&((d.damageFlags&65536U)!=0||(d.damageFlags&(H_PIERCE|H_EXPLOSION))==0);
}
uint64_t sampleCoordinateSkill(inout Runtime s,Definition d,uint64_t coefficient,uint64_t when,out uint64_t partAmount)
{
    partAmount=0;if(!coordinateFrameReady(s)){s.error=64;return 0;}
    bool normal=d.damageNormal!=0,marker=(d.damageFlags&65536U)!=0;uint flags=d.damageFlags&~H_PART;
    if(normal&&(s.attackContext[d.owner]&4)!=0)flags|=H_EXPLOSION;
    if(!marker&&(flags&(H_PIERCE|H_EXPLOSION))!=0){s.error=64;return 0;}
    uint64_t factors[9],intercept,explosion,pierce;uint sampled;
    sampleDamageFactorsForReach(s,d.owner,coefficient,when,factors,intercept,explosion,pierce,sampled,true,normal,normal?s.coreDamageBonus[d.owner]:s.coreBonus,flags,ONE,normal&&(s.attackContext[d.owner]&1)!=0,false,d._wireRow);
    uint64_t amount=damageFromFactors(s,factors,false);
    if(marker&&results[s.resourceOutput+CP_FRAME+3]!=0&&s.error==0)partAmount=damageFromFactors(s,factors,true);
    return amount;
}
void captureCoordinateCast(inout Runtime s,Definition d,uint depth,uint64_t when)
{
    if(depth>=CP_CASTS||!coordinateFrameReady(s)){s.error=64;return;}
    uint at=s.resourceOutput+CP_CAST+depth*CP_SNAPSHOT_WORDS;
    for(uint i=0;i<CP_SNAPSHOT_WORDS;i++)results[at+i]=0;
    results[at+1]=0x43505331U;results[at+2]=d._wireRow;
    if((d.damageFlags&65536U)==0)return;
    uint frame=s.resourceOutput+CP_FRAME,count=results[frame+3];if(count>127){s.error=64;return;}results[at]=count;
    for(uint i=0;i<count;i++)
    {
        uint from=frame+8+128*4+i*4,slot=results[from],gen=results[from+3];
        if(slot==0||slot>=actorPoolCount(s)||results[from+1]!=1||gen==0||gen>0x7fffffffU){s.error=64;return;}
        uint node=commands[actorBinding(s,slot)+3];if(node>=32||results[at+4+node]!=0&&results[at+4+node]!=gen){s.error=64;return;}
        results[at+4+node]=gen;results[at+36+i/4]|=slot<<((i%4)*8);
    }
}
uint coordinateSnapshotSlot(uint at,uint index){return (results[at+36+index/4]>>((index%4)*8))&255U;}
void storeCoordinatePacket(inout Runtime s,uint landing,LandingReceipt r)
{
    uint index=(landing-s.resourceOutput-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    if(index>=CP_PACKET_COUNT||r.depth==0||r.depth>CP_CASTS){s.error=64;return;}
    uint from=s.resourceOutput+CP_CAST+(r.depth-1)*CP_SNAPSHOT_WORDS,to=s.resourceOutput+CP_PACKETS+index*CP_SNAPSHOT_WORDS;
    if(results[from+1]!=0x43505331U||results[from+2]!=r.row||results[from]>127){s.error=64;return;}
    for(uint i=0;i<CP_SNAPSHOT_WORDS;i++)results[to+i]=results[from+i];
    uint head=s.resourceOutput+CP_BASE,n=results[head+3],count=results[to],words=4+count*4;
    if(n>CP_SELECTION_WORDS||words>CP_SELECTION_WORDS-n){s.error=64;return;}
    uint log=s.resourceOutput+CP_SELECTION+n;results[log]=r.row;results[log+1]=r.hit;results[log+2]=count;results[log+3]=0;
    for(uint i=0;i<count;i++)
    {
        uint slot=coordinateSnapshotSlot(to,i),binding=actorBinding(s,slot),node=commands[binding+3],at=log+4+i*4;
        results[at]=slot;results[at+1]=commands[binding];results[at+2]=commands[binding+1];results[at+3]=results[to+4+node];
    }
    results[head+3]=n+words;results[head+4]++;
}
void coordinateTrace(inout Runtime s,uint who,uint slot,uint gen,uint64_t amount,uint64_t when,bool extra)
{
    uint head=s.resourceOutput+CP_BASE,count=results[head+2];if(count>=CP_TRACE_COUNT){s.error=64;return;}
    uint at=s.resourceOutput+CP_TRACE+count*CP_TRACE_WORDS;results[at]=who;results[at+1]=slot;results[at+2]=commands[actorBinding(s,slot)];results[at+3]=gen;
    storeNumber(at+4,when);storeNumber(at+6,amount);results[at+8]=uint(extra);for(uint i=9;i<12;i++)results[at+i]=0;results[head+2]=count+1;
}
void deliverCoordinateParts(inout Runtime s,LandingReceipt r,uint64_t when,uint output)
{
    if(r.coordinatePacket==0||r.coordinatePacket>CP_PACKET_COUNT){s.error=64;return;}
    uint at=s.resourceOutput+CP_PACKETS+(r.coordinatePacket-1)*CP_SNAPSHOT_WORDS,count=results[at];Definition d=readDefinition(s.inputBase,r.row);
    if(results[at+1]!=0x43505331U||results[at+2]!=r.row||count>127){s.error=64;return;}
    for(uint i=0;i<count&&s.error==0;i++)
    {
        uint slot=coordinateSnapshotSlot(at,i),binding=actorBinding(s,slot),node=commands[binding+3],gen=results[at+4+node];
        if(slot==0||slot>=actorPoolCount(s)||commands[binding]!=1||gen==0||results[actorPoolAt(s,slot)]!=gen){s.error=64;return;}
        if(!worldOverlayLand(s,d.owner,0,r.partAmount,false))continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,d.owner,ACTOR_REF|slot,r.partAmount);
        if(s.error!=0)return;
        coordinateTrace(s,d.owner,slot,gen,r.partAmount,when,true);
        uint family=results[counterHead(s)+11];results[counterHead(s)+11]=((d.damageFlags&H_CORE)!=0&&d.damageNormal==0)?0:1;
        // Canonical target-kind accounting continues after retirement. Its typed
        // receipt and lifesteal follow it; pool hits/dealt only change while live.
        counterPhysicalPacket(s,d.owner,slot,gen,r.partAmount,results[actorPoolHead(s)+19]!=0,when,output);
        results[counterHead(s)+11]=family;
        if((s.healthMask&64)!=0&&s.error==0)dispatch(s,17,0,d.owner,0,when,output,r.partAmount);
    }
}
