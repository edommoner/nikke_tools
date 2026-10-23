// Codec and late recipient binding only. Effect quantities, binary64 damage,
// hit multiplicity, gauge, Actor HP, counter completion and healing are shared.
bool worldSkillsEnabled(inout Runtime s)
{ return targetCountersEnabled(s)&&(commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==7||worldPendingEnabled(s)); }
#ifdef PORTABLE_WORLD_PROJECTILE
bool worldSkillNeedsReach(inout Runtime s,Definition d)
{
    if((d.damageFlags&65536U)!=0) return true;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
    {
        uint at=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8;
        if((commands[at]==1||commands[at]==2)&&commands[at+1]!=0&&results[actorPoolAt(s,slot)+1]!=0) return true;
    }
    return false;
}
uint64_t sampleWorldPartSkill(inout Runtime s,Definition d,uint64_t coefficient,uint64_t when,out uint64_t partAmount,out uint64_t interruptAmount,out uint interruptReach)
{
    bool marker=(d.damageFlags&65536U)!=0,hasParts=commands[s.inputBase+P_WORLD_TEAM_INPUT_BASE+3]!=0,dynamicParts=false;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
    {
        if(commands[actorBinding(s,slot)]!=1||results[actorPoolAt(s,slot)+1]==0) continue;
        hasParts=true;uint at=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8;
        if(commands[at]==1&&commands[at+1]!=0) dynamicParts=true;
    }
    uint flags=d.damageFlags&~H_PART;if(marker&&hasParts&&!dynamicParts) flags|=H_PART;
    bool normal=d.damageNormal!=0;if(normal&&(s.attackContext[d.owner]&4)!=0) flags|=H_EXPLOSION;uint64_t coreBonus=normal?s.coreDamageBonus[d.owner]:s.coreBonus;
    uint64_t factors[9],interceptFactor,explosionRange,pierceRange;uint sampledFlags;
    sampleDamageFactorsForReach(s,d.owner,coefficient,when,factors,interceptFactor,explosionRange,pierceRange,sampledFlags,true,normal,coreBonus,flags,ONE,normal&&(s.attackContext[d.owner]&1)!=0,false,d._wireRow);
    uint64_t threshold=f64Add(HUNDRED,uint64_t(0xbe112e0b)<<32|uint64_t(0xe826d695));
    bool explosion=(flags&H_EXPLOSION)!=0||normal&&(s.attackContext[d.owner]&4)!=0;
    interruptReach=explosion?(!f64Less(explosionRange,threshold)?4U:3U):(flags&H_PIERCE)!=0?(!f64Less(pierceRange,threshold)?2U:1U):0U;
    uint partReach=marker?5U:interruptReach;bool part=false,interrupt=false;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
    {
        uint at=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8;
        if(results[actorPoolAt(s,slot)+1]==0||commands[at+1]==0) continue;
        if(commands[at]==1&&commands[at+1]<=partReach) part=true;
        if(commands[at]==2&&commands[at+1]<=interruptReach) interrupt=true;
    }
    uint64_t amount=damageFromFactors(s,factors,false);partAmount=0;interruptAmount=0;
    if(part&&s.error==0) partAmount=damageFromFactors(s,factors,true);
    if(interrupt&&s.error==0) { factors[8]=interceptFactor;interruptAmount=damageFromFactors(s,factors,true); }
    return amount;
}
#endif
#ifdef PORTABLE_WORLD_PROJECTILE
#include "world_interrupt_runtime.slang"
#endif
bool validWorldSkillDefinition(inout Runtime s,uint row,Definition d)
{
    if(d.enemyBuff!=0||!validEnemyRoute(s.inputBase,d.damageRoute)||d.damageCount==0||d.damageCount>128||d.damageHits>256||d.damagePending!=0&&!worldPendingEnabled(s)||(d.periodicFlags!=0||!f64Zero(d.interval))&&!worldPeriodicClock(s,d)||d.healthScaling!=0||referenceScaleMode(s,row)!=0&&!(worldPendingEnabled(s)&&d.damagePending!=0&&referenceScaleMode(s,row)==1)&&!(worldPeriodicClock(s,d)&&referenceScaleMode(s,row)==3)) return false;
#ifdef PORTABLE_PARENT_FIXED_DAMAGE
    if(!validParentFixed(s,row,d)) return false;
#endif
    if((d.damageFlags&~uint(
#ifdef PORTABLE_PARENT_FIXED_DAMAGE
        262144U|
#endif
        1|2|4|8|16|32|64|128|256|512|1024|2048|4096|8192|16384|65536|H_NAMED_SKILL))!=0||(d.damageFlags&H_DOT)!=0&&!worldPeriodicClock(s,d)||d.damageNormal>1) return false;
#ifndef PORTABLE_WORLD_PROJECTILE
    if((d.damageFlags&(H_PART|65536U))!=0) return false;
#else
    if((d.damageFlags&H_PART)!=0&&(d.damageFlags&65536U)==0) return false;
    if((d.damageFlags&65536U)!=0&&
#ifdef PORTABLE_FULL_BURST_LANDING
        d.damagePending==1
#else
        d.damagePending!=0
#endif
    ) return false;
#endif
#ifndef PORTABLE_WORLD_PROJECTILE
    // Earlier world tiers have no reach receipt or private interrupt executor.
    if((d.damageFlags&(H_PIERCE|H_EXPLOSION))!=0||d.damageNormal!=0&&(s.attackContext[d.owner]&4)!=0)
        for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]==1||commands[actorBinding(s,slot)]==6) return false;
