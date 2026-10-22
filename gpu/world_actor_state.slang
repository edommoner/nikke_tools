// Named predicates consume canonical carrier keys;lifetimes/scalars remain shared.
bool actorStateEnabled(inout Runtime s)
{ return WORLD_MUTATION_STATE_ENABLED(s,actorFieldsEnabled(s) && commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+4]==0x57533031); }
// Preserve the scalar value before updating the same RW buffer element.
// Slang CUDA can otherwise retain a pointer and load it after the store.
[noinline]
uint actorStateQueryScopeSnapshot(uint at)
{ return results[at]; }
uint actorStatePushQuery(inout Runtime s,uint target)
{
    if(!actorStateEnabled(s)) return 0;
    uint at=actorFieldHead(s)+3;uint previous=actorStateQueryScopeSnapshot(at);results[at]=actorFieldLogicalSlot(s,target)+1;return previous;
}
void actorStatePopQuery(inout Runtime s,uint previous)
{ if(actorStateEnabled(s)) results[actorFieldHead(s)+3]=previous; }
void actorStateEvent(inout Runtime s,Frame frames[32],int depth,uint entryOwner,uint entryTarget)
{
    if(!actorStateEnabled(s)) return;
    uint owner=entryOwner,target=entryTarget;
    for(int i=depth;i>=0;i--) if(frames[i].mode==0) { owner=frames[i].owner;target=frames[i].target;break; }
    results[actorFieldHead(s)+4]=owner;results[actorFieldHead(s)+5]=target;
}
uint actorStateCurrentTarget(inout Runtime s)
{
    uint head=actorFieldHead(s),scope=results[head+3];if(scope!=0) return scope-1;
    uint target=results[head+5];if((target&ACTOR_REF)!=0) return COUNTER_CONTEXT_TARGET(s,actorFieldLogicalSlot(s,target));
    return COUNTER_CONTEXT_TARGET(s,actorPhysicalTarget(s,results[head+4],0)&127U);
}
uint64_t actorNamedTargetStack(inout Runtime s,int name,out bool present)
{
    uint target=actorStateCurrentTarget(s);uint64_t count=0;present=false;
    if(target>=actorPoolCount(s)||results[actorPoolAt(s,target)+1]==0) return 0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];
        // Presence follows the resident list;numeric modifier queries separately
        // filter end time. A post-frame query must not run an invented tick.
        WORLD_PERIODIC_NAMED(s,row,target,count,present,name) if(s.alive[row]==0 || int(definition_name(s.inputBase,s.carrierDefinition[row]))!=name || definition_enemyBuff(s.inputBase,s.carrierDefinition[row])==0 || !actorFieldMember(s,row,target==0?0:ACTOR_REF|target)) continue;
        present=true;count=larger(count,carrierStackValue(s,row));
    }
    return count;
}
uint64_t actorNamedSelfStack(inout Runtime s,uint who,int name)
{
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(s.alive[row]==0 || d.owner!=who || int(d.name)!=name) continue;
        bool member=d.enemyBuff!=0 ? (s.activeRecipients[row]&32)!=0 : (s.activeRecipients[row]&(1U<<who))!=0;
        if(member) return carrierStackValue(s,row);
    }
    return 0;
}
bool actorNamedConditionKind(uint kind)
{ return kind==C_TARGET_STATE||kind==C_NOT_TARGET_STATE||kind==C_TARGET_STACK||kind==C_SELF_STATE||kind==C_NOT_SELF_STATE||kind==C_SELF_STACK; }
bool actorNamedConditionValid(inout Runtime s,uint at,uint kind,uint64_t arg)
{
    if(commands[at+1]>=P_DEFINITIONS || !f64Finite(arg)) return false;
    if(kind==C_SELF_STATE||kind==C_NOT_SELF_STATE) return f64Zero(arg)||f64Equal(arg,ONE)||f64Equal(arg,f64FromI64(2));
    if(kind==C_TARGET_STATE||kind==C_NOT_TARGET_STATE) return f64Zero(arg);
    uint status;uint64_t integer=f64ToI64(arg,1,status);
    return status==0&&!f64Less(arg,0)&&!f64Less(f64FromI64(2147483647),arg)&&f64Equal(arg,f64FromI64(integer));
}
void actorStateGone(inout Runtime s,uint slot)
{
    if(!actorStateEnabled(s)) return;
    uint at=actorFieldHead(s)+8+slot/32;results[at]|=1U<<(slot%32);
}
void actorStateDropGone(inout Runtime s)
{
    if(!actorStateEnabled(s)) return;
    WORLD_RECIPIENT_GONE(s) uint head=actorFieldHead(s);ActorBits gone;bool any=false;
    for(uint i=0;i<4;i++) { gone.words[i]=results[head+8+i];any|=gone.words[i]!=0;results[head+8+i]=0; }
    if(!any) return;
    // Native drops labels after death/start/end notifications. A new generation
    // created during those notifications is also removed if its label is gone.
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],bound=results[actorFieldKey(s,row)];
        if(bound!=0 && actorBitsHas(gone,bound-1)) s.activeRecipients[row]&=~32U;
    }
}
bool initializeActorState(inout Runtime s)
{
    bool enabled=actorStateEnabled(s);
    for(uint step=0;step<P_COMMANDS;step++)
    {
        uint at=s.inputBase+P_WORLD_ACTOR_STATE_INPUT_BASE+step*2,name=commands[at],flags=commands[at+1];
        bool query=enabled&&step<commands[s.inputBase+2]&&commands[s.inputBase+P_COMMAND_BASE+step*8]==41;
        if(query ? name>=P_DEFINITIONS||flags!=0 : name!=0||flags!=0) return false;
    }
    if(enabled) results[actorFieldHead(s)+14]=0x57533031;return true;
}
[noinline]
bool actorNamedQueryCommand(inout Runtime s,uint at,uint step,uint64_t when)
{
    if(!actorStateEnabled(s)) return false;
    uint who=commands[at+3],kind=commands[at+4],id=commands[at+5],gen=commands[at+6],index=commands[at+7];
    if(who>=5||kind>5||id>=0x10000000U||gen==0||gen>=0x80000000U||index>=P_COMMANDS) return false;
    uint out=s.resourceOutput+P_WORLD_ACTOR_FIELD_QUERY_BASE+index*16;for(uint i=0;i<16;i++) results[out+i]=0;
    uint slot,status=worldActorResolve(s,kind,id,gen,slot);results[out]=status;if(status!=0) return true;
    uint name=commands[s.inputBase+P_WORLD_ACTOR_STATE_INPUT_BASE+step*2];
    results[out+1]=kind;results[out+2]=id;results[out+3]=gen;results[out+4]=results[actorPoolAt(s,slot)+1];results[out+5]=name;
    uint previous=actorStatePushQuery(s,kind==1||slot==0?0:ACTOR_REF|slot);bool present;uint64_t stack=actorNamedTargetStack(s,int(name),present);actorStatePopQuery(s,previous);
    results[out+6]=uint(present);storeNumber(out+7,stack);results[out+9]=s.enemySnapshot;return true;
}

bool actorNamedNumericCondition(inout Runtime s,uint row,uint who,uint64_t when)
{
    uint previous=0;bool body=actorStateEnabled(s)&&definition_stat(s.inputBase,s.carrierDefinition[row])==S_infinite_ammo;
    if(body) previous=actorStatePushQuery(s,0);
    bool ok=basicConditions(s,row,when,true,who);if(body) actorStatePopQuery(s,previous);return ok;
}

bool actorStateHeaderInvalid(inout Runtime s,uint base,uint index)
{ uint value=commands[base+index];return index==4 ? WORLD_MUTATION_HEADER_INVALID(s,value,value!=0&&value!=0x57533031) : value!=0; }

bool actorStateHealthContract(Definition d)
{
    bool health=(d.alliedFlags&1)!=0||d.stat==S_def_caster_based_pct||(d.stat>=S_max_hp_pct&&d.stat<=S_max_hp_only_pct)||d.stat==S_max_hp_from_max_hp_pct;
    // Explicitly packed direct-health policy preserves native helper semantics;
    // ordinary stat/buff queries continue to evaluate their runtime predicates.
    return (d.flags&256U)!=0 || !(d.enemyBuff==0&&health&&(d.flags&2)!=0&&f64Less(d.duration,0));
}
