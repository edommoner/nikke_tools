        if(s.error!=0)return legacy;if(!worldOverlayLand(s,who,0,amount,false))continue;
        storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,who,ACTOR_REF|slot,amount);if(s.error!=0)return legacy;
        coordinateTrace(s,who,slot,gen,amount,when,CF_PACKET_EXTRA);
        uint kind=commands[actorBinding(s,slot)];
        if(kind==0)publishCounterLanding(s,who,ACTOR_REF|slot,amount,when,s.resourceOutput);
        else if(kind==1)counterPhysicalPacket(s,who,slot,gen,amount,coordinatePartNeedsRetirement(s,slot,gen),when,s.resourceOutput);
        if((s.healthMask&64)!=0&&s.error==0)dispatch(s,17,0,who,0,when,s.resourceOutput,amount);
#ifdef PORTABLE_DAMAGE_ACCUM
        if(slot==0&&damageAccumEnabled(s)&&s.error==0)dispatch(s,39,0,who,0,when,s.resourceOutput,amount);
#endif
