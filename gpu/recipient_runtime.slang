#ifdef PORTABLE_BELOW_DEF
#include "below_def_recipient_runtime.slang"
#endif
// Friendly-only selection seeds the existing allied RNG without enabling revival.
bool validAlliedRandomMetadata(uint input)
{
    uint at=input+P_RECIPIENT_META_BASE;
    if(commands[at+2]!=0 && commands[at+2]!=0x41524731U) return false;
    if(commands[at+2]==0 && (commands[at+3]!=0 || commands[at+4]!=0)) return false;
    if(commands[at+5]!=0 && (commands[at+5]!=0x4e515231U || commands[at+2]!=0x41524731U)) return false;
    if(commands[at+6]>1 || (commands[at+6]!=0 && commands[at+5]!=0x4e515231U)) return false;
    if(commands[at+7]!=0) return false;
    return true;
}
bool alliedRandomEnabled(inout Runtime s)
{ return commands[s.inputBase+P_RECIPIENT_META_BASE+2]==0x41524731U; }
#ifdef PORTABLE_RANDOM_CLEANSE
bool alliedHasHarmful(inout Runtime s,uint who)
{
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]!=0 && s.lazyPending[slot]==0 && (definition_polarity(s.inputBase,definition)==2 || definition_polarity(s.inputBase,definition)==3) && (s.activeRecipients[slot]&(1U<<who))!=0) return true;
    }
    return false;
}
#endif
bool validRecipientLeaf(uint at, bool enemy = false)
{
    uint kind = commands[at], count = commands[at+1], mask = commands[at+2];
#ifdef PORTABLE_RANDOM_CLEANSE
    if(kind==20) return !enemy && count<=5 && mask==0 && commands[at+3]==0 && commands[at+4]==0 && commands[at+5]==0 && commands[at+6]<P_DEFINITIONS && commands[at+7]==0;
#endif
#ifdef PORTABLE_BELOW_DEF
    if(kind==14) return !enemy && count==0 && mask==0 && commands[at+3]==0 && commands[at+4]==0 && commands[at+5]==0 && commands[at+6]<P_DEFINITIONS && (commands[at+7]&8U)==0 && (commands[at+7]>>4)<=P_DEFINITIONS;
#endif
#ifdef PORTABLE_LEFTMOST
    if(kind==24) return !enemy && count<=5 && mask<=31 && commands[at+3]==0 && commands[at+4]==0 && commands[at+5]==0 && commands[at+6]<P_DEFINITIONS && (commands[at+7]&~7U)==0;
#endif
    if (enemy) return kind == 4 && count == 0 && mask == 0 && commands[at+3] == 0 && commands[at+4] == 0 && commands[at+5] == 0 && commands[at+6] < P_DEFINITIONS && (commands[at+7] & ~7U) == 0;
    if (kind > 25 || (kind == 17 || kind == 20 || kind == 24) || kind == 4 || kind == 14 || count > 5 || mask > 31 || commands[at+3] > (kind == 12 || kind == 13 ? 2 : 1)) return false;
    if ((kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16 || kind == 21) && count == 0) return false;
    if((kind==22 || kind==23) && (count==0 || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0 || (commands[at+7]>>4)!=0)) return false;
    if(kind==18 && (count!=0 || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0 || (commands[at+7]>>4)!=0)) return false;
    if((kind==19 || kind==25) && (mask!=0 || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0)) return false;
    uint order = commands[at+4], seen = 0; bool ended = false;
    if (order >> 15 != 0 || commands[at+6] >= P_DEFINITIONS || (commands[at+7] & 8) != 0 || (commands[at+7] >> 4) > P_DEFINITIONS) return false;
    for (uint i = 0; i < 5; i++)
    {
        uint encoded = (order >> (3*i)) & 7;
        if (encoded == 0) { ended = true; continue; }
        if (ended || encoded > 5 || (seen & (1U << (encoded-1))) != 0) return false;
        seen |= 1U << (encoded-1);
    }
    return order == 0 || kind == 8 && seen == mask;
}
bool validRecipientPlan(uint at,bool enemy,uint input)
{
    if(commands[at]!=17) return validRecipientLeaf(at,enemy);
    uint total=commands[input+P_RECIPIENT_META_BASE],count=commands[at+1],first=commands[at+2];
    if(enemy || total>P_RECIPIENT_NODES || count==0 || count>21 || first>total || count>total-first || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]>=P_DEFINITIONS || (commands[at+7]&~7U)!=0) return false;
    if(commands[input+P_RECIPIENT_META_BASE+1]>1) { return false; }
    if(!validAlliedRandomMetadata(input)) return false;
    for(uint node=0;node<count;node++) if(!validRecipientLeaf(input+P_RECIPIENT_NODE_BASE+(first+node)*8)) return false;
    return true;
}
// Shared ordered selection. Static metadata is compiled once; ranks and burst
// membership are resolved from this invocation's GPU state, never CPU traces.
[noinline]
uint selectRecipientLeaf(inout Runtime s, uint row, uint at, uint64_t when, out uint64_t order)
{
    Definition d = readDefinition(s.inputBase,row);
    uint kind = commands[at], count = commands[at+1], candidates = commands[at+2];
    uint exclude = commands[at+3], authoredOrder = commands[at+4];
#ifdef PORTABLE_BELOW_DEF
    if(kind==14) return selectBelowDefense(s,row,when,order);
#endif
#ifdef PORTABLE_LEFTMOST
    if(kind==24)
    {
        uint mask=0,written=0;order=0;
        for(uint who=0;who<5 && written<count;who++)
            if((candidates&(1U<<who))!=0 && (s.downMask&(1U<<who))==0)
            { mask|=1U<<who;order|=uint64_t(who+1)<<(3*written++); }
        return mask;
    }
#endif
    if (kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16 || kind==22) return rankedRecipientsAt(s,row,at,when,order);
    if(kind==19 || kind==25
#ifdef PORTABLE_RANDOM_CLEANSE
       || kind==20
#endif
       )
    {
#ifdef PORTABLE_WORLD_PROJECTILE
        if(!alliedRandomEnabled(s)) { s.error=64;order=0;return 0; }
        uint pool[5],size=0;
        for(uint who=0;who<5;who++) if((s.downMask&(1U<<who))==0 &&
            (kind==19 ? who!=d.owner :
#ifdef PORTABLE_RANDOM_CLEANSE
             kind==20 ? alliedHasHarmful(s,who) :
#endif
             !f64Less(0,s.coverHP[who]))) pool[size++]=who;
        uint ignored,mask=0,k=min(count,size),before=results[s.resourceOutput+P_REVIVAL_RNG_BASE];
        uint sampled=mtSampleFive(s.resourceOutput+P_REVIVAL_RNG_BASE,size,k,ignored);order=0;
        uint poolMask=0;for(uint i=0;i<size;i++) poolMask|=1U<<pool[i];
        for(uint i=0;i<k;i++) { uint who=pool[((sampled>>(i*3))&7)-1];mask|=1U<<who;order|=uint64_t(who+1)<<(i*3); }
        alliedSampleRecord(s,d.owner,kind,k,poolMask,uint(order),before,when);
        return mask;
#else
        s.error=64;order=0;return 0;
#endif
    }
    if(kind==23)
    {
#ifdef PORTABLE_WORLD_PROJECTILE
        if(!revivalEnabled(s)) { s.error=64;order=0;return 0; }
        uint pool[5],size=0;for(uint who=0;who<5;who++) if((candidates&s.downMask&(1U<<who))!=0) pool[size++]=who;
        if(size==0) { order=0;return 0; }
        uint ignored,mask=0;uint sampled=mtSampleFive(s.resourceOutput+P_REVIVAL_RNG_BASE,size,min(count,size),ignored);order=0;
        for(uint i=0;i<min(count,size);i++) { uint who=pool[((sampled>>(i*3))&7)-1];mask|=1U<<who;order|=uint64_t(who+1)<<(i*3); }
        return mask;
#else
        s.error=64;order=0;return 0;
#endif
    }
    if (kind == 21) return coverRecipients(s,count,order);
    if (kind == 0)
    {
        uint mask = (1U << d.owner) & ~s.downMask;
        order = mask != 0 ? d.owner+1 : 0; return mask;
    }
    uint slots[5]; uint size = 0;
    if (kind == 2)
    { for (uint who = d.owner+1; who < 5 && size < count; who++) slots[size++] = who; }
    else if (kind == 3)
    {
        slots[size++] = d.owner;
        if (d.owner > 0 && count > 0) slots[size++] = d.owner-1;
        if (d.owner < 4 && size <= count) slots[size++] = d.owner+1;
    }
    else if (kind == 8 && authoredOrder != 0)
    {
        for (uint i = 0; i < 5; i++)
        { uint encoded = (authoredOrder >> (3*i)) & 7; if (encoded != 0) slots[size++] = encoded-1; }
    }
    else
    {
        uint pool = kind == 8 || kind == 15 || kind == 16 || kind == 18 ? candidates : 31;
        if(kind==18)
        {
            pool &= ~(1U<<d.owner);
            for(uint who=0;who<5;who++) if(!statusPersona(s,who)) pool &= ~(1U<<who);
        }
        if (kind == 9 || kind == 11) pool &= s.castMask;
        if (kind == 10) pool &= ~s.castMask;
        if (kind == 11) pool &= candidates;
        if (kind == 12 || kind == 13)
        {
            for (uint who = 0; who < 5; who++)
            {
                bool present = stateMember(s,who,int(commands[at+5]),exclude);
                if (kind == 12 && !present || kind == 13 && present) pool &= ~(1U << who);
            }
        }
        else if (exclude != 0) pool &= ~(1U << d.owner);
        pool &= ~s.downMask;
        for (uint who = 0; who < 5; who++) if ((pool & (1U << who)) != 0) slots[size++] = who;
    }
    uint mask = 0, written = 0; order = 0;
    for (uint i = 0; i < size; i++) if ((s.downMask & (1U << slots[i])) == 0)
    { mask |= 1U << slots[i]; order |= uint64_t(slots[i]+1) << (3*written++); }
    return mask;
}

