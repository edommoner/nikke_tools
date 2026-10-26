// Canonical128 source pools and immutable typed recipient sets. Every number
// uses the same integer binary64 operations as the shared event interpreter.
static const uint ACTOR_REF=0x80000000U;
bool actorPoolsEnabled(inout Runtime s) { return commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE]!=0; }
uint actorPoolHead(inout Runtime s) { return s.resourceOutput+P_WORLD_ACTOR_POOL_OUTPUT_BASE; }
uint actorPoolAt(inout Runtime s,uint slot) { return s.resourceOutput+P_WORLD_ACTOR_POOL_STATE_BASE+slot*16; }
uint actorPoolDef(inout Runtime s,uint slot) { return s.inputBase+P_WORLD_ACTOR_POOL_DEF_BASE+slot*12; }
uint64_t actorNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
struct ActorBits { uint words[4]; };
ActorBits actorBitsEmpty() { ActorBits b;for(uint i=0;i<4;i++) b.words[i]=0;return b; }
void actorBitsAdd(inout ActorBits b,uint slot) { b.words[slot/32]|=1U<<(slot%32); }
bool actorBitsHas(ActorBits b,uint slot) { return (b.words[slot/32]&(1U<<(slot%32)))!=0; }
bool actorBitsIntersects(ActorBits a,ActorBits b)
{ for(uint i=0;i<4;i++) if((a.words[i]&b.words[i])!=0) return true;return false; }
uint actorPoolCount(inout Runtime s) { return commands[s.inputBase+P_WORLD_ACTOR_INPUT_BASE+1]; }
uint actorPoolSet(inout Runtime s,uint index) { return s.resourceOutput+P_WORLD_ACTOR_SET_BASE+index*P_WORLD_ACTOR_SET_WORDS; }
bool actorPoolsClearedAllowed(inout Runtime s,uint node)
{ return actorPoolsEnabled(s) && commands[s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4]!=0; }
bool actorPoolsTargetSpawn(inout Runtime s)
{
    if(!actorPoolsEnabled(s)) return false;
    uint count=commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+1];if(count>128) return false;
    for(uint slot=0;slot<count;slot++)
    { uint d=actorPoolDef(s,slot),n=commands[d+6];for(uint i=0;i<min(n,8U);i++) if(((commands[d+7]>>(i*3))&7)==2) return true; }
    return false;
}
uint actorPoolsEnemyCount(inout Runtime s)
{
    uint count=0;for(uint slot=0;slot<actorPoolCount(s);slot++)
        if((commands[actorBinding(s,slot)]==0 || commands[actorBinding(s,slot)]==5) && results[actorPoolAt(s,slot)+1]!=0) count++;
    return count;
}
[noinline]
bool initializeActorPools(inout Runtime s)
{
    uint base=s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE,head=actorPoolHead(s);
    for(uint i=0;i<P_WORLD_ACTOR_POOL_OUTPUT_WORDS-P_WORLD_FRAME_OUTPUT_WORDS;i++) results[head+i]=0;
    if(commands[base]==0)
    { for(uint i=0;i<P_WORLD_ACTOR_POOL_INPUT_WORDS-P_WORLD_ACTOR_INPUT_WORDS;i++) if(commands[base+i]!=0) return false;return true; }
    if(commands[base]!=0x57485031 || !worldActorsEnabled(s) || commands[base+1]!=actorPoolCount(s)) return false;
    #ifdef PORTABLE_WORLD_ACTOR_FIELDS
    uint64_t bossAtk=loadNumber(base+2);if(!f64Finite(bossAtk)||f64Less(bossAtk,0)) return false;
    for(uint i=4;i<8;i++) if(WORLD_STATE_HEADER_INVALID(s,base,i,commands[base+i]!=0)) return false;
#else
    for(uint i=2;i<8;i++) if(commands[base+i]!=0) return false;
#endif
    for(uint slot=0;slot<128;slot++)
    {
        uint d=actorPoolDef(s,slot),mode=commands[d],kind=commands[actorBinding(s,slot)];
        if(slot==0 || slot>=actorPoolCount(s)) { for(uint i=0;i<12;i++) if(commands[d+i]!=0) return false;continue; }
        uint64_t hp=loadNumber(d+2),after=loadNumber(d+4);
        if(!f64Finite(hp)||f64Less(hp,0)||!f64Finite(after)||f64Less(after,0)||commands[d+1]>0x7fffffff) return false;
        if(kind==1||kind==6 ? mode!=1 : mode<2||mode>4) return false;
        if(mode<=2 && (commands[d+1]!=0 || !f64Zero(after)) || mode==2 && !f64Less(0,hp)) return false;
        if(mode>=3 && commands[d+1]==0 || mode==3 && (!f64Zero(hp)||!f64Zero(after)) || mode==4 && (!f64Less(0,hp)||!f64Less(0,after))) return false;
        uint n=commands[d+6],packed=commands[d+7];if(n>8 || (packed>>(n*3))!=0 || kind!=1 && kind!=6 && (n!=0||commands[d+8]!=0)) return false;
        for(uint i=0;i<n;i++) if(((packed>>(i*3))&7)==0||((packed>>(i*3))&7)>4) return false;
        #ifdef PORTABLE_WORLD_ACTOR_FIELDS
        uint64_t atk=loadNumber(d+9);if(!f64Finite(atk)||f64Less(atk,0)||kind!=5&&!f64Zero(atk)) return false;
        if(commands[d+8]>0x7fffffff || commands[d+11]>(focusAimEnabled(s) && kind==1 ? 1U : 0U)) return false;
#else
        if(commands[d+8]>0x7fffffff || commands[d+9]!=0||commands[d+10]!=0||commands[d+11]!=0) return false;
#endif
    }
    // Wide enemy carriers/skill packets are connected in the next stage.
    // Numeric allied buffs and weapon modes already use the common core.
    for(uint row=0;row<s.count;row++)
    { Definition d=readDefinition(s.inputBase,row); PROJECTILE_POOL_ROW(s,row,d)
#ifdef PORTABLE_WORLD_ACTOR_FIELDS
        if(!actorFieldsDefinitionValid(s,row,d)) return false;
#else
        if(d.enemyBuff!=0 || (d.kind!=0&&d.kind!=2&&d.kind!=4) || d.conditionCount!=0) return false;
#endif
    }
    for(uint step=0;step<P_COMMANDS;step++)
    {
        uint at=s.inputBase+P_WORLD_ACTOR_LAND_INPUT_BASE+step*2;uint64_t amount=loadNumber(at);
        if(!f64Finite(amount)||f64Less(amount,0)) return false;
    }
    results[head]=0x57485031;results[head+1]=actorPoolCount(s);results[actorPoolAt(s,0)]=1;results[actorPoolAt(s,0)+1]=1;
    actorPoolsSync(s,0);worldActorsApply(s);return s.error==0;
}
[noinline]
void actorPoolsSync(inout Runtime s,uint64_t when)
{
    if(!actorPoolsEnabled(s)) return;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
    {
        uint b=actorBinding(s,slot),p=actorPoolAt(s,slot),g=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+commands[b+3]*24,gen=results[g+1];
        if(gen!=results[p])
        {
            WORLD_STATE_BEFORE_RESET(s,b,p,slot) COUNTER_EXTRA_RESET(s,slot) for(uint i=0;i<16;i++) results[p+i]=0;
            results[p]=gen;results[p+1]=results[g];storeNumber(p+8,actorNumber(g+2));
            if(commands[b]==5)
            { uint head=actorPoolHead(s);if(results[head+4]==0x7fffffff) { s.error=2;return; }results[p+10]=++results[head+4]; }
        }
        else if(results[g]==0 && results[p+1]!=0)
        { results[p+1]=0;if(commands[b]==5) { WORLD_STATE_GONE(s,slot) results[p+2]=2; } }
    }
    s.enemySnapshot=actorPoolsEnemyCount(s);
}
uint actorPoolsCleared(inout Runtime s)
{
    if(!actorPoolsEnabled(s)) return 0;
    ActorBits alive=actorBitsEmpty();for(uint i=1;i<actorPoolCount(s);i++) if(results[actorPoolAt(s,i)+1]!=0) actorBitsAdd(alive,i);
    uint mask=0,nodes=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint n=0;n<nodes;n++)
    {
        uint graph=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+n*24,d=s.inputBase+P_WORLD_FRAME_INPUT_BASE+16+n*64;
        if(results[graph]==0 || (commands[d+1]&2)==0) continue;
        ActorBits required=actorBitsEmpty();bool any=false;
        for(uint slot=1;slot<actorPoolCount(s);slot++)
            if(commands[actorBinding(s,slot)+3]==n && (commands[actorBinding(s,slot)]==5 || f64Less(0,loadNumber(actorPoolDef(s,slot)+2)))) { actorBitsAdd(required,slot);any=true; }
        if(any && !actorBitsIntersects(required,alive)) mask|=1U<<n;
    }
    return mask;
}
void actorPoolNotice(inout Runtime s,uint slot,uint generation,uint event)
{
    uint head=actorPoolHead(s),n=results[head+5];if(n>=P_WORLD_ACTOR_NOTICES) { s.error=2;return; }
    uint at=s.resourceOutput+P_WORLD_ACTOR_NOTICE_BASE+n*3;results[at]=event;results[at+1]=slot;results[at+2]=generation;results[head+5]=n+1;
}
void actorPoolAddOverkill(inout Runtime s,uint who,uint64_t amount,bool attributed=true)
{ uint at=actorPoolHead(s)+16;storeNumber(at,f64Add(actorNumber(at),amount));if(attributed) s.addOverkill[who]=f64Add(s.addOverkill[who],amount); }
[noinline]
void actorPoolLand(inout Runtime s,uint who,uint slot,uint64_t amount)
{
    uint head=actorPoolHead(s),scratch=head+18,p=actorPoolAt(s,slot),d=actorPoolDef(s,slot),kind=commands[actorBinding(s,slot)],gen=results[p];
    for(uint i=0;i<6;i++) results[scratch+i]=0;
    uint64_t took=0,overkill=0,when=actorNumber(head+2);bool killed=false,live=results[p+1]!=0;
#ifdef PORTABLE_WORLD_PROJECTILE
    uint interruptReceipt=0;
    if(kind==6) { interruptReceipt=beginInterruptAimReceipt(s,who,slot,amount);if(s.error!=0) return;accumulateInterruptAimDamage(s,who,amount);if(s.error!=0) return; }
#endif
    bool directTarget=kind==1 || kind==6;
#ifdef PORTABLE_COORDINATE_SAMPLED_PARENT
    if(kind==0 || kind==1)recordSampledParentDamage(s,who,amount);
#endif
    if(kind==0 || kind==1)
    { s.total[who]=f64Add(s.total[who],amount);s.scoredDamage[who]=f64Add(s.scoredDamage[who],amount); }
    if(kind==0)
    {
        if(results[p+3]==0x7fffffff) { s.error=2;return; }results[p+3]++;
        storeNumber(p+4,f64Add(actorNumber(p+4),amount));storeNumber(p+6,f64Add(actorNumber(p+6),amount));
        s.targetDamage[0]=actorNumber(p+4);s.targetScoredDamage[0]=actorNumber(p+4);s.targetHits[0]=results[p+3];
        took=amount;results[scratch]=1;
    }
    else if(live)
    {
        uint mode=commands[d];bool counting=mode==3 || mode==4 && !f64Less(when,f64Add(f64Add(actorNumber(p+8),loadNumber(d+4)),WS_EPS^F64_SIGN));
        if(COUNTER_PART_DIRECT(s,kind,directTarget || counting))
        { if(results[p+3]==0x7fffffff) { s.error=2;return; }results[p+3]++; }
        took=directTarget ? amount : counting ? smaller(amount,ONE) : smaller(amount,f64Add(loadNumber(d+2),actorNumber(p+4)^F64_SIGN));
        uint64_t dealt=COUNTER_PART_DEALT(s,kind,d,p,f64Add(actorNumber(p+4),took));storeNumber(p+4,dealt);
        if(COUNTER_PART_DIRECT(s,kind,directTarget)) storeNumber(p+6,f64Add(actorNumber(p+6),amount));
        killed=directTarget ? f64Less(0,loadNumber(d+2))&&!f64Less(dealt,loadNumber(d+2)) : counting ? results[p+3]>=commands[d+1] : !f64Less(dealt,loadNumber(d+2));
        if(kind==5) { s.addScoredDamage[who]=f64Add(s.addScoredDamage[who],took);overkill=f64Add(amount,took^F64_SIGN);actorPoolAddOverkill(s,who,overkill); }
        results[scratch]=1;
        if(killed)
        {
            results[p+1]=0;results[p+2]=1;results[head+14]++;
            WorldSchedule w=frameSchedule(s);wsLog(w,5,commands[actorBinding(s,slot)+3],slot,when);s.error=w.error;
            if(kind==5) { WORLD_STATE_GONE(s,slot) actorPoolNotice(s,slot,gen,4); }
            else
            {
                uint64_t score=actorNumber(head+8),next=score+uint64_t(commands[d+8]);if(next<score) { s.error=2;return; }storeNumber(head+8,next);
                for(uint i=0;i<commands[d+6];i++) actorPoolNotice(s,slot,gen,(commands[d+7]>>(i*3))&7);
            }
        }
    }
    else if(kind==5) { overkill=amount;actorPoolAddOverkill(s,who,amount); }
    results[scratch+1]=uint(killed);storeNumber(scratch+2,took);storeNumber(scratch+4,overkill);results[head+15]++;
    if(!f64Finite(actorNumber(p+4))||!f64Finite(actorNumber(p+6))||!f64Finite(actorNumber(head+16))||!f64Finite(s.total[who])||!f64Finite(s.scoredDamage[who])||!f64Finite(s.addScoredDamage[who])||!f64Finite(s.addOverkill[who])) s.error=16;
#ifdef PORTABLE_WORLD_PROJECTILE
    if(kind==6) endInterruptAimReceipt(s,interruptReceipt,who,slot);
#endif
    worldActorsApply(s);
}
uint actorPhysicalTarget(inout Runtime s,uint who,uint legacy)
{
    if(!actorPoolsEnabled(s)) return legacy;
    if(focusAimEnabled(s) && results[s.resourceOutput+P_FOCUS_STATE_BASE+6]==0x46414331U)
    {
        uint slot=uint(actorNumber(s.resourceOutput+P_FOCUS_STATE_BASE)>>(8*who))&255U;
#ifdef PORTABLE_COORDINATE_TYPED_AIM
        if(typedAimEnabled(s))
        {
            slot=uint(actorNumber(s.resourceOutput+P_FOCUS_STATE_BASE)>>(9*who))&511U;
            // Typed physical packets route through their own sampled consumer.
            // Their aim identity cannot index the canonical actor pool.
#ifdef PORTABLE_COORDINATE_TYPED_ACTORS
            if(typedActorPolicyEnabled(s)&&slot==0)return ACTOR_REF|focusFirstAdd(s);
#endif
            if(slot==257)return ACTOR_REF|focusFirstAdd(s);
            if(slot>=128)return ACTOR_REF;
        }
#endif
        return ACTOR_REF|(slot==128 ? focusFirstAdd(s) : slot);
    }
    uint slot=0,order=0xffffffffU;
    for(uint i=1;i<actorPoolCount(s);i++) if(commands[actorBinding(s,i)]==5 && results[actorPoolAt(s,i)+1]!=0 && results[actorPoolAt(s,i)+10]<order) { slot=i;order=results[actorPoolAt(s,i)+10]; }
    return ACTOR_REF|slot;
}
bool actorPhysicalGate(inout Runtime s,uint who,uint target,uint64_t amount,uint64_t when)
{
#ifdef PORTABLE_COORDINATE_SKILLS
    s.error=64;return false; // Coordinate physical probability is not connected.
#endif
    if(!actorPoolsEnabled(s)) return worldOverlayLand(s,who,target,amount,worldPhysicalNormal(s,who));
    storeNumber(actorPoolHead(s)+2,when);uint ref=actorPhysicalTarget(s,who,target),slot=ref&127;
    return commands[actorBinding(s,slot)]==5 || worldOverlayLand(s,who,0,amount,worldPhysicalNormal(s,who));
}
[noinline]
void actorPoolsDeliver(inout Runtime s,uint64_t when,uint output)
{
    if(!actorPoolsEnabled(s)) return;
    uint head=actorPoolHead(s),end=results[head+5];
    for(uint i=0;i<end && s.error==0;i++)
    { uint at=s.resourceOutput+P_WORLD_ACTOR_NOTICE_BASE+i*3,event=results[at];results[head+9+event]++;worldFrameNotice(s,event,when,output); }
    uint count=results[head+5]-end;
    for(uint i=0;i<count*3;i++) results[s.resourceOutput+P_WORLD_ACTOR_NOTICE_BASE+i]=results[s.resourceOutput+P_WORLD_ACTOR_NOTICE_BASE+end*3+i];
    results[head+5]=count;
}
void actorPoolsSpawnNotice(inout Runtime s,uint node,uint64_t when,uint output)
{
    if(!actorPoolsEnabled(s) || commands[s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4]!=2) return;
    for(uint i=0;i<commands[s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4+1] && s.error==0;i++) { results[actorPoolHead(s)+6]++;worldFrameNotice(s,5,when,output); }
}
[noinline]
// Stable Actor sequence: body first, then add birth order within each add run.
void actorSortSpawnOrder(inout Runtime s,inout uint order[128],uint count)
{
    for(uint i=1;i<count;i++)
    {
        uint slot=order[i],insert=i;
        if(commands[actorBinding(s,slot)]!=5) continue;
        while(insert>0 && commands[actorBinding(s,order[insert-1])]==5 && results[actorPoolAt(s,slot)+10]<results[actorPoolAt(s,order[insert-1])+10])
        { order[insert]=order[insert-1];insert--; }
        order[insert]=slot;
    }
}
[noinline]
void actorSetCapture(inout Runtime s,uint kindMask,uint index,uint route=2,uint limit=128,uint inherited=0,uint who=0 NAMED_ENEMY_PARAMETER)
{
#ifdef PORTABLE_ATTACK_GROUPS
    if(route==0&&kindMask==33&&results[agHead(s)+4]!=0) { agCapture(s,results[agHead(s)+4],index);return; }
#endif
    uint at=actorPoolSet(s,index),head=actorPoolHead(s);
    if(results[at+5]!=0) { s.error=64;return; }
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++) results[at+i]=0;
    uint order[128],count=0;
    for(uint slot=0;slot<actorPoolCount(s);slot++)
    {
        uint kind=commands[actorBinding(s,slot)];if((kindMask&(1U<<kind))==0 || results[actorPoolAt(s,slot)+1]==0) continue;
        order[count++]=slot;
    }
    actorSortSpawnOrder(s,order,count);
