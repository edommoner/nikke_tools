// Native removal changes resident membership, not unrelated mode/instant clocks.
uint filterRemovalOrder(uint order,uint mask,uint width,uint count)
{
    uint filtered=0,size=0,field=(1U<<width)-1;
    for(uint i=0;i<count;i++)
    {
        uint value=(order>>(i*width))&field;if(value==0) break;
        if((mask&(1U<<(value-1)))!=0) filtered|=value<<(width*size++);
    }
    return filtered;
}
uint removalMembers(inout Runtime s,uint slot)
{
    uint definition=s.carrierDefinition[slot];
    if(s.defs[definition].kind!=3 || f64Zero(s.defs[definition].interval)) return s.lazyPending[slot]!=0 ? 0 : s.activeRecipients[slot];
    if((s.defs[definition].periodicFlags&1)==0) return 1U<<(s.timerTarget[definition]+5);
    uint mask=0,order=s.periodicOrder[definition];
    for(uint i=0;i<8;i++) { uint value=(order>>(4*i))&15;if(value==0) break;mask|=1U<<(value-1); }
    return mask<<5;
}
// All old instances are changed before any state_end callback runs. This
// preserves callbacks that recycle a slot or register a new same-name clock.
void removeNamedResidents(inout Runtime s,uint row,uint target,uint64_t when)
{
    uint policy=s.defs[row].target,name=uint(s.defs[row].targetName),scope=0xffffffff;
    if(policy==1) { uint order;scope=selectRecipients(s,row,when,order); }
    else if(policy==2) { uint order;scope=enemyDamageMask(s,s.defs[row],target,order)<<5; }
    if(scope==0) return;
    for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0 || s.defs[definition].name!=name) continue;
        uint notices=s.defs[definition].enemyBuff!=0 ? enemyMaskCount(s.activeRecipients[slot]>>5) : 1;
        if(policy!=0)
        {
            uint prior=removalMembers(s,slot),stripped=prior&scope;
            if(stripped==0) continue;
            uint remaining=prior&~stripped;
            if(s.defs[definition].kind==3 && !f64Zero(s.defs[definition].interval))
            {
                if((s.defs[definition].periodicFlags&1)!=0) s.periodicOrder[definition]=filterRemovalOrder(s.periodicOrder[definition],remaining>>5,4,8);
            }
            else
            {
                s.activeRecipients[slot]=remaining;
                s.carrierRecipientOrder[slot]=filterRemovalOrder(s.carrierRecipientOrder[slot],remaining&31,3,5);
            }
            if(s.defs[definition].enemyBuff!=0)
            {
                notices=enemyMaskCount(stripped>>5);
                if(remaining!=0) { queueRemovalNotice(s,s.defs[definition].owner,name,notices);continue; }
            }
            else if(remaining!=0) continue;
        }
        queueCarrierEnd(s,slot,notices);
        // Only periodic damage has both a resident and its definition clock.
        // Instant clocks have no resident, and never reach this retirement.
        if(s.defs[definition].kind==3) s.timerActive[definition]=0;
    }
}
bool validRemovalDefinition(uint input,uint combat,uint row)
{
    uint at=input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS;
    if(commands[at+D_KIND]!=1) return true;
    uint policy=commands[at+D_TARGET];int name=int(commands[at+D_TARGET_NAME]);
    if(policy>2 || name< -1 || name>=int(P_DEFINITIONS)) return false;
    uint recipient=input+P_RECIPIENT_BASE+row*8;
    if(policy==1) { if(!validRecipientPlan(recipient) || commands[recipient+7]!=0) return false; }
    else for(uint i=0;i<8;i++) if(commands[recipient+i]!=0) return false;
    uint packet=input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS;
    if(policy==2)
    {
        if(combat==0 || commands[packet]>9 || commands[packet+1]==0 || commands[packet+1]>256) return false;
        for(uint i=2;i<8;i++) if(commands[packet+i]!=0) return false;
    }
    else for(uint i=0;i<8;i++) if(commands[packet+i]!=0) return false;
    return true;
}