[noinline]
uint selectRecipients(inout Runtime s,uint row,uint64_t when,out uint64_t order)
{
    uint at=s.inputBase+P_RECIPIENT_BASE+row*8;
    if(commands[at]!=17) return selectRecipientLeaf(s,row,at,when,order);
    uint count=commands[at+1],first=commands[at+2],seen=0,written=0;order=0;
    for(uint node=0;node<count;node++)
    {
        uint64_t leafOrder;selectRecipientLeaf(s,row,s.inputBase+P_RECIPIENT_NODE_BASE+(first+node)*8,when,leafOrder);
        for(uint i=0;i<5;i++)
        {
            uint encoded=(leafOrder>>(i*3))&7;if(encoded==0) break;uint bit=1U<<(encoded-1);
            if(written==21) { s.error=64;return 0; }
            seen|=bit;order|=uint64_t(encoded)<<(3*written++);
        }
    }
    return seen;
}

// Ordered GPU observations, sharing the bounded revival event bank. No CPU plan.
void alliedSampleRecord(inout Runtime s,uint owner,uint kind,uint k,uint pool,uint order,uint before,uint64_t when)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    uint head=s.resourceOutput+P_REVIVAL_BASE,index=results[head+6]++;
    uint history=s.resourceOutput+P_ORDERED_HISTORY_BASE;
    uint at=orderedHistoryRecordAt(s.resourceOutput+P_REVIVAL_TRACE_BASE,history,index,nativeNumericEnabled(s));
    if(at==0xffffffffU) { s.error=64;return; }
    results[at]=3;results[at+1]=owner|(kind<<3)|(k<<8);
    results[at+2]=pool;results[at+3]=order;results[at+4]=before;
    results[at+5]=results[s.resourceOutput+P_REVIVAL_RNG_BASE];storeNumber(at+6,when);
    if(!orderedHistoryRecordDone(history,index,at)) s.error=64;
#endif
}
