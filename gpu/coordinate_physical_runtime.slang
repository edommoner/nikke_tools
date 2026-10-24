#include "coordinate_physical_layout.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
#include "coordinate_geometry_v1.slang"
#include "coordinate_power_v1.slang"
#include "coordinate_quadrature_v1.slang"
#include "coordinate_landing_resident_v1.slang"
#include "packet_integer_sum.slang"

uint cfBank(inout Runtime s,uint who){return s.resourceOutput+CF_BANK+who*CF_BANK_WORDS;}
uint64_t coordinatePhysicalParentQuantity(inout Runtime s,uint who)
{uint bank=cfBank(s,who);return results[bank+2]!=0?actorNumber(bank+14):uint64_t(0);}
void captureCoordinatePhysicalBodyOnly(inout Runtime s,uint row,uint depth)
{
    if(depth>=CP_CASTS||!coordinateFrameReady(s)){s.error=64;return;}
    uint at=s.resourceOutput+CP_CAST+depth*CP_SNAPSHOT_WORDS;
    for(uint i=0;i<CP_SNAPSHOT_WORDS;i++)results[at+i]=0;
    results[at+1]=0x43505331U;results[at+2]=row;
}
uint64_t coordinatePhysicalBodyCore(inout Runtime s,uint who){return actorNumber(cfBank(s,who)+8);}
bool initializeCoordinatePhysical(inout Runtime s)
{
    // This scratch occupies the dormant group compaction arena. No group
    // owner or group-trigger definition may share this particular profile.
    if(commands[s.inputBase+104402]!=0||s.target!=0||s.landingPolicy!=1)return false;
#ifdef PORTABLE_COORDINATE_LIVE_CORE
    if(!validCoordinateCoreIR(s))return false;
#endif
    if(focusAimEnabled(s))return false; // Explicit waypoints/layer2 need their own caller.
    for(uint row=0;row<s.count;row++)for(uint slot=0;slot<readDefinition(s.inputBase,row).triggerCount;slot++)
        if(commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8]==62)return false;
    for(uint i=CF_BASE;i<CF_END;i++)results[s.resourceOutput+i]=0;
#ifdef PORTABLE_COORDINATE_GEOMETRY_CACHE
    initializeGeometryCache(s);
