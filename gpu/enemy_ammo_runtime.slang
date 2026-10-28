uint eamHead(inout Runtime s){return s.resourceOutput+EAM_OUTPUT_BASE;}
uint eamRule(inout Runtime s,uint slot){return s.inputBase+EAM_BASE+EAM_ROW_BASE+slot*8;}
uint eamState(inout Runtime s,uint slot){return eamHead(s)+EAM_STATE_BASE+slot*EAM_STATE_WORDS;}
uint eamHistory(inout Runtime s,uint index){return eamHead(s)+EAM_HISTORY_BASE+index*EAM_HISTORY_WORDS;}
bool enemyAmmoDefinition(inout Runtime s,uint row,Definition d)
{return d.kind==13&&commands[s.inputBase+P_RECIPIENT_BASE+row*8]==4;}
bool enemyAmmoRecipientValid(inout Runtime s,uint row,Definition d)
{
    uint at=s.inputBase+P_RECIPIENT_BASE+row*8;
    if(d.kind!=13||d.enemyBuff!=0||!f64Finite(d.value)||commands[at]!=4||commands[at+6]>=P_DEFINITIONS)return false;
    for(uint i=1;i<8;i++)if(i!=6&&commands[at+i]!=0)return false;
    return true;
}

uint eamEvent(inout Runtime s,uint kind)
{
    uint h=eamHead(s),n=results[h+2];if(n>=EAM_EVENTS){s.error=2;return h;}
    uint at=h+EAM_EVENT_BASE+n*16;results[at]=kind;results[h+2]=n+1;return at;
}
void eamSyncHistory(inout Runtime s,uint slot)
{
    uint p=eamState(s,slot),index=results[p+4];if(index==0)return;
    uint h=eamHistory(s,index-1);results[h+4]=results[p+1];storeNumber(h+6,actorNumber(p+2));
    uint actor=actorPoolAt(s,slot);results[h+5]=uint(results[actor]==results[p]&&results[actor+1]!=0);
}
void eamReloadEvent(inout Runtime s,uint kind,uint slot,uint before,uint after,uint64_t when,uint64_t deadline)
{
    uint at=eamEvent(s,kind);if(s.error!=0)return;
    results[at+1]=slot;results[at+2]=results[eamState(s,slot)];results[at+3]=before;results[at+4]=after;
    storeNumber(at+6,when);storeNumber(at+8,deadline);
}

void enemyAmmoRefresh(inout Runtime s,uint64_t when)
{
    uint input=s.inputBase+EAM_BASE,head=eamHead(s);
    for(uint i=0;i<commands[input+2]&&s.error==0;i++)
    {
        uint slot=commands[input+EAM_ORDER_BASE+i]-1,rule=eamRule(s,slot),p=eamState(s,slot),actor=actorPoolAt(s,slot),generation=results[actor];
        if(generation==0)continue;
        if(results[p]!=generation)
        {
            if(results[p+4]!=0)results[eamHistory(s,results[p+4]-1)+5]=0;
            uint index=results[head+1];if(index>=EAM_HISTORIES){s.error=2;return;}
            results[head+1]=index+1;results[p]=generation;results[p+1]=commands[rule+2];storeNumber(p+2,F64_SIGN|ONE);results[p+4]=index+1;
            uint h=eamHistory(s,index);results[h]=slot;results[h+1]=generation;results[h+2]=commands[rule+1];results[h+3]=commands[rule+2];storeNumber(h+8,when);
        }
        uint64_t deadline=actorNumber(p+2);
        if(results[actor+1]!=0&&f64Less(0,deadline)&&!f64Less(when,deadline))
        {
            uint before=results[p+1];results[p+1]=commands[rule+1];storeNumber(p+2,F64_SIGN|ONE);
            eamReloadEvent(s,5,slot,before,results[p+1],when,deadline);
        }
        eamSyncHistory(s,slot);
    }
}

bool initializeEnemyAmmo(inout Runtime s)
{
    uint input=s.inputBase+EAM_BASE,count=commands[input+2];
    if(commands[input]!=EAM_MAGIC||commands[input+1]!=1||count==0||count>128||commands[input+3]!=actorPoolCount(s))return false;
    for(uint i=4;i<16;i++)if(commands[input+i]!=0)return false;
    ActorBits declared=actorBitsEmpty();
    for(uint i=0;i<128;i++)
    {
        uint encoded=commands[input+EAM_ORDER_BASE+i];
        if(i>=count){if(encoded!=0)return false;continue;}
        if(encoded==0||encoded>actorPoolCount(s)||actorBitsHas(declared,encoded-1))return false;
        actorBitsAdd(declared,encoded-1);
    }
    for(uint slot=0;slot<128;slot++)
    {
        uint row=eamRule(s,slot);bool present=actorBitsHas(declared,slot);
        if(!present){for(uint i=0;i<8;i++)if(commands[row+i]!=0)return false;continue;}
        uint kind=commands[actorBinding(s,slot)];uint64_t duration=loadNumber(row+4);
        if(kind!=0&&kind!=5||commands[row]!=1||commands[row+1]==0||commands[row+1]>0x7fffffffU||commands[row+2]>commands[row+1]||commands[row+3]>1||!f64Finite(duration)||!f64Less(0,duration)||commands[row+6]!=0||commands[row+7]!=0)return false;
    }
    for(uint node=0;node<commands[s.inputBase+WF_INPUT+1];node++)
    {
        if(commands[s.inputBase+WF_INPUT+16+node*64+6]!=0&&!actorBitsHas(declared,0))return false;
        if(commands[adbRow(s,node)]==0)continue;
        for(uint slot=1;slot<actorPoolCount(s);slot++)if(commands[actorBinding(s,slot)]==5&&commands[actorBinding(s,slot)+3]==node&&!actorBitsHas(declared,slot))return false;
    }
    for(uint i=0;i<EAM_EVENT_BASE+EAM_EVENTS*16;i++)results[eamHead(s)+i]=0;
    results[eamHead(s)]=EAM_MAGIC;return true;
}

