// Logical enemy queries project exact typed generations; physical receipts stay intact.
bool typedOwnerPolicyEnabled(inout Runtime s)
{return commands[DF_EXTRA(s)+15]==2&&commands[DF_EXTRA(s)+12]==1;}
bool validTypedOwnerPolicy(inout Runtime s)
{
    uint p=DF_EXTRA(s),count=commands[p+2320];
    if(count==0||count>128)return false;
    for(uint slot=0;slot<count;slot++)
    {
        uint binding=p+2328+slot*12,kind=commands[binding+1];
        if((kind!=2&&kind!=3)||commands[binding+5]!=0||commands[binding+6]!=0||commands[binding+7]!=1)return false;
    }
    return true;
}
uint typedOwnerContextTarget(inout Runtime s,uint kind,uint identity,uint generation)
{
    uint count=commands[DF_EXTRA(s)+2320],base=DF_BASE(s.resourceOutput);
    for(uint slot=0;slot<count;slot++)
    {
        uint at=dtAt(base,slot);
        if(results[at]==kind&&results[at+1]==identity)
        {
            // Death does not erase ownership. Re-entry invalidates the old generation.
            if(results[at+2]==generation&&results[at+10]==0&&results[at+11]==0&&results[at+12]==1)return 0;
            s.error=64;return 128;
        }
    }
    s.error=64;return 128;
}
