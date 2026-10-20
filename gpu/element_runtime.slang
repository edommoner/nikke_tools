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
        uint row=s.orderedRows[pass];
        if(s.alive[row]==0 || (s.activeRecipients[row]&(1U<<who))==0) continue;
        uint definition=s.carrierDefinition[row];
        if(definition_kind(s.inputBase,definition)==0 &&
           definition_stat(s.inputBase,definition)==S_element_code_override &&
           definition_damageRoute(s.inputBase,definition)==code) return true;
    }
    return false;
}
