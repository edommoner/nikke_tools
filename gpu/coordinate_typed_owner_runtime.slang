// Logical enemy queries project exact typed generations; physical receipts stay intact.
bool typedOwnerPolicyEnabled(inout Runtime s)
{
    uint p=DF_EXTRA(s);
    return commands[p+15]==2&&(commands[p+12]==1
#ifdef PORTABLE_COORDINATE_LOGICAL_OWNERS
        ||commands[p+12]==3
#endif
    );
}
bool validTypedOwnerPolicy(inout Runtime s)
{
    uint p=DF_EXTRA(s),count=commands[p+2320];
    if(count==0||count>128)return false;
    for(uint slot=0;slot<count;slot++)
    {
        uint binding=p+2328+slot*12,kind=commands[binding+1];
        if(kind!=2&&kind!=3)return false;
#ifdef PORTABLE_COORDINATE_LOGICAL_OWNERS
        if(commands[p+12]==3)
        {
            uint ownerKind=commands[binding+5],ownerId=commands[binding+6],ownerGen=commands[binding+7];
            if(ownerKind==0){if(ownerId!=0||ownerGen!=1)return false;}
            else if(ownerKind==5)
            {
                if(ownerGen==0||ownerGen>=0x80000000U)return false;
                bool found=false;
                for(uint a=1;a<commands[s.inputBase+P_WORLD_ACTOR_INPUT_BASE+1];a++)
                    if(commands[actorBinding(s,a)]==5&&commands[actorBinding(s,a)+1]==ownerId)found=true;
                if(!found)return false;
            }
            else return false;
            continue;
        }
#endif
        if(commands[binding+5]!=0||commands[binding+6]!=0||commands[binding+7]!=1)return false;
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
            if(results[at+2]!=generation){s.error=64;return 128;}
#ifdef PORTABLE_COORDINATE_LOGICAL_OWNERS
            if(commands[DF_EXTRA(s)+12]==3)
            {
                uint ownerKind=results[at+10],ownerId=results[at+11],ownerGen=results[at+12];
                for(uint a=0;a<actorPoolCount(s);a++)
                    if(commands[actorBinding(s,a)]==ownerKind&&commands[actorBinding(s,a)+1]==ownerId)
                    {
                        // Exact dead owners retain their identity. A new ADD generation never inherits the old field.
                        if((ownerKind==0||ownerKind==5)&&results[actorPoolAt(s,a)]==ownerGen)return a;
                        s.error=64;return 128;
                    }
                s.error=64;return 128;
            }
#endif
            if(results[at+10]==0&&results[at+11]==0&&results[at+12]==1)return 0;
            s.error=64;return 128;
        }
    }
    s.error=64;return 128;
}
