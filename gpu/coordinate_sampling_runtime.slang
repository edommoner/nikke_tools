#include "coordinate_sampling_bank.slang"
#include "coordinate_sample_v1.slang"
#ifdef PORTABLE_COORDINATE_SAMPLED_PARENT
#include "packet_integer_ratio.slang"
#include "sampled_parent_damage_totals.slang"
#ifdef PORTABLE_COORDINATE_SAMPLED_SKILLS
#include "coordinate_sampled_skill_runtime.slang"
#ifdef PORTABLE_COORDINATE_SAMPLED_BURSTS
#include "coordinate_sampled_burst_runtime.slang"
#endif
#endif
#endif
uint csMeta(inout Runtime s){return s.resourceOutput+CS_META;}
uint csRng(inout Runtime s){return s.resourceOutput+CS_RNG;}
uint csRow(inout Runtime s,uint i){return s.resourceOutput+CS_ROWS+i*CS_ROW_WORDS;}
void captureCoordinateSampleBasis(inout Runtime s,uint64_t critical,uint64_t damage,uint64_t coreBonus,uint64_t coreDamage,bool optimal)
{
    uint h=csMeta(s);storeNumber(h+40,critical);
    storeNumber(h+42,larger(0,f64Add(s.baseCritDamage,f64Div(damage,HUNDRED))));
    storeNumber(h+44,f64Add(coreBonus,f64Div(coreDamage,HUNDRED)));
    results[h+46]=uint(s.phase==5)|(uint(optimal)<<1);
}
bool initializeCoordinateSampling(inout Runtime s)
{
    // Damage effects need the same sampled skill RNG hook before admission.
    // Keep the initial physical path explicit rather than accepting EV skills.
#ifdef PORTABLE_COORDINATE_SAMPLED_SKILLS
    for(uint row=0;row<s.count;row++)
    {
        uint kind=definition_kind(s.inputBase,row);
#ifdef PORTABLE_COORDINATE_SAMPLED_VITAL
        if(kind!=0&&kind!=2&&kind!=3&&kind!=4&&kind!=6&&kind!=7&&kind!=8&&kind!=24
#ifdef PORTABLE_COORDINATE_ORIGINAL_CLOCKS
            &&kind!=22 // Existing shared remaining skill-clock reduction.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_ROSTER
            &&kind!=1 // Existing named removal, recipient snapshot and callbacks.
#endif
#ifdef PORTABLE_COORDINATE_HEALING
            &&kind!=32 // Existing received-healing pool discharge, including lifecycle.
#endif
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
            &&((kind!=5&&kind!=25)||!burstControls(s)) // Existing shared cooldown/reentry handlers.
#endif
#ifdef PORTABLE_COORDINATE_SQUAD_MODE_STATE
            &&kind!=29 // Existing shared revival handler; mode flags survive on_down/on_revive.
#endif
        )return false; // Shared weapon/heal/reduce dispatch.
        if(kind==2||kind==6||kind==7||kind==8
#ifdef PORTABLE_COORDINATE_HEALING
            ||kind==32
#endif
        )s.quantityMask|=0x02000000U; // Reuse exact totals even without a damage skill.
#elif defined(PORTABLE_COORDINATE_SAMPLED_BURSTS)
        if(kind!=0&&kind!=3&&kind!=4&&kind!=24)return false; // Existing burst-gauge instant.
#else
        if(kind!=0&&kind!=3)return false;
#endif
        if(kind==3)
        {
#ifdef PORTABLE_COORDINATE_SAMPLED_BURSTS
            if(definition_damagePending(s.inputBase,row)>2)return false;
#else
            if(definition_damagePending(s.inputBase,row)!=0)return false;
#endif
            if(definition_damageFlags(s.inputBase,row)!=262144U)s.quantityMask|=0x02000000U;
        }
    }
#elif defined(PORTABLE_COORDINATE_SAMPLED_PARENT)
    for(uint row=0;row<s.count;row++)
    {
        uint kind=definition_kind(s.inputBase,row);
        if(kind!=0&&!(kind==3&&definition_damageFlags(s.inputBase,row)==262144U))return false;
    }
#else
    for(uint row=0;row<s.count;row++)if(definition_kind(s.inputBase,row)!=0)return false;
    if((s.quantityMask&0x01000000U)!=0)return false;
#endif
#ifdef PORTABLE_COORDINATE_MANUAL_ACTIONS
    if(manualControls(s))s.quantityMask|=0x02000000U;
#endif
    uint input=s.inputBase+P_ENEMY_TARGET_META_BASE;
    if(commands[input]!=1)return false;
    mtSeed(csRng(s),uint64_t(commands[input+1])|(uint64_t(commands[input+2])<<32));
#ifdef PORTABLE_COORDINATE_SAMPLED_PARENT
    initializeSampledParentDamage(s);
#ifdef PORTABLE_COORDINATE_MANUAL_ACTIONS
    initializeManualControls(s);
#ifdef PORTABLE_COORDINATE_COVER_POLICIES
    if(!initializeCoverPolicies(s))return false;
#ifdef PORTABLE_COORDINATE_SQUAD_ACTIONS
    if(!initializeSquadControls(s))return false;
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
    if(!initializeBurstControls(s))return false;
#endif
#endif
#endif
#endif
#ifdef PORTABLE_COORDINATE_SAMPLED_BURSTS
    for(uint i=0;i<CSB_WORDS;i++)results[s.resourceOutput+CSB_BASE+i]=0;
#endif
#endif
    return true;
}
uint64_t prepareCoordinateSampleBasis(inout Runtime s,uint who,Weapon w,uint64_t coefficient,uint64_t when,uint flags)
{
    uint h=csMeta(s),frame=s.resourceOutput+CP_FRAME,n=results[frame+2];
    uint64_t factors[9],intercept,explosion,pierce;uint sampled;
    sampleDamageFactorsForReach(s,who,f64Div(coefficient,f64FromI64(w.pellets)),when,factors,intercept,explosion,pierce,sampled,false,WORLD_PACKET_NORMAL(s,who),w.coreBonus,flags,w.fullChargeMult,w.optimal!=0,true);
    for(uint i=0;i<9;i++)storeNumber(h+20+i*2,factors[i]);storeNumber(h+38,intercept);
    results[h]=w.pellets*w.muzzles;results[h+1]=0;results[h+2]=1;results[h+3]=n;
    storeNumber(h+10,when);results[h+12]=w.pellets;results[h+13]=w.muzzles;results[h+54]=who;
    for(uint i=0;i<n*4;i++)results[h+CS_FRAME+i]=results[frame+8+i];
    return 0;
}
bool sampledCoordinateContains(inout Runtime s,uint slot,uint64_t px,uint64_t py,uint64_t grow)
{
    uint area=coordinateAreaRow(s,slot),r=cRow(coordinatePoolView(s),commands[area]-1);uint kind=commands[r+4];
    uint64_t co=ONE,si=0;if(kind==2)coordinateSinCosDegrees(cNumber(r+16),si,co);
    uint64_t d=coordinateShapeDistance(kind,cNumber(r+6),cNumber(r+8),cNumber(r+10),cNumber(r+12),cNumber(r+14),co,si,px,py);
    if(!f64Finite(d)){s.error=16;return false;}return coordinateShapeContains(d,grow);
}
uint64_t sampledCoordinateF3(inout Runtime s,bool critical,bool core)
{
    uint h=csMeta(s);uint64_t f3=ONE;
    if(critical)f3=f64Add(f3,actorNumber(h+42));
    if((results[h+46]&1)!=0)f3=f64Add(f3,uint64_t(0x3fe00000U)<<32);
    if((results[h+46]&2)!=0)f3=f64Add(f3,(uint64_t(0x3fd33333U)<<32)|uint64_t(0x33333333U));
    if(core)f3=f64Add(f3,actorNumber(h+44));return f3;
}
bool sampleCoordinatePhysicalPellet(inout Runtime s,Weapon w,uint who,uint64_t when,uint output,uint hit)
{
    uint h=csMeta(s),input=s.resourceOutput+CF_INPUT,n=results[h+3],at=csRow(s,hit);
    if(hit>=results[h]||hit>=CS_PELLETS||who!=results[h+54]){s.error=64;return true;}
    for(uint i=0;i<CS_ROW_WORDS;i++)results[at+i]=0;
    uint64_t ax=actorNumber(input+4),ay=actorNumber(input+6),radius=actorNumber(input+8),grow=actorNumber(input+10),k=actorNumber(input+12);
    uint coreAt=clShapeAt(input,CL_TARGETS);bool hasCore=results[input+3]!=0;
    bool angle=n!=0||hasCore&&(!f64Equal(actorNumber(coreAt+2),ax)||!f64Equal(actorNumber(coreAt+4),ay));
    uint64_t px,py,u,v;uint status;coordinateSamplePoint(csRng(s),ax,ay,radius,k,angle,px,py,u,v,status);
    if(status!=0){s.error=status;return true;}
    uint front=0;
    for(uint i=0;i<n;i++)
    {
        uint slot=results[h+CS_FRAME+i*4];
        if(front==0&&sampledCoordinateContains(s,slot,px,py,0))front=slot;
        if(f64Less(0,grow)&&sampledCoordinateContains(s,slot,px,py,grow))results[at+8+slot/32]|=1U<<(slot%32);
    }
    bool inCore=false;
    if(hasCore)
    {
        uint64_t d=coordinateShapeMax(0,f64Add(coordinateHypot(f64Add(px,actorNumber(coreAt+2)^F64_SIGN),f64Add(py,actorNumber(coreAt+4)^F64_SIGN)),actorNumber(coreAt+6)^F64_SIGN));
        if(!f64Finite(d)){s.error=64;return true;}
        inCore=coordinateShapeContains(d,0);
    }
    bool critical=f64Less(coordinateRandom53(csRng(s)),actorNumber(h+40)),reach=f64Less(0,grow),core=reach?inCore:front==0&&inCore;
    bool part=front!=0&&commands[actorBinding(s,front)]==1,body=front==0&&!inCore;
    results[at]=front;results[at+1]=uint(critical)|(uint(core)<<1)|(uint(part)<<2)|(uint(body)<<3)|(uint(reach)<<4);
    uint64_t factors[9];for(uint i=0;i<9;i++)factors[i]=actorNumber(h+20+i*2);
    factors[7]=sampledCoordinateF3(s,critical,false);factors[2]=sampledCoordinateF3(s,critical,core);
    storeNumber(at+2,damageFromFactors(s,factors,false));factors[2]=factors[7];
    storeNumber(at+4,damageFromFactors(s,factors,true));factors[8]=actorNumber(h+38);storeNumber(at+6,damageFromFactors(s,factors,true));
    storeNumber(h+4,part?ONE:uint64_t(0));storeNumber(h+6,body?ONE:uint64_t(0));
    sampleWorldFraction(s,who,critical?ONE:uint64_t(0),core?ONE:uint64_t(0));
    if(reach)
    {
        results[h+1]++;
        for(uint i=0;i<n;i++){uint slot=results[h+CS_FRAME+i*4];if((results[at+8+slot/32]&(1U<<(slot%32)))!=0)results[h+1]++;}
    }
    else results[h+1]++;
#ifdef PORTABLE_COORDINATE_SAMPLED_PARENT
    if((s.quantityMask&0x01000000U)!=0&&s.error==0)
    {
        PacketIntegerSum total;total.low=actorNumber(h+50);total.high=actorNumber(h+52);
        if(reach||front==0) {if(!packetIntegerAddAmount(total,actorNumber(at+2)))s.error=16;}
        if(reach)
        {
            for(uint i=0;i<n;i++)
            {
                uint e=h+CS_FRAME+i*4,slot=results[e],kind=results[e+1];
                if((results[at+8+slot/32]&(1U<<(slot%32)))!=0&&!packetIntegerAddAmount(total,actorNumber(at+(kind==1?4:6))))s.error=16;
            }
        }
        else if(front!=0&&!packetIntegerAddAmount(total,actorNumber(at+(commands[actorBinding(s,front)]==1?4:6))))s.error=16;
        storeNumber(h+50,total.low);storeNumber(h+52,total.high);
        if(hit+1==results[h]&&s.error==0)
        {
            uint status;uint64_t quantity=packetIntegerRatio(total,w.muzzles,status);
            if(status!=0)s.error=16;else storeNumber(h+14,quantity);
        }
    }
#endif
    return true;
}
void notifySampledCoordinateChargeTeam(inout Runtime s,uint who,uint count,uint64_t when,uint output)
{
    uint h=csMeta(s);
    for(uint i=0;i<count&&s.error==0;i++)
    {
        uint flags=results[csRow(s,i)+1];storeNumber(h+4,(flags&4)!=0?ONE:uint64_t(0));storeNumber(h+6,(flags&8)!=0?ONE:uint64_t(0));
        notifyCoordinatePhysicalTeam(s,who,when,output);
    }
}
void notifySampledCoordinateChargeFractions(inout Runtime s,uint who,uint count,uint64_t when,uint output)
{
    for(uint kind=0;kind<2;kind++)for(uint i=0;i<count&&s.error==0;i++)
    {
        uint flags=results[csRow(s,i)+1];sampleWorldFraction(s,who,(flags&1)!=0?ONE:uint64_t(0),(flags&2)!=0?ONE:uint64_t(0));notifyWorldFraction(s,who,kind,when,output);
    }
}
uint sampledCoordinateNotCore(inout Runtime s,uint who,uint muzzle)
{
    if(notCoreEnabled(s))
    {
        uint h=csMeta(s),pellets=results[h+12],core=0;
        for(uint i=0;i<pellets;i++)core+=uint((results[csRow(s,muzzle*pellets+i)+1]&2)!=0);
        storeNumber(s.resourceOutput+P_NOT_CORE_SHOT_BASE+who*2,f64Div(f64FromI64(core),f64FromI64(pellets)));
    }
    return notCoreContext(s,who);
}
uint64_t deliverSampledCoordinateShot(inout Runtime s,uint who,uint64_t legacy)
{
    uint h=csMeta(s);if(results[h+2]==0||s.error!=0)return legacy;results[h+2]=0;
    uint count=results[h],n=results[h+3];uint64_t when=actorNumber(h+10);
    s.frameAmmoActive[who]=0;s.physicalGaugeOwner=0;
    bool grouped=beginCoordinatePhysicalGroup(s,who,when,results[h+1]);
    for(uint hit=0;hit<count&&s.error==0;hit++)
    {
        uint at=csRow(s,hit),front=results[at],flags=results[at+1];bool reach=(flags&16)!=0;
        if(reach||front==0)coordinateGroupBodyPacket(s,who,actorNumber(at+2),when,false,grouped);
        for(uint i=0;i<n&&s.error==0;i++)
        {
            uint e=h+CS_FRAME+i*4,slot=results[e],targetKind=results[e+1];
            if(!(reach?(results[at+8+slot/32]&(1U<<(slot%32)))!=0:slot==front))continue;
            uint gen=coordinateLandingGeneration(s,slot,results[e+3]);uint64_t amount=actorNumber(at+(targetKind==1?4:6));bool extra=reach;
#define CF_PACKET_EXTRA extra
#include "coordinate_physical_target_delivery.slang"
#undef CF_PACKET_EXTRA
        }
    }
    if(grouped)finishCoordinatePhysicalGroup(s,who,when,s.resourceOutput);
    return legacy;
}
