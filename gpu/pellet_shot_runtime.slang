// Static raw-spelling IDs are owned by one shooter. No battle result is packed.
[noinline]
bool validPelletInShot(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        for(uint slot=0;slot<d.triggerCount;slot++)
        {
            uint at=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
            if(commands[at]!=27) continue;
            uint tag=commands[at+4],status;uint64_t threshold=loadNumber(at+1),integer=f64ToI64(threshold,1,status);
            if(s.combat==0 || commands[at+3]!=0 || tag==0 || tag>s.count*8 || status!=0 || !f64Equal(threshold,f64FromI64(integer)) || f64Less(threshold,f64FromI64(uint64_t(-2147483648))) || f64Less(f64FromI64(2147483647),threshold) || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0) return false;
            bool predecessor=tag==1;
            for(uint other=0;other<s.count;other++)
            {
                Definition od=readDefinition(s.inputBase,other);
                if(od.owner!=d.owner) continue;
                for(uint os=0;os<od.triggerCount;os++)
                {
                    uint p=s.inputBase+P_EVENT_BASE+other*P_EVENT_WORDS+os*8;
                    if(commands[p]!=27) continue;
                    uint otag=commands[p+4];uint64_t value=loadNumber(p+1);
                    if(otag==tag && !f64Equal(value,threshold)) return false;
                    if(otag+1==tag) predecessor=true;
                    if(otag<tag && f64Less(threshold,value)) return false;
                }
            }
            if(!predecessor) return false;
            s.quantityMask|=1U<<(19+d.owner);
        }
    }
    return true;
}

[noinline]
void notifyPelletInShot(inout Runtime s,uint who,uint count,uint64_t when,uint output)
{
    if((s.quantityMask&(1U<<(19+who)))==0) return;
    uint cursor=0;
    for(uint work=0;work<s.count*8 && s.error==0;work++)
    {
        uint next=0xffffffff;uint64_t threshold=0;
        for(uint row=0;row<s.count;row++)
        {
            Definition d=readDefinition(s.inputBase,row);
            if(d.owner!=who) continue;
            for(uint slot=0;slot<d.triggerCount;slot++)
            {
                uint at=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
                if(commands[at]!=27) continue;
                uint tag=commands[at+4];
                if(tag>cursor && tag<next) { next=tag;threshold=loadNumber(at+1); }
            }
        }
        if(next==0xffffffff || f64Less(f64FromI64(count),threshold)) return;
        dispatch(s,0,27,who,int(next),when,output);cursor=next;
    }
}
