// World descriptor provider selected by the common executor's layout variant.
#include "world_schedule.slang"
static const uint WF_INPUT=P_WORLD_FRAME_INPUT_BASE, WF_PAYLOAD=P_WORLD_FRAME_PAYLOAD_BASE, WF_OUTPUT=P_WORLD_FRAME_OUTPUT_BASE;
static const uint WF_TARGETS=P_WORLD_FRAME_TARGET_BASE, WF_HITS=P_WORLD_FRAME_HIT_BASE;
bool worldFrameEnabled(inout Runtime s) { return commands[s.inputBase+WF_INPUT]!=0; }
bool scheduledArgument(uint arg) { return (arg&0x80000000U)!=0; }
// Only product entries admit native external-caster definitions. All recipients
// are selected by an actual incoming landing, never by a CPU hit schedule.
bool worldBossDebuffDefinition(inout Runtime s,uint row)
{
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
    uint head=s.inputBase+WF_INPUT,count=commands[head+1];
    if(commands[head]!=0x57533031U||count==0||count>32) return false;
    for(uint node=0;node<count;node++)
    {
        uint p=s.inputBase+WF_PAYLOAD+node*16,first=commands[p+4],n=commands[p+5];
        if(commands[p]==32&&commands[p+6]==0x42444631U&&first>0&&n>0&&n<=32&&first-1+n<=s.count&&row>=first-1&&row<first-1+n) return true;
    }
#endif
    return false;
}
bool validWorldBossDebuff(inout Runtime s,uint row,Definition d)
{
    bool scalar=d.stat==S_atk_pct||d.stat==S_enemy_def_down_pct&&d.alliedFlags==1||d.stat==S_crit_rate||d.stat==S_crit_dmg||d.stat==S_accuracy_pct||d.stat==S_attack_speed_pct||d.stat==S_reload_speed_pct||d.stat==S_charge_speed_pct||d.stat==S_max_ammo_pct||d.stat==S_atk_dmg_pct||d.stat==S_heal_received_pct;
    bool marker=d.stat==S_stun&&f64Equal(d.value,ONE)||d.stat==S_cover_disabled&&f64Zero(d.value);
    return worldBossDebuffDefinition(s,row)&&d.owner==5&&d.kind==0&&d.enemyBuff==0&&d.recipients==0&&d.flags==0&&d.conditionCount==0&&d.triggerCount==1
        &&commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS]==0&&d.healthScaling==0&&(d.alliedFlags==0||d.alliedFlags==1&&d.stat==S_enemy_def_down_pct||d.alliedFlags==2&&d.stat==S_received_dmg_pct)&&d.quantityFlags==0&&d.damageFlags==0&&d.lazyGroup==0&&d.mergeEligible==0
        &&d.alias==-1&&d.group==row&&d.budget==-1&&f64Zero(d.interval)&&d.polarity>=2&&d.polarity<=3&&f64Finite(d.value)
        &&(scalar&&f64Less(d.value,0)||d.stat==S_received_dmg_pct&&f64Less(0,d.value)||marker);
}
uint incomingCommandAddress(inout Runtime s,uint arg)
{
#ifdef PORTABLE_ADD_ATTACK_BATTLE
    if((arg&0xc0000000U)==0xc0000000U)return s.inputBase+ADB_BASE+ADB_ROW_BASE+(arg&31U)*ADB_ROW_WORDS+8;
#endif
    return s.inputBase+(scheduledArgument(arg)?WF_PAYLOAD+(arg&31U)*16:P_COMMAND_BASE+arg*8);
}
uint incomingDamageAddress(inout Runtime s,uint arg)
{ return scheduledArgument(arg)?incomingCommandAddress(s,arg)+8:s.inputBase+P_INCOMING_BASE+arg*P_INCOMING_WORDS; }
uint enemyRuleAddress(inout Runtime s,uint arg)
{ return scheduledArgument(arg)?incomingCommandAddress(s,arg)+12:s.inputBase+P_ENEMY_TARGET_COMMAND_BASE+arg*4; }
uint enemyQueryAddress(inout Runtime s,uint arg)
{ return s.resourceOutput+(scheduledArgument(arg)?WF_TARGETS+results[s.resourceOutput+WF_OUTPUT+8]*8:P_ENEMY_TARGET_QUERY_BASE+arg*8); }
uint incomingRecordAddress(inout Runtime s,uint arg,uint origin,uint member,bool primary,uint legacy)
{
    if(!scheduledArgument(arg)) return legacy;
    uint head=s.resourceOutput+WF_OUTPUT,count=results[head+6];
    if(count>=2048) { s.error=2;return 0; }
    results[head+6]=count+1;uint relative=WF_HITS+count*16;
    results[s.resourceOutput+relative+2]=1U|(primary?2U:0U)|(origin<<2)|(results[head+8]<<5);
    return relative;
}
WorldSchedule frameSchedule(inout Runtime s)
{ WorldSchedule w;w.input=s.inputBase+WF_INPUT;w.output=s.resourceOutput+WF_OUTPUT;w.count=commands[w.input+1];w.error=s.error;return w; }
[noinline]
bool initializeWorldFrame(inout Runtime s)
{
    for(uint j=0;j<65536;j++) results[s.resourceOutput+WF_OUTPUT+j]=0;
    uint start=s.inputBase+WF_INPUT;
    if(commands[start]==0)
    { for(uint j=0;j<2832;j++) if(commands[start+j]!=0) return false;return true; }
    if(commands[start]!=0x57533031 || s.combat==0 || commands[start+2]!=0 || commands[start+3]!=(s.clockMode!=0?1U:2U) || commands[start+4]!=1 || commands[start+5]!=0) return false;
    uint64_t through=wsLoad(start+6);
    if(!f64Finite(through) || f64Less(through,0) || f64Less(f64FromI64(180),through)) return false;
    for(uint j=9;j<16;j++) if(commands[start+j]!=0) return false;
    for(uint j=2064;j<2320;j++) if(commands[start+j]!=0) return false;
    WorldSchedule w=frameSchedule(s);if(!wsValidate(w)) return false;
    bool spawnNotice=false;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    spawnNotice=actorPoolsTargetSpawn(s);
#endif
    for(uint n=0;n<w.count;n++) for(uint end=0;end<2;end++)
    {
        uint d=start+16+n*64,count=commands[d+12+end],packed=commands[d+14+end];
        for(uint i=0;i<count;i++) if(((packed>>(i*3))&7)==2) spawnNotice=true;
    }
    if(commands[start+8]>P_DEFINITIONS || (commands[start+8]!=0)!=spawnNotice) return false;
    bool reached=false;
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+step*8;
        if(commands[at]==4) return false;
        if(commands[at]==24)
        { uint64_t t=loadNumber(at+1);if(!f64Finite(t)||f64Less(t,0)||f64Less(through,t)) return false;if(f64Equal(t,through)) reached=true; }
    }
    if(!COUNTER_WORLD_LITERAL(s,through,reached)) return false;
    for(uint n=0;n<32;n++)
    {
        uint p=s.inputBase+WF_PAYLOAD+n*16,d=start+16+n*64;
        if(n>=w.count || commands[d+6]==0) { for(uint j=0;j<16;j++) if(commands[p+j]!=0) return false;continue; }
        if((commands[d+1]&2)!=0 || commands[p]!=32 || commands[p+1]!=0 || commands[p+2]!=0 || commands[p+3]>1) return false;
        if(commands[p+4]!=0||commands[p+5]!=0||commands[p+6]!=0||commands[p+7]!=0)
        {
            uint first=commands[p+4],n=commands[p+5],bound=commands[p+7];
            if(first==0||n==0||n>32||first-1+n>s.count||commands[p+6]!=0x42444631U||n<32&&(bound>>n)!=0) return false;
            for(uint row=first-1;row<first-1+n;row++) if(!validWorldBossDebuff(s,row,readDefinition(s.inputBase,row))) return false;
        }
        uint64_t attack=loadNumber(p+8),coeff=loadNumber(p+10);
        if(!f64Finite(attack)||f64Less(attack,0)||f64Less(FOREVER,attack)||!f64Finite(coeff)||f64Less(coeff,0)||f64Less(f64FromI64(1000000),coeff)) return false;
        uint rule=commands[p+12],count=commands[p+13],slots=commands[p+14],ignore=commands[p+15];
        if(rule>3 || ignore>1 || rule==0 && (count!=0||slots!=0||ignore!=0) || rule!=0 && (count==0||count>5)) return false;
        if(rule!=1 && slots!=0) return false;
        if(rule==1)
        {
            uint previous=0;
            for(uint i=0;i<5;i++) { uint encoded=(slots>>(3*i))&7;if(i<count ? encoded==0||encoded>5||encoded<=previous : encoded!=0) return false;previous=encoded; }
            if((slots>>15)!=0) return false;
        }
    }
    // No actor-cleared input is accepted by this direct-attack coupling stage.
    for(uint n=0;n<w.count;n++) if((commands[start+16+n*64+1]&2)!=0)
    {
#ifdef PORTABLE_WORLD_ACTOR_POOLS
        if(!actorPoolsClearedAllowed(s,n)) return false;
#else
        return false;
#endif
    }
    return commands[s.inputBase+P_ENEMY_TARGET_META_BASE]==1;
}
