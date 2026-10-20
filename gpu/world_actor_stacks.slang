// Wide receiver matching only;the shared stack loop owns numeric conversion,
// clamping,lifetime refresh,and deferred notices for both GPU backends.
bool actorStacksEnabled(inout Runtime s)
{ return actorFieldsEnabled(s)&&commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+4]==0x57543031; }
bool actorStackBlocked(inout Runtime s,uint target)
{
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];
        if(s.alive[row]!=0&&s.lazyPending[row]==0&&(definition_flags(s.inputBase,s.carrierDefinition[row])&8)!=0&&actorRecipientMember(s,row,target==0?0:ACTOR_REF|target)) return true;
    }
    return false;
}
bool actorStackAffected(inout Runtime s,uint row,ActorBits scope)
{
    for(uint target=0;target<actorPoolCount(s);target++)
        if(actorBitsHas(scope,target)&&actorRecipientMember(s,row,target==0?0:ACTOR_REF|target)&&!actorStackBlocked(s,target)) return true;
    return false;
}
