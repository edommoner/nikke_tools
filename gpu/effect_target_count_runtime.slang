// Named capacities are separate from numeric damage stats and marker stacks.
static const uint TC_STAT=93U;
bool validTargetCountDefinitions(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);if(d.stat!=TC_STAT)continue;
        uint64_t value=d.value;uint status;uint64_t integer=f64ToI64(value,1U,status);
        if(d.kind!=0||d.enemyBuff!=0||d.targetName<0||d.targetName>=int(P_DEFINITIONS)||d.lazyGroup!=0||d.queryResolve!=0||
           d.alliedFlags!=0||d.healthScaling!=0||d.quantityFlags!=0||d.damageFlags!=0||
           !f64Finite(value)||f64Less(value,0)||status!=0||integer>2147483647UL||!f64Equal(value,f64FromI64(integer))||
           !f64Zero(d.interval))return false;
#ifdef PORTABLE_EFFECT_TARGET_COUNT_SHOTS
        if(s.combat==0||d.bulletDuration==0)return false;
#else
        if(d.bulletDuration!=0)return false;
#endif
        uint plan=s.inputBase+P_RECIPIENT_BASE+row*8;
        if(commands[plan]!=0&&commands[plan]!=1
#ifdef PORTABLE_NAMED_RANGE_BATTLE
           &&commands[plan]!=12
#endif
        )return false;
    }
#ifdef PORTABLE_EFFECT_TARGET_COUNT_SHOTS
    return initializeTargetCountShotPlan(s);
#else
    return true;
#endif
}
bool namedTargetCountValue(inout Runtime s,uint who,uint name,uint base,uint limit,uint64_t when,out uint capacityOut,out uint64_t total)
{
    capacityOut=0;total=0;
    if(!f64Finite(when)||f64Less(when,0)||who>=5||name>=P_DEFINITIONS||limit==0||limit>2147483647U||base>limit)return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition d=residentDefinition(s,slot);
        if(d.stat!=TC_STAT||d.targetName!=int(name)||s.alive[slot]==0||!f64Less(when,s.end[slot])||
           (s.activeRecipients[slot]&(1U<<who))==0||!basicConditions(s,slot,when,true,who))continue;
        total=f64Add(total,recipientValue(s,slot,who));
    }
    uint64_t capacity=f64Add(f64FromI64(base),total);uint status;uint64_t integer=f64ToI64(capacity,1U,status);
    if(!f64Finite(capacity)||f64Less(capacity,0)||f64Less(f64FromI64(limit),capacity)||status!=0||
       !f64Equal(capacity,f64FromI64(integer)))return false;
    capacityOut=uint(integer);return true;
}
bool targetCountCommand(inout Runtime s,uint at,uint64_t when,uint output,inout uint queries)
{
    uint who=commands[at+3],name=commands[at+4],base=commands[at+5],limit=commands[at+6],index=commands[at+7],capacity;
    uint64_t total;
    if(index>=P_COMMANDS||!namedTargetCountValue(s,who,name,base,limit,when,capacity,total))return false;
    uint dst=output+P_QUERY_BASE+index*P_QUERY_WORDS;for(uint j=0;j<P_QUERY_WORDS;j++)results[dst+j]=0;
    storeNumber(dst,when);results[dst+2]=who;results[dst+3]=name;results[dst+4]=base;results[dst+5]=limit;
    results[dst+6]=capacity;storeNumber(dst+7,total);results[dst+9]=0x54435131U;queries=max(queries,index+1);return true;
}