#endif
    if(d.damageRoute==3)
        for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]==5&&commands[actorPoolDef(s,slot)]==3) return false;
    return true;
}
bool validWorldSkillReceipt(inout Runtime s,LandingReceipt r,bool legacy)
{
    if(!worldSkillsEnabled(s)) return legacy;
    bool accumReceipt=false;
#ifdef PORTABLE_DAMAGE_ACCUM
    accumReceipt=r.row<s.count && definition_kind(s.inputBase,r.row)==34;
#endif
    return r.row<s.count&&(definition_kind(s.inputBase,r.row)==3||accumReceipt)&&WORLD_PERIODIC_VALID(s,r,r.mask==0xffffffffU)&&r.hit>=1&&r.hit<=256&&r.hits>=r.hit&&r.hits<=256&&r.depth>=1&&r.depth<=P_DEPTH&&r.epoch<=0x7fffffff&&r.interruptReach<=4&&(r.interruptReach!=0||f64Zero(r.interruptAmount))&&f64Finite(r.interruptAmount)&&!f64Less(r.interruptAmount,0)&&f64Finite(r.amount)&&(accumReceipt||!f64Less(r.amount,0))&&f64Finite(r.when)&&f64Finite(r.partAmount)&&!f64Less(r.partAmount,0);
}
void storeWorldSkillReceipt(inout Runtime s,uint at,LandingReceipt r)
{
    if(!worldSkillsEnabled(s)) { storeLandingReceipt(at,r);return; }
    results[at]=r.row;results[at+1]=r.hit|(r.hits<<9)|(r.depth<<18);
    storeNumber(at+2,r.amount);storeNumber(at+4,r.when);results[at+6]=r.epoch;results[at+7]=0;WORLD_PERIODIC_STORE(s,at,r)
#ifdef PORTABLE_WORLD_PROJECTILE
    storeSkillPartAmount(at,r.partAmount);
    storeWorldSkillReachPacket(s,at,r);
#endif
}
LandingReceipt loadWorldSkillReceipt(uint at)
{
    LandingReceipt r={};uint counts=results[at+1];r.row=results[at];r.mask=0xffffffffU;
    r.hit=counts&511;r.hits=(counts>>9)&511;r.depth=counts>>18;r.amount=actorNumber(at+2);r.when=actorNumber(at+4);r.epoch=results[at+6];WORLD_PERIODIC_LOAD(r,at)
#ifdef PORTABLE_WORLD_PROJECTILE
    r.partAmount=loadSkillPartAmount(at);
    loadWorldSkillReachPacket(r,at);
#endif
    return r;
}
uint worldSkillHead(inout Runtime s) { return s.resourceOutput+P_WORLD_SKILL_HEAD_BASE; }
void initializeWorldSkills(inout Runtime s)
{
    if(!worldSkillsEnabled(s)) return;
#ifdef PORTABLE_DAMAGE_ACCUM
    if(damageAccumEnabled(s)) { results[damageAccumHeader(s)]=0;results[damageAccumHeader(s)+1]=0; }
#endif
    WORLD_PERIODIC_INIT(s) for(uint i=P_WORLD_SKILL_HEAD_BASE;i<P_WORLD_SKILL_TRACE_BASE+128*48;i++) results[s.resourceOutput+i]=0;
    results[worldSkillHead(s)]=0x57534b31;
}
void logWorldSkill(inout Runtime s,LandingReceipt r,uint set,uint64_t share,uint64_t when)
{
    uint h=worldSkillHead(s),n=results[set];results[h+2]=max(results[h+2],n);
    if(s.traceTotal==0x7fffffff) { s.error=2;return; }s.traceTotal++;
    if(s.traceMode!=1)
    {
#ifdef PORTABLE_WORLD_PROJECTILE_SKILL_DIAGNOSTIC
        if(definition_owner(s.inputBase,r.row)!=0) return;
#else
        return;
#endif
    }
    uint index=results[h+1];if(index==128) { s.error=8;return; }results[h+1]++;
    uint at=s.resourceOutput+P_WORLD_SKILL_TRACE_BASE+index*48;
    results[at]=r.row;results[at+1]=r.hit;results[at+2]=r.hits;results[at+3]=n;
    storeNumber(at+4,r.when);storeNumber(at+6,when);storeNumber(at+8,r.amount);storeNumber(at+10,share);
    for(uint i=0;i<4;i++) results[at+12+i]=results[set+1+i];
    for(uint i=0;i<n;i++) { uint slot=results[set+8+i*4];results[at+16+i/4]|=(slot+1)<<((i%4)*8); }
}
// One Actor landing lifecycle for queued direct skills and immediate pending packets.
[noinline]
bool landWorldSkillReceipt(inout Runtime s,LandingReceipt r,uint64_t when,uint output)
{
    Definition d=readDefinition(s.inputBase,r.row);
    uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return false; }
    WORLD_PERIODIC_CAPTURE_PACKET(s,r,index,actorSetCapture(s,33,index,d.damageRoute,d.damageCount,0,d.owner NAMED_ENEMY_ARGUMENT(r.row));)if(s.error!=0) return false;
    uint set=actorPoolSet(s,index),n=results[set];uint64_t share=r.amount;
    if((d.damageFlags&H_SPLIT)!=0&&n>1)
    {
        uint status;uint64_t weighted=f64Mul(r.amount,f64Div(ONE,f64FromI64(n)));
        uint64_t rounded=f64ToI64(weighted,0,status);if(status!=0) { s.error=16;return false; }share=f64FromI64(rounded);
    }
    logWorldSkill(s,r,set,share,when);
    for(uint i=0;i<n&&s.error==0;i++)
    {
        uint entry=set+8+i*4,slot=results[entry],generation=results[entry+1];
        if(results[actorPoolAt(s,slot)]!=generation||results[actorPoolAt(s,slot)+1]==0) continue;
        if(slot==0&&!worldOverlayLand(s,d.owner,0,share,false)) continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,d.owner,ACTOR_REF|slot,share);
        uint receipt=actorPoolHead(s)+18;
        if(results[receipt]!=0&&s.error==0)
        {
            uint64_t amount=commands[actorBinding(s,slot)]==5 ? actorNumber(receipt+2) : share;
            uint previous=results[counterHead(s)+11];// Canonical core_damage tags are WEAPON; normal_attack overrides them
            // with normal_skill, which is SKILL. The normalized descriptor
            // carries both facts without backend-specific string routing.
            results[counterHead(s)+11]=WORLD_PERIODIC_FAMILY(s,d,((d.damageFlags&H_CORE)!=0&&d.damageNormal==0) ? 0 : 1);
            counterPhysicalPacket(s,d.owner,slot,generation,amount,results[receipt+1]!=0,when,output);
            results[counterHead(s)+11]=previous;
            if((s.healthMask&64)!=0&&s.error==0) dispatch(s,17,0,d.owner,0,when,output,share);
#ifdef PORTABLE_DAMAGE_ACCUM
            if(damageAccumEnabled(s) && slot==0 && s.error==0) dispatch(s,39,0,d.owner,0,when,output,share);
#endif
#ifdef PORTABLE_WORLD_PROJECTILE
            if(slot==0&&!f64Zero(r.partAmount)&&s.error==0)
            {
                uint family=results[counterHead(s)+11];results[counterHead(s)+11]=WORLD_PERIODIC_FAMILY(s,d,((d.damageFlags&H_CORE)!=0&&d.damageNormal==0)?0:1);
                deliverCounterPartGroup(s,d.owner,ACTOR_REF,when,output,(d.damageFlags&65536U)!=0?5U:r.interruptReach,r.partAmount);
                results[counterHead(s)+11]=family;
            }
            if(slot==0&&r.interruptReach!=0&&!f64Zero(r.interruptAmount)&&s.error==0)
                deliverWorldInterruptGroup(s,d.owner,when,output,r.interruptReach,r.interruptAmount);
#endif
            uint out=worldSkillHead(s);if(results[out+3]==0x7fffffff) { s.error=2;break; }results[out+3]++;
        }
    }
    results[set+5]=0;results[actorPoolHead(s)+7]--;
    return s.error==0;
}
[noinline]
void drainWorldSkills(inout Runtime s,uint64_t when,uint output)
{
    uint h=landingHeader(s);if(s.landingPolicy==0||results[h]==results[h+1]) return;
    if(results[h+4]==0x7fffffff) { s.error=2;return; }results[h+4]++;
    uint saved=s.target,work=0;
    while(results[h+1]<results[h]&&s.error==0)
    {
        if(++work>4096) { s.error=4;break; }
        LandingReceipt r=loadWorldSkillReceipt(landingAddress(s,results[h+1]++));
        if(!validWorldSkillReceipt(s,r,false)) { s.error=64;break; }
        if(!landWorldSkillReceipt(s,r,when,output)) break;
        if(results[h+3]==0x7fffffff) { s.error=2;break; }results[h+3]++;
    }
    if(s.error==0) { results[h]=0;results[h+1]=0; }s.target=saved;
}

