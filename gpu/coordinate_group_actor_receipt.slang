        if(kind!=5&&!worldOverlayLand(s,who,0,amount,false))continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,who,ACTOR_REF|slot,amount);
        uint receipt=actorPoolHead(s)+18;if(results[receipt]==0||s.error!=0)continue;
        coordinateTrace(s,who,slot,generation,amount,when,extra);
        if(grouped)agCollect(s,results[agHead(s)+3]-1,slot,generation);
        uint64_t credit=kind==5?actorNumber(receipt+2):amount;
        counterPhysicalPacket(s,who,slot,generation,credit,results[receipt+1]!=0,when,s.resourceOutput);
        if((s.healthMask&64)!=0&&s.error==0)dispatch(s,17,0,who,0,when,s.resourceOutput,amount);
        if(slot==0&&damageAccumEnabled(s)&&s.error==0)dispatch(s,39,0,who,0,when,s.resourceOutput,amount);