#ifdef PORTABLE_WORLD_ACTOR_FIELDS
    actorFieldSelectOrder(s,order,count,route,limit,inherited,who NAMED_ENEMY_ARGUMENT(definition));
#endif
    ActorBits bits=actorBitsEmpty();
    for(uint i=0;i<count;i++)
    {
        uint slot=order[i],entry=at+8+i*4,b=actorBinding(s,slot);actorBitsAdd(bits,slot);
        results[entry]=slot;results[entry+1]=results[actorPoolAt(s,slot)];results[entry+2]=commands[b];results[entry+3]=commands[b+1];
    }
    results[at]=count;for(uint i=0;i<4;i++) results[at+1+i]=bits.words[i];results[at+5]=1;results[head+7]++;
}
void actorReceiptReset(inout Runtime s,uint index,uint status)
{ uint at=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+index*8;for(uint i=0;i<8;i++) results[at+i]=0;results[at]=status; }
void actorReceiptAppend(inout Runtime s,uint index)
{
    uint at=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+index*8,from=actorPoolHead(s)+18;
    results[at+2]+=results[from];results[at+3]+=results[from+1];storeNumber(at+4,f64Add(actorNumber(at+4),actorNumber(from+2)));storeNumber(at+6,f64Add(actorNumber(at+6),actorNumber(from+4)));
}
[noinline]
void actorDirectLand(inout Runtime s,uint who,uint kind,uint identity,uint generation,uint index,uint64_t amount,uint64_t when)
{
    uint slot,status=worldActorResolve(s,kind,identity,generation,slot);actorReceiptReset(s,index,status);uint out=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+index*8;results[out+1]=1;
    if(status!=0) return;
    storeNumber(actorPoolHead(s)+2,when);land(s,who,ACTOR_REF|slot,amount);actorReceiptAppend(s,index);
}
[noinline]
void actorSetLand(inout Runtime s,uint who,uint setIndex,uint index,uint64_t amount,uint64_t when)
{
    uint at=actorPoolSet(s,setIndex);if(results[at+5]!=1) { s.error=64;return; }results[at+5]=2;
    actorReceiptReset(s,index,0);uint out=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+index*8;results[out+1]=results[at];storeNumber(actorPoolHead(s)+2,when);
    for(uint i=0;i<results[at] && s.error==0;i++)
    {
        uint entry=at+8+i*4,slot=results[entry];if(results[actorPoolAt(s,slot)]!=results[entry+1]) continue;
        land(s,who,ACTOR_REF|slot,amount);actorReceiptAppend(s,index);
    }
    results[at+5]=0;results[actorPoolHead(s)+7]--;
}
void actorPoolQuery(inout Runtime s,uint kind,uint identity,uint generation,uint query)
{
    uint out=s.resourceOutput+P_WORLD_ACTOR_POOL_QUERY_BASE+query*16,slot,status=worldActorResolve(s,kind,identity,generation,slot);
    for(uint i=0;i<16;i++) results[out+i]=0;results[out]=status;if(status!=0) return;
    uint p=actorPoolAt(s,slot);results[out+1]=kind;results[out+2]=identity;results[out+3]=generation;results[out+4]=results[p+1];results[out+5]=results[p+2];results[out+6]=results[p+3];results[out+7]=results[p+10];
    for(uint i=0;i<4;i++) results[out+8+i]=results[p+4+i];results[out+12]=results[p+8];results[out+13]=results[p+9];
}
[noinline]
bool actorPoolCommand(inout Runtime s,uint command,uint step,uint64_t when)
{
    if(!actorPoolsEnabled(s)) return false;
    uint at=s.inputBase+P_COMMAND_BASE+step*8;
    if(command==34)
    {
        uint who=commands[at+3],kind=commands[at+4],id=commands[at+5],gen=commands[at+6],query=commands[at+7];
        if(who>=5 || kind>5 || id>=0x10000000U || gen==0||gen>=0x80000000U||query>=P_COMMANDS) return false;
        actorDirectLand(s,who,kind,id,gen,query,loadNumber(s.inputBase+P_WORLD_ACTOR_LAND_INPUT_BASE+step*2),when);
    }
    else if(command==35)
    {
        uint mask=commands[at+3],index=commands[at+4];if(mask==0||(mask&~35U)!=0||index>=P_WORLD_ACTOR_SETS||commands[at+5]!=0||commands[at+6]!=0||commands[at+7]!=0) return false;
        actorSetCapture(s,mask,index);
    }
    else if(command==36)
    {
        uint who=commands[at+3],set=commands[at+4],query=commands[at+5];if(who>=5||set>=P_WORLD_ACTOR_SETS||query>=P_COMMANDS||commands[at+6]!=0||commands[at+7]!=0) return false;
        actorSetLand(s,who,set,query,loadNumber(s.inputBase+P_WORLD_ACTOR_LAND_INPUT_BASE+step*2),when);
    }
    else if(command==37)
    {
        uint kind=commands[at+3],id=commands[at+4],gen=commands[at+5],query=commands[at+6];if(kind>5||id>=0x10000000U||gen==0||gen>=0x80000000U||query>=P_COMMANDS||commands[at+7]!=0) return false;
        actorPoolQuery(s,kind,id,gen,query);
    }
    else if(command==38)
    {
        uint set=commands[at+3];if(set>=P_WORLD_ACTOR_SETS || commands[at+4]!=0||commands[at+5]!=0||commands[at+6]!=0||commands[at+7]!=0||results[actorPoolSet(s,set)+5]!=1) return false;
        results[actorPoolSet(s,set)+5]=0;results[actorPoolHead(s)+7]--;
    }
    else return false;
    return true;
}
