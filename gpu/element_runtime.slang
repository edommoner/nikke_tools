// Native presence helper: this deliberately does not invoke numeric-buff query
// filters or resolve pending ranked recipients. Roster identity is immutable.
// Expiry is owned by the carrier lifecycle: periodic callbacks run before its
// cleanup, exactly as the native active-buff presence helper does.
bool elementMatch(inout Runtime s,uint who)
{
    if((s.attackContext[who]&2)!=0) return true;
    uint world=s.inputBase+P_WORLD_META_BASE,code=commands[world];
    if(code==0 || commands[world+2]==0) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind==0 && d.stat==S_element_code_override && s.alive[row]!=0 &&
           d.damageRoute==code &&
           (s.activeRecipients[row]&(1U<<who))!=0) return true;
    }
    return false;
}