void applyEnemyAmmoInstant(inout Runtime s,Definition d,uint row,uint64_t when)
{
    enemyAmmoRefresh(s,when);if(s.error!=0)return;
    uint order[128],count=0;
    for(uint slot=0;slot<actorPoolCount(s);slot++)
        if(commands[eamRule(s,slot)]!=0&&results[actorPoolAt(s,slot)+1]!=0)order[count++]=slot;
    actorSortSpawnOrder(s,order,count);
    uint begin=eamEvent(s,1);if(s.error!=0)return;
    results[begin+1]=row;results[begin+2]=d.owner;results[begin+3]=d.name;storeNumber(begin+4,when);storeNumber(begin+6,d.value);results[begin+8]=count;
    int64_t flat;uint64_t fraction;
    if(!prepareAmmoInstant(13,d.value,flat,fraction)){s.error=16;return;}
    for(uint i=0;i<count&&s.error==0;i++)
    {
        uint slot=order[i],rule=eamRule(s,slot),p=eamState(s,slot),capacity=commands[rule+1],before=results[p+1];int after;
        if(!ammoInstantResult(13,capacity,int(before),flat,fraction,after)){s.error=16;return;}
        results[p+1]=uint(after);uint64_t deadline=actorNumber(p+2);
        uint target=eamEvent(s,2);if(s.error!=0)return;
        results[target+1]=row;results[target+2]=slot;results[target+3]=results[p];results[target+4]=capacity;results[target+5]=before;results[target+6]=uint(after);storeNumber(target+8,when);
        if(commands[rule+3]!=0&&f64Less(0,deadline)&&uint(after)>=capacity)
        {storeNumber(p+2,F64_SIGN|ONE);eamReloadEvent(s,6,slot,before,uint(after),when,deadline);}
        eamSyncHistory(s,slot);
    }
    if(d.target!=0&&s.error==0)
    {
        uint done=eamEvent(s,3);if(s.error!=0)return;
        results[done+1]=row;results[done+2]=d.name;results[done+3]=d.owner;storeNumber(done+4,when);results[done+6]=count;
    }
    // Original applyDefinitionFrame dispatches the one named completion only
    // after this complete loop; no new notifier is introduced here.
}

bool enemyAmmoAttempt(inout Runtime s,uint record,uint node,uint64_t when)
{
    enemyAmmoRefresh(s,when);if(s.error!=0)return false;
    uint map=adbMap(s,record),slot=results[map],generation=results[map+1],actor=actorPoolAt(s,slot),p=eamState(s,slot),rule=eamRule(s,slot);
    uint at=eamEvent(s,7);if(s.error!=0)return false;
    results[at+1]=record;results[at+2]=slot;results[at+3]=generation;results[at+7]=results[s.resourceOutput+WF_OUTPUT+WS_LOG+record*6+2];storeNumber(at+8,when);results[at+10]=node;
    if(results[actor]!=generation){results[at+6]=5;return false;}
#ifdef PORTABLE_ENEMY_AMMO_SELF_DESTRUCT
    bool retiredQueue=enemyAmmoRetiredQueue(s,record,node,slot,generation,when);
    if(retiredQueue)results[at+11]=1;
#else
    bool retiredQueue=false;
#endif
    if(results[actor+1]==0&&!retiredQueue){results[at+6]=4;return false;}
    uint before=results[p+1];results[at+4]=before;results[at+5]=before;
    if(f64Less(0,actorNumber(p+2))){results[at+6]=2;return false;}
    if(before==0)
    {
        uint64_t deadline=f64Add(when,loadNumber(rule+4));storeNumber(p+2,deadline);results[at+6]=3;
        eamReloadEvent(s,4,slot,0,0,when,deadline);eamSyncHistory(s,slot);return false;
    }
    results[p+1]=before-1;results[at+5]=before-1;results[at+6]=1;eamSyncHistory(s,slot);return true;
}

void enemyAmmoFinish(inout Runtime s)
{
    uint input=s.inputBase+EAM_BASE;
    for(uint i=0;i<commands[input+2];i++)eamSyncHistory(s,commands[input+EAM_ORDER_BASE+i]-1);
}
