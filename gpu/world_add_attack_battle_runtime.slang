uint adbHead(inout Runtime s){return s.resourceOutput+ADB_OUTPUT_BASE;}
uint adbRow(inout Runtime s,uint node){return s.inputBase+ADB_BASE+ADB_ROW_BASE+node*ADB_ROW_WORDS;}
uint adbMap(inout Runtime s,uint record){return adbHead(s)+ADB_MAP_BASE+record*2;}
bool addAttackArgument(uint arg){return (arg&0xc0000000U)==0xc0000000U;}

bool initializeAddAttackBattle(inout Runtime s)
{
    uint base=s.inputBase+ADB_BASE,nodes=commands[s.inputBase+WF_INPUT+1];
    if(commands[base]!=ADB_MAGIC||commands[base+1]!=1||commands[base+2]!=nodes||commands[base+3]!=actorPoolCount(s))return false;
    for(uint i=4;i<16;i++)if(commands[base+i]!=0)return false;
    for(uint node=0;node<32;node++)
    {
        uint row=adbRow(s,node),count=commands[row];
        if(node>=nodes||count==0){for(uint i=0;i<24;i++)if(commands[row+i]!=0)return false;continue;}
        uint source=s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4;
        if(commands[source]!=2||commands[source+1]!=count||count>127||commands[row+1]>0x7fffffffU||commands[s.inputBase+WF_INPUT+16+node*64+6]!=0)return false;
        uint64_t interval=loadNumber(row+2);
        if(!f64Finite(interval)||f64Less(interval,0)||commands[row+1]==0&&!f64Zero(interval))return false;
#ifdef PORTABLE_ADD_SELF_DESTRUCT
        if(!validAddSelfDestructRow(s,row))return false;
#else
        for(uint i=4;i<8;i++)if(commands[row+i]!=0)return false;
#endif
        uint p=row+8;
        if(commands[p]!=32||commands[p+1]!=0||commands[p+2]!=0||commands[p+3]>1)return false;
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
        if(commands[p+6]==0x42444631U)
        {if(!worldBossAddDebuffPayload(s,node))return false;}
        else
#endif
        for(uint i=4;i<8;i++)if(commands[p+i]!=0)return false;
        uint64_t attack=loadNumber(p+8),coeff=loadNumber(p+10);
        if(!f64Finite(attack)||f64Less(attack,0)||!f64Finite(coeff)||f64Less(coeff,0)||f64Less(f64FromI64(1000000),coeff))return false;
        uint rule=commands[p+12],n=commands[p+13],slots=commands[p+14],ignore=commands[p+15];
        if(rule>3||ignore>1||rule==0&&(n!=0||slots!=0||ignore!=0)||rule!=0&&(n==0||n>5)||rule!=1&&slots!=0)return false;
        if(rule==1)
        {
            uint previous=0;
            for(uint i=0;i<5;i++){uint encoded=(slots>>(3*i))&7;if(i<n ? encoded==0||encoded>5||encoded<=previous : encoded!=0)return false;previous=encoded;}
            if((slots>>15)!=0)return false;
        }
    }
    for(uint i=0;i<ADB_MAP_BASE+ADB_MAP_ROWS*2;i++)results[adbHead(s)+i]=0;
    results[adbHead(s)]=ADB_MAGIC;
#ifdef PORTABLE_ADD_SELF_DESTRUCT
    return initializeAddSelfDestruct(s);
#else
    return true;
#endif
}

void addAttackEmit(inout Runtime s,inout WorldSchedule w,uint node,uint slot,uint generation,uint index,uint64_t when)
{
    uint record=results[w.output+2];wsLog(w,3,node,index,when);s.error=w.error;
    if(s.error!=0)return;
    uint map=adbMap(s,record);results[map]=slot;results[map+1]=generation;results[adbHead(s)+1]++;
}

void addAttackBattleFrame(inout Runtime s,uint64_t when,uint first)
{
    WorldSchedule w=frameSchedule(s);uint end=results[w.output+2],head=adbHead(s),shotStart=end;
    for(uint n=0;n<64;n++)results[head+ADB_BODY_BASE+n]=0;
    for(uint i=first;i<end;i++)
    {
        uint at=w.output+WS_LOG+i*6;if(results[at]!=3)continue;
        shotStart=min(shotStart,i);uint body=head+ADB_BODY_BASE+results[at+1]*2;
        if(results[body]==0)results[body+1]=results[at+2];results[body]++;
    }
    results[w.output+2]=shotStart;
    for(uint node=0;node<w.count&&s.error==0;node++)
    {
        uint body=head+ADB_BODY_BASE+node*2;
        for(uint j=0;j<results[body]&&s.error==0;j++)addAttackEmit(s,w,node,0,1,results[body+1]+j,when);
        uint row=adbRow(s,node),count=commands[row];if(count==0)continue;
        for(uint slot=1;slot<actorPoolCount(s)&&s.error==0;slot++)
        {
            uint b=actorBinding(s,slot);if(commands[b]!=5||commands[b+3]!=node)continue;
            uint p=actorPoolAt(s,slot),index,cursor=head+ADB_STATE_BASE+slot*2;
#ifdef PORTABLE_ADD_SELF_DESTRUCT
            while(s.error==0&&nextWorldAddAttack(cursor,results[p],results[p+1]!=0,f64Add(actorNumber(p+8),loadNumber(row+5)),commands[row+1],loadNumber(row+2),when,index))
#else
            while(s.error==0&&nextWorldAddAttack(cursor,results[p],results[p+1]!=0,actorNumber(p+8),commands[row+1],loadNumber(row+2),when,index))
#endif
            {
                addAttackEmit(s,w,node,slot,results[p],index,when);
                results[wsState(w,node)+4]++;
            }
#ifdef PORTABLE_ADD_SELF_DESTRUCT
            if(s.error==0)retireAddAfterFinalShot(s,node,slot,cursor,when);
#endif
        }
    }
    for(uint n=0;n<64;n++)results[head+ADB_BODY_BASE+n]=0;
}

uint addAttackDeliveryArgument(inout Runtime s,uint record,uint node)
{
    uint slot=results[adbMap(s,record)];
    return 0x80000000U|node|(slot!=0 ? 0x40000000U|(slot<<5) : 0);
}

uint64_t addAttackBasis(inout Runtime s,uint arg,uint64_t when)
{
    // Native ADD attacks retain their literal atk; the existing CPU incoming
    // handler currently applies the caster-based attack debuff only to BODY.
    return addAttackArgument(arg)?0:collectWorldEnemyAttackFlat(s,0,when);
}

void addAttackBattleFinish(inout Runtime s)
{
    // Finish retires all actual pools. Expose the same native cleared predicate
    // only after this final synchronization; no new graph transition is run.
    for(uint node=0;node<commands[s.inputBase+WF_INPUT+1];node++)
    {
        uint g=s.resourceOutput+WF_OUTPUT+16+node*24,d=s.inputBase+WF_INPUT+16+node*64;
        if(commands[adbRow(s,node)]!=0&&results[g+1]!=0&&(commands[d+1]&2)!=0)results[g+6]=1;
    }
}
