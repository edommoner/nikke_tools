// Existing named-state presence and scoped query restoration, not a new state bank.
uint namedEnemyDescriptor(inout Runtime s,uint row)
{ return s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+24; }
void namedEnemyTrace(inout Runtime s,uint definition,uint order[128],uint count)
{
#ifdef PORTABLE_NAMED_ENEMY_DIAGNOSTIC
    uint head=s.resourceOutput+P_REVIVAL_BASE,index=results[head+6]++;
    if(index>=P_REVIVAL_TRACE_COUNT) { s.error=64;return; }
    uint at=s.resourceOutput+P_REVIVAL_TRACE_BASE+index*8;ActorBits bits=actorBitsEmpty();
    for(uint i=0;i<count;i++) actorBitsAdd(bits,order[i]);
    results[at]=0x4e455431U;results[at+1]=definition;
    for(uint i=0;i<4;i++) results[at+2+i]=bits.words[i];results[at+6]=count;results[at+7]=0;
#endif
}
bool namedEnemyPresent(inout Runtime s,uint row,uint target)
{
    uint at=namedEnemyDescriptor(s,row),previous=actorStatePushQuery(s,target==0?0:ACTOR_REF|target);
    bool present=false;actorNamedTargetStack(s,int(commands[at+1])-1,present,(commands[at+2]&1U)!=0);
    actorStatePopQuery(s,previous);return present;
}
bool validNamedEnemyDefinitions(inout Runtime s)
{
    bool named=false;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);if(d.kind==2) continue;
        uint at=namedEnemyDescriptor(s,row),tag=commands[at],name=commands[at+1],flags=commands[at+2];
        if(tag==0)
        { if(name!=0 || flags!=0 || commands[at+3]!=0 || d.damageRoute==11) return false;continue; }
        if(tag!=0x4e455231U || flags>3 || commands[at+3]!=0 || !actorStateEnabled(s) || s.combat==0 || !worldFrameEnabled(s)) return false;
        if(name==0 ? (flags!=2 || d.damageRoute==11) : (name>P_DEFINITIONS || d.damageRoute!=11 || d.damageCount!=128)) return false;
        if((flags&2U)!=0 && !(d.enemyBuff!=0 && (d.kind==0 || d.kind==4) || d.kind==3 && (d.damageFlags&H_DOT)!=0)) return false;
        if(name!=0 && !(d.enemyBuff!=0 || d.kind==3 || (d.kind==1 || d.kind==15) && d.target==2)) return false;
        named|=name!=0;
    }
#ifdef PORTABLE_NAMED_ENEMY_DIAGNOSTIC
    if(named)
    {
        if(alliedRandomEnabled(s)) return false;
        for(uint row=0;row<s.count;row++) if(definition_kind(s.inputBase,row)==29) return false;
        results[s.resourceOutput+P_REVIVAL_BASE+6]=0;
        for(uint i=0;i<P_REVIVAL_TRACE_COUNT*8;i++) results[s.resourceOutput+P_REVIVAL_TRACE_BASE+i]=0;
    }
#endif
    return true;
}