#endif
    return true;
}
void notifyCoordinatePhysicalTeam(inout Runtime s,uint who,uint64_t when,uint output)
{
    uint bank=cfBank(s,who);
    notifyWorldTeamFraction(s,who,0,actorNumber(bank+4),when,output);
    if(s.error==0)notifyWorldTeamFraction(s,who,1,actorNumber(bank+6),when,output);
}
void cfShape(inout Runtime s,uint to,uint row)
{
    results[to]=commands[row+4];results[to+1]=0;
    for(uint i=0;i<6;i++)clWrite(to+2+i*2,cNumber(row+6+i*2));
    results[to+14]=0;results[to+15]=0;
}
void cfPacket(inout Runtime s,uint bank,uint slot,uint generation,uint64_t amount,bool extra)
{
    uint count=results[bank+1];if(count>=CF_PACKET_COUNT){s.error=64;return;}
    uint at=bank+CF_TEMPLATE+count*CF_PACKET_WORDS;
    results[at]=slot;results[at+1]=generation;storeNumber(at+2,amount);results[at+4]=uint(extra);results[bank+1]=count+1;
}
uint64_t cfWeighted(inout Runtime s,uint64_t amount,uint64_t probability)
{
    uint status;uint64_t integer=f64ToI64(f64Mul(amount,probability),0,status);
    if(status!=0){s.error=16;return 0;}return f64FromI64(integer);
}
[noinline]
uint64_t coordinatePhysicalSample(inout Runtime s,uint who,Weapon w,uint64_t coefficient,uint64_t when)
{
    uint bank=cfBank(s,who),input=s.resourceOutput+CF_INPUT,output=s.resourceOutput+CF_LANDING;
    uint frame=s.resourceOutput+CP_FRAME,n=results[frame+2],count=w.pellets*w.muzzles;
    if(!coordinateFrameReady(s)||n>CL_TARGETS||count==0||count>1024){s.error=64;return 0;}
    for(uint i=0;i<CF_BANK_WORDS;i++)results[bank+i]=0;
    for(uint i=0;i<CL_INPUT;i++)results[input+i]=0;
    for(uint i=0;i<CL_OUTPUT;i++)results[output+i]=0;
    uint64_t accuracy=plainQuantity(s,who,S_accuracy_pct,when),radius=f64Div(currentNormalSpread(s,who,accuracy),uint64_t(0x40000000U)<<32);
    uint flags=WORLD_PACKET_FLAGS(s,who,(w.mode==1?(PARTIAL_IS_FULL(w)?H_CHARGE:0U)|((s.attackContext[who]&4)!=0?H_EXPLOSION:0U):0U));
    if(!f64Zero(plainQuantity(s,who,S_pierce_enabled,when)))flags|=H_PIERCE;
    uint meta=coordinateAreaInput(s);uint64_t grow=0;
    if((flags&H_PIERCE)!=0)grow=f64Mul(cNumber(meta+8),f64Add(ONE,f64Div(plainQuantity(s,who,S_pierce_range,when),HUNDRED)));
    if((flags&H_EXPLOSION)!=0)grow=larger(grow,f64Mul(f64Mul(cNumber(meta+12+who*2),cNumber(meta+10)),f64Add(ONE,f64Div(plainQuantity(s,who,S_explosion_range,when),HUNDRED))));
    if(!f64Finite(radius)||!f64Finite(grow)){s.error=16;return 0;}grow=larger(0,grow);
    results[input]=CL_MAGIC;results[input+1]=1;results[input+2]=n;
    clWrite(input+4,cNumber(meta+4));clWrite(input+6,cNumber(meta+6));clWrite(input+8,radius);clWrite(input+10,grow);
#ifdef PORTABLE_COORDINATE_LIVE_CORE
    uint64_t ax=cNumber(meta+4),ay=cNumber(meta+6),cx,cy,diameter;
    coordinateCoreGeometry(s,ax,ay,cx,cy,diameter);
    clWrite(input+4,ax);clWrite(input+6,ay);
    if(f64Less(0,diameter))
    {
        results[input+3]=1;uint coreAt=clShapeAt(input,CL_TARGETS);results[coreAt]=1;
        clWrite(coreAt+2,cx);clWrite(coreAt+4,cy);clWrite(coreAt+6,f64Div(diameter,uint64_t(0x40000000U)<<32));
    }
#endif
    clWrite(input+12,(uint64_t(0x40046666U)<<32)|uint64_t(0x66666666U)); // MODEL_N=2.55
    for(uint i=0;i<n;i++)
    {
        uint slot=results[frame+8+i*4],area=coordinateAreaRow(s,slot),row=cRow(coordinatePoolView(s),commands[area]-1);
        cfShape(s,clShapeAt(input,i),row);
    }
#ifdef PORTABLE_COORDINATE_GEOMETRY_CACHE
    if(!coordinateCachedLanding(s,input,output,count)){if(s.error==0)s.error=64;return 0;}
#else
    if(!coordinateLandingV1(input,output)){s.error=64;return 0;}
#endif
    uint64_t front=0,part=0;
    for(uint i=0;i<n;i++)
    {
        uint64_t value=actorNumber(output+16+i*2);front=f64Add(front,value);
        if(results[frame+8+i*4+1]==1)part=f64Add(part,value);
    }
    uint64_t open=actorNumber(output+4),under=actorNumber(output+6),wb=larger(0,f64Add(ONE,front^F64_SIGN));
    bool reach=f64Less(0,grow);uint64_t tiny=(uint64_t(0x3d719799U)<<32)|uint64_t(0x812dea11U);
    uint64_t pcb=reach?under:f64Less(tiny,wb)?f64Div(open,wb):uint64_t(0);
    storeNumber(bank+4,part);storeNumber(bank+6,larger(0,f64Add(f64Add(ONE,front^F64_SIGN),open^F64_SIGN)));storeNumber(bank+8,pcb);
    uint64_t factors[9],intercept,explosion,pierce;uint sampled;
    sampleDamageFactorsForReach(s,who,f64Div(coefficient,f64FromI64(w.pellets)),when,factors,intercept,explosion,pierce,sampled,false,WORLD_PACKET_NORMAL(s,who),w.coreBonus,flags,w.fullChargeMult,w.optimal!=0,true);
    // The ordinary factor sampler captured crit and conditional body-core.
    // Fraction notifications instead use the native pellet's open/under core.
    storeNumber(s.resourceOutput+P_WORLD_FRACTION_STATE_BASE+who*8+6,reach?under:open);
    uint64_t body=damageFromFactors(s,factors,false);
    if(reach||f64Less(0,wb))cfPacket(s,bank,0,1,reach?body:cfWeighted(s,body,wb),false);
    bool partReady=false,interruptReady=false;uint64_t partAmount=0,interruptAmount=0;
    for(uint i=0;i<n&&s.error==0;i++)
    {
        uint64_t probability=actorNumber(output+16+(reach?CL_TARGETS*2:0)+i*2);if(!f64Less(0,probability))continue;
        uint at=frame+8+i*4,slot=results[at],kind=results[at+1];uint64_t amount;
        if(kind==1){if(!partReady){partAmount=damageFromFactors(s,factors,true);partReady=true;}amount=partAmount;}
        else if(kind==6)
        {
            if(!interruptReady){uint64_t targetFactors[9];for(uint j=0;j<9;j++)targetFactors[j]=factors[j];targetFactors[8]=intercept;interruptAmount=damageFromFactors(s,targetFactors,true);interruptReady=true;}amount=interruptAmount;
        }
        else{s.error=64;return 0;}
        cfPacket(s,bank,slot,results[at+3],cfWeighted(s,amount,probability),reach);
    }
    if((s.quantityMask&0x01000000U)!=0&&w.mode==1&&PARTIAL_IS_FULL(w))
    {
        PacketIntegerSum sum=packetIntegerZero();
        for(uint i=0;i<results[bank+1];i++)if(!packetIntegerAddAmount(sum,actorNumber(bank+CF_TEMPLATE+i*CF_PACKET_WORDS+2))){s.error=16;return 0;}
        // Native sum(all packets across muzzles)/muzzles is this exact integer.
        // Multiply while still integer; rounding the template sum first loses
        // units when its low bits are later amplified by the pellet count.
        storeNumber(bank+14,packetIntegerBinary64(packetIntegerMultiply(sum,w.pellets)));
    }
    results[bank]=count;storeNumber(bank+10,when);results[bank+2]=1;
    return body;
}
[noinline]
uint64_t coordinatePhysicalDeliver(inout Runtime s,uint who,uint64_t legacy)
{
    uint bank=cfBank(s,who);if(results[bank+2]==0||s.error!=0)return legacy;
    uint count=results[bank],packets=results[bank+1];uint64_t when=actorNumber(bank+10);results[bank+2]=0;
    // The caller's normal landing phase clears these after finishWeaponShot.
    // Do it before publishing our packets, at the same semantic boundary.
    s.frameAmmoActive[who]=0;s.physicalGaugeOwner=0;
    for(uint hit=0;hit<count&&s.error==0;hit++)for(uint i=0;i<packets&&s.error==0;i++)
    {
        uint at=bank+CF_TEMPLATE+i*CF_PACKET_WORDS,slot=results[at],gen=slot==0?1:coordinateLandingGeneration(s,slot,results[at+1]);uint64_t amount=actorNumber(at+2);
        if(s.error!=0)return legacy;if(!worldOverlayLand(s,who,0,amount,false))continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,who,ACTOR_REF|slot,amount);if(s.error!=0)return legacy;
        coordinateTrace(s,who,slot,gen,amount,when,results[at+4]!=0);
        uint kind=commands[actorBinding(s,slot)];
        if(kind==0)publishCounterLanding(s,who,ACTOR_REF|slot,amount,when,s.resourceOutput);
        else if(kind==1)counterPhysicalPacket(s,who,slot,gen,amount,coordinatePartNeedsRetirement(s,slot,gen),when,s.resourceOutput);
        if((s.healthMask&64)!=0&&s.error==0)dispatch(s,17,0,who,0,when,s.resourceOutput,amount);
#ifdef PORTABLE_DAMAGE_ACCUM
        if(slot==0&&damageAccumEnabled(s)&&s.error==0)dispatch(s,39,0,who,0,when,s.resourceOutput,amount);
#endif
    }
    return legacy;
}
