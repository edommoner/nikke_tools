// Shared frozen history, threshold dispatch, and ownership release.
results[head+3]=0;results[at]=2;
    uint log=0xffffffffU,compact=0xffffffffU;
    if(results[head+5]<AG_LOG_CAP)
    {
        log=s.resourceOutput+AG_LOG+results[head+5]++*AG_WORDS;
        for(uint i=0;i<AG_WORDS;i++) results[log+i]=results[at+i];
    }
    if(results[head+10]!=0)
    {
        // Lossless variable-length history is independent of the 32 live
        // group slots. No rolling hash, dropped target or overwritten record.
        uint words=24+results[at+4]*4,used=results[head+11];
        if(used>AG_COMPACT_WORDS||words>AG_COMPACT_WORDS-used) { s.error=64;return true; }
        compact=s.resourceOutput+AG_COMPACT+used;results[head+11]+=words;
        for(uint i=0;i<words;i++) results[compact+i]=results[at+i];
    }
    uint key=agKey(s,group),prior=results[head+4];bool seen[129];for(uint i=0;i<129;i++) seen[i]=false;
    for(uint row=0;row<s.count&&s.error==0;row++)
    {
        Definition d=readDefinition(s.inputBase,row);if(d.owner!=who) continue;
        for(uint slot=0;slot<d.triggerCount&&s.error==0;slot++)
        {
            uint p=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;if(commands[p]!=62) continue;uint threshold=commands[p+4];
            if(seen[threshold]) continue;seen[threshold]=true;if(results[at+4]<threshold) continue;
            results[head+4]=key;results[head+6]++;
            if(log!=0xffffffffU) results[log+10]++;
            if(compact!=0xffffffffU) results[compact+10]++;
            dispatch(s,0,62,who,int(threshold),when,output);
        }
    }
    results[head+4]=prior;agRelease(s,key);return true;
