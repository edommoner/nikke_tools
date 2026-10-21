// Native team-hit lowering supplies immutable attacker-bound definitions.
// This adapter owns only team counters, source-owner predicates and fractions.
uint teamBindingOwner(uint input,uint row)
{ return commands[input+P_WORLD_TEAM_INPUT_BASE+8+row*2]; }
uint teamBudgetRow(uint input,uint row)
{ uint key=commands[input+P_WORLD_TEAM_INPUT_BASE+9+row*2];return key==0?row:key-1; }
bool teamActivationContext(uint input,uint row,bool runtime,uint event)
{ return !runtime&&teamBindingOwner(input,row)!=0&&(event==44||event==45); }
uint teamConditionOwner(uint input,uint row,bool runtime,uint event,uint fallback)
{ return teamActivationContext(input,row,runtime,event)?teamBindingOwner(input,row)-1:fallback; }
[noinline]
uint64_t teamConditionTarget(inout Runtime s,uint row,int name,out bool present)
{
    uint previous=actorStatePushQuery(s,actorPhysicalTarget(s,teamBindingOwner(s.inputBase,row)-1,0));uint64_t count=actorNamedTargetStack(s,name,present);actorStatePopQuery(s,previous);return count;
}
bool teamAdditionalCondition(uint kind)
{ return kind==C_HP_ABOVE||kind==C_HP_BELOW||kind==C_HP_MAX||kind==C_PROB||kind==C_FULL||kind==C_NOT_FULL; }
bool validTeamAdditionalCondition(uint at,uint kind,uint64_t arg)
{
    if(commands[at+1]!=0||!f64Finite(arg)) return false;
    if(kind==C_HP_MAX||kind==C_FULL||kind==C_NOT_FULL) return f64Zero(arg);
    if(kind==C_PROB) return !f64Less(arg,0)&&!f64Less(ONE,arg);
    return !f64Less(arg,0)&&!f64Less(HUNDRED,arg);
}
[noinline]
void initializeWorldTeam(inout Runtime s)
{
    s.teamEvent=0;if(!worldTeamEnabled(s)) { s.error=64;return; }
    uint input=s.inputBase+P_WORLD_TEAM_INPUT_BASE;
    if(commands[input]!=0x57544831||commands[input+1]!=1||commands[input+2]!=s.count||commands[input+3]>1) { s.error=64;return; }
    for(uint j=4;j<8;j++) if(commands[input+j]!=0) { s.error=64;return; }
    for(uint row=0;row<P_DEFINITIONS;row++)
    {
        uint origin=commands[input+8+row*2],key=commands[input+9+row*2];
        if(row>=s.count) { if(origin!=0||key!=0) s.error=64;continue; }
        if(origin>5||key>s.count||(origin==0)!=(key==0)) { s.error=64;return; }
        Definition d=readDefinition(s.inputBase,row);bool team=false;
        for(uint slot=0;slot<d.triggerCount;slot++)
        {
            uint event=commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8];
            if(event==44||event==45) team=true;
            else if(origin!=0) { s.error=64;return; }
        }
        if(team!=(origin!=0)) { s.error=64;return; }
        if(origin==0) continue;
        uint first=key-1;
        if(first+5>s.count||row<first||row>=first+5||d.owner!=row-first||!f64Zero(d.interval)||(d.kind!=0&&d.kind!=2&&d.kind!=3&&d.kind!=4&&d.kind!=5&&d.kind!=6&&d.kind!=7&&d.kind!=8&&d.kind!=24&&!WORLD_RELOAD_FORCE_KIND(d.kind))) { s.error=64;return; }
        for(uint member=first;member<first+5;member++) if(commands[input+8+member*2]!=origin||commands[input+9+member*2]!=key||definition_owner(s.inputBase,member)!=member-first) { s.error=64;return; }
        Definition root=readDefinition(s.inputBase,first);
        if(d.name!=root.name||d.kind!=root.kind||d.stat!=root.stat||d.budget!=root.budget||d.triggerCount!=root.triggerCount||commands[input+8+first*2]!=origin||commands[input+9+first*2]!=key) { s.error=64;return; }
        for(uint slot=0;slot<d.triggerCount*8;slot++) if(commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot]!=commands[s.inputBase+P_EVENT_BASE+first*P_EVENT_WORDS+slot]) { s.error=64;return; }
    }
    for(uint i=P_WORLD_TEAM_STATE_BASE;i<P_WORLD_TEAM_TRACE_BASE+P_WORLD_TEAM_TRACE_COUNT*8;i++) results[s.resourceOutput+i]=0;
    results[s.resourceOutput+P_WORLD_TEAM_HEAD_BASE]=0x57544831; WORLD_CONTROL_INIT(s)
}
[noinline]
void notifyWorldTeam(inout Runtime s,uint who,uint64_t when,uint output)
{
    uint kind=WORLD_PROJECTILE_PARTS(s,commands[s.inputBase+P_WORLD_TEAM_INPUT_BASE+3])==1?0:1;
    uint state=s.resourceOutput+P_WORLD_TEAM_STATE_BASE+who*4,head=s.resourceOutput+P_WORLD_TEAM_HEAD_BASE;
    uint64_t frac=f64Add(ONE,actorNumber(s.resourceOutput+P_WORLD_FRACTION_STATE_BASE+who*8+6)^F64_SIGN),value=actorNumber(state+kind*2);bool fired=false;
    if(!f64Finite(frac)||f64Less(frac,0)||f64Less(ONE,frac)) { s.error=16;return; }
    if(!f64Less(frac,ONE)) fired=true;
    else if(f64Less(0,frac))
    {
        results[head+4]|=1U<<(who*2+kind);value=f64Add(value,frac);
        if(!f64Less(value,ONE)) { value=f64Add(value,ONE^F64_SIGN);fired=true; }
        storeNumber(state+kind*2,value);
    }
    uint count=results[head+1];WORLD_ROSTER_TRACE_BEGIN(s,head,count,P_WORLD_TEAM_TRACE_COUNT,5)
    uint at=s.resourceOutput+P_WORLD_TEAM_TRACE_BASE+count*8;results[head+1]=count+1;
    results[at]=44+kind;results[at+1]=who|(uint(fired)<<3)|(((results[head+4]>>(who*2+kind))&1U)<<4);
    storeNumber(at+2,when);storeNumber(at+4,frac);storeNumber(at+6,value);WORLD_ROSTER_TRACE_END
    if(fired)
    {
        if(results[head+2+kind]==0x7fffffff) { s.error=2;return; }
        results[head+2+kind]++;uint previous=s.target;s.target=0;dispatch(s,0,44+kind,who,0,when,output);s.target=previous;
    }
}
