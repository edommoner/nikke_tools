#include "coordinate_area_layout.slang"
#include "coordinate_math.slang"
#include "coordinate_shape_math.slang"
uint coordinateAreaInput(inout Runtime s){return s.inputBase+CA_BASE_INPUT;}
uint coordinateAreaRow(inout Runtime s,uint slot){return coordinateAreaInput(s)+CA_HEADER+slot*CA_ROW_WORDS;}
bool validCoordinateAreaIR(inout Runtime s)
{
    uint at=coordinateAreaInput(s);CoordinateScene c=coordinatePoolView(s);
    if(commands[at]!=0x43415231U||commands[at+1]!=1||commands[at+2]!=c.count||commands[at+3]!=0)return false;
    for(uint i=4;i<22;i+=2)if(!f64Finite(cNumber(at+i))||i>=8&&f64Less(cNumber(at+i),0))return false;
    for(uint i=12;i<22;i+=2)if(f64Zero(cNumber(at+i)))return false;
    for(uint i=22;i<CA_HEADER;i++)if(commands[at+i]!=0)return false;
    for(uint slot=0;slot<128;slot++)
    {
        uint p=coordinateAreaRow(s,slot);
        if(slot==0||slot>c.count){for(uint j=0;j<8;j++)if(commands[p+j]!=0)return false;continue;}
        uint index=commands[p];if(index==0||index>c.count)return false;
        uint row=cRow(c,index-1);if(commands[row+5]!=slot||commands[p+1]!=commands[row+4]||!f64Zero(cNumber(row+16))||commands[p+6]!=0||commands[p+7]!=0)return false;
        uint64_t co=cNumber(p+2),si=cNumber(p+4);
        if(!coordinateShapeMatrixValid(commands[p+1],co,si))return false;
    }
    return true;
}
bool coordinateAreaContains(inout Runtime s,uint slot,uint64_t ax,uint64_t ay,uint64_t grow)
{
    CoordinateScene c=coordinatePoolView(s);uint m=coordinateAreaRow(s,slot),row=cRow(c,commands[m]-1);
    uint64_t distance=coordinateShapeDistance(commands[row+4],cNumber(row+6),cNumber(row+8),cNumber(row+10),cNumber(row+12),cNumber(row+14),cNumber(m+2),cNumber(m+4),ax,ay);
    return coordinateShapeContains(distance,grow);
}
bool validCoordinateAreaSkill(inout Runtime s,Definition d){return d.damagePending==0;}
// This narrow hook fills the already-existing interruption receipt fields.
uint64_t sampleCoordinateAreaSkill(inout Runtime s,Definition d,uint64_t coefficient,uint64_t when,out uint64_t partAmount,out uint64_t interruptAmount,out uint interruptReach)
{
    partAmount=0;interruptAmount=0;interruptReach=0;if(!coordinateFrameReady(s)){s.error=64;return 0;}
    bool normal=d.damageNormal!=0,marker=(d.damageFlags&65536U)!=0;uint flags=d.damageFlags&~H_PART;
    if(normal&&(s.attackContext[d.owner]&4)!=0)flags|=H_EXPLOSION;
    uint64_t factors[9],intercept,explosion,pierce;uint sampled;
    sampleDamageFactorsForReach(s,d.owner,coefficient,when,factors,intercept,explosion,pierce,sampled,false,normal,normal?s.coreDamageBonus[d.owner]:s.coreBonus,flags,ONE,normal&&(s.attackContext[d.owner]&1)!=0,false,d._wireRow);
    uint64_t amount=damageFromFactors(s,factors,false),grow=0;uint meta=coordinateAreaInput(s);
    if(!marker)
    {
        if((flags&H_PIERCE)!=0)grow=f64Mul(cNumber(meta+8),f64Add(ONE,f64Div(plainQuantity(s,d.owner,S_pierce_range,when),HUNDRED)));
        if((flags&H_EXPLOSION)!=0)grow=larger(grow,f64Mul(f64Mul(cNumber(meta+12+d.owner*2),cNumber(meta+10)),f64Add(ONE,f64Div(plainQuantity(s,d.owner,S_explosion_range,when),HUNDRED))));
    }
    if(!f64Finite(grow)){s.error=64;return 0;}if(!f64Less(0,grow))grow=0;
    uint64_t ax=cNumber(meta+4),ay=cNumber(meta+6);
    if(focusAimEnabled(s)&&results[s.resourceOutput+P_FOCUS_STATE_BASE+6]==0x46414331U)
    {
        uint slot=uint(actorNumber(s.resourceOutput+P_FOCUS_STATE_BASE)>>(8*d.owner))&255U;
        if(slot>0&&slot<128){CoordinateScene c=coordinatePoolView(s);uint m=coordinateAreaRow(s,slot),row=cRow(c,commands[m]-1);ax=cNumber(row+6);ay=cNumber(row+8);}
    }
    cStore(s.resourceOutput+CP_BASE+6,grow);cStore(s.resourceOutput+CP_BASE+8,ax);cStore(s.resourceOutput+CP_BASE+10,ay);
    if((marker||f64Less(0,grow))&&results[s.resourceOutput+CP_FRAME+3]!=0)partAmount=damageFromFactors(s,factors,true);
    if(f64Less(0,grow)){factors[8]=intercept;interruptAmount=damageFromFactors(s,factors,true);interruptReach=1;}
    return amount;
}
void captureCoordinateAreaCast(inout Runtime s,Definition d,uint depth,uint64_t when)
{
    if((d.damageFlags&65536U)!=0){captureCoordinateCast(s,d,depth,when);return;}
    if(depth>=CP_CASTS||!coordinateFrameReady(s)){s.error=64;return;}
    uint at=s.resourceOutput+CP_CAST+depth*CP_SNAPSHOT_WORDS;for(uint j=0;j<CP_SNAPSHOT_WORDS;j++)results[at+j]=0;
    results[at+1]=0x43505331U;results[at+2]=d._wireRow;
    uint head=s.resourceOutput+CP_BASE,frame=s.resourceOutput+CP_FRAME;uint64_t grow=actorNumber(head+6),ax=actorNumber(head+8),ay=actorNumber(head+10);if(!f64Less(0,grow))return;
    uint count=0;
    for(uint i=0;i<results[frame+2];i++)
    {
        uint from=frame+8+i*4,slot=results[from],gen=results[from+3];if(!coordinateAreaContains(s,slot,ax,ay,grow))continue;
        uint node=commands[actorBinding(s,slot)+3];if(node>=32||gen==0||count>=127||results[at+4+node]!=0&&results[at+4+node]!=gen){s.error=64;return;}
        results[at+4+node]=gen;results[at+36+count/4]|=slot<<((count%4)*8);count++;
    }
    results[at]=count;
}
void deliverCoordinateAreaTargets(inout Runtime s,LandingReceipt r,uint64_t when,uint output)
{
    if(r.coordinatePacket==0||r.coordinatePacket>CP_PACKET_COUNT){s.error=64;return;}
    uint at=s.resourceOutput+CP_PACKETS+(r.coordinatePacket-1)*CP_SNAPSHOT_WORDS,count=results[at];Definition d=readDefinition(s.inputBase,r.row);
    if(results[at+1]!=0x43505331U||results[at+2]!=r.row||count>127){s.error=64;return;}
    for(uint i=0;i<count&&s.error==0;i++)
    {
        uint slot=coordinateSnapshotSlot(at,i),binding=actorBinding(s,slot),node=commands[binding+3],gen=results[at+4+node],kind=commands[binding];
        if(slot==0||slot>=actorPoolCount(s)||(kind!=1&&kind!=6)||gen==0||results[actorPoolAt(s,slot)]!=gen){s.error=64;return;}
        uint64_t amount=kind==1?r.partAmount:r.interruptAmount;
        if(!worldOverlayLand(s,d.owner,0,amount,false))continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,d.owner,ACTOR_REF|slot,amount);if(s.error!=0)return;
        coordinateTrace(s,d.owner,slot,gen,amount,when,true);
        if(kind==1)
        {
            uint family=results[counterHead(s)+11];results[counterHead(s)+11]=WORLD_PERIODIC_FAMILY(s,d,((d.damageFlags&H_CORE)!=0&&d.damageNormal==0)?0:1);
            counterPhysicalPacket(s,d.owner,slot,gen,amount,results[actorPoolHead(s)+19]!=0,when,output);results[counterHead(s)+11]=family;
        }
        if((s.healthMask&64)!=0&&s.error==0)dispatch(s,17,0,d.owner,0,when,output,amount);
    }
}