#ifdef PORTABLE_WORLD_PENDING_SKILLS
void landWorldPending(inout Runtime s,Definition d,uint row,uint index,uint hit,uint64_t when,uint output)
{
    LandingReceipt r={};r.row=row;r.mask=0xffffffffU;r.hit=hit+1;r.hits=d.damageHits;r.depth=1;r.amount=pendingBatchAmount(s,index);r.when=when;r.epoch=s.enemyEpoch;
    uint saved=s.target;landWorldSkillReceipt(s,r,when,output);s.target=saved;
}
#endif

#ifdef PORTABLE_WORLD_PERIODIC
#include "world_periodic_runtime.slang"
#ifdef PORTABLE_WORLD_INITIAL_SPAWN
#include "world_spawn_runtime.slang"
#ifdef PORTABLE_WORLD_FRACTION
#include "world_fraction_runtime.slang"
#ifdef PORTABLE_WORLD_TEAM
#include "world_team_runtime.slang"
#ifdef PORTABLE_WORLD_CHARGE_CONTROL
#include "world_charge_control_runtime.slang"
#endif
#endif
#endif
#endif
#else
bool worldPeriodicClock(inout Runtime s,Definition d) { return false; }
#endif

#ifdef PORTABLE_PARENT_FIXED_DAMAGE
#include "parent_fixed_runtime.slang"
#endif
