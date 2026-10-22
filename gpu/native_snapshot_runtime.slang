// Pinned logging is observable: a full-burst snapshot directly resolves every
// pending carrier once for each squad member, without freezing membership.
void nativeFullBurstSnapshot(inout Runtime s,uint64_t when)
{
    if(!nativeNumericEnabled(s) || commands[s.inputBase+P_RECIPIENT_META_BASE+6]==0) return;
    for(uint who=0;who<5;who++)
        for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
        {
            uint row=s.orderedRows[pass];
            if(s.alive[row]==0 || s.lazyPending[row]==0) continue;
            uint64_t order;selectRecipients(s,s.carrierDefinition[row],when,order);
        }
}

// Expiration logs consume pending lazy membership after state-end children.
// The dead carrier is reserved until this continuation releases its snapshot.
void finishNativeExpiredSnapshot(inout Runtime s,uint slot,uint64_t when)
{
    ensureLazyRecipients(s,slot,when);
    discardLazy(s,slot);s.stacks[slot]=0;
}
