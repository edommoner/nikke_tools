// GPU-owned boss victim rules; all returned targets are derived from current GPU state.
// Include after rank/query/carrier helpers and the integer MT module.
[noinline]
uint currentTaunters(inout Runtime s,uint64_t when)
{
    uint mask=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];
        if(definition_kind(s.inputBase,definition)!=0 || definition_stat(s.inputBase,definition)!=S_taunt || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;
        if(definition_enemyBuff(s.inputBase,definition)!=0)
        {
            bool member=false;
            for(uint enemy=0;enemy<s.targetCount;enemy++)
                if((s.activeRecipients[row]&(1U<<(enemy+5)))!=0 && targetLive(s,enemy,enemyCarrierGeneration(s,row,enemy))) member=true;
            if(member) mask|=1U<<definition_owner(s.inputBase,definition);
            // Native enemy branch never rechecks this carrier's runtime predicate.
            continue;
        }
        // taunters iterates target_chars before calling _live;None does not resolve here.
        if(s.lazyPending[row]!=0) continue;
        uint64_t order=carrierOrder(s,row);
        for(uint i=0;i<21;i++)
        {
            uint encoded=uint((order>>(3*i))&7);if(encoded==0) break;uint who=encoded-1;
            if((s.downMask&(1U<<who))==0 && queryRecipient(s,row,who,when)) { mask|=1U<<who;break; }
        }
    }
    return mask & ~s.downMask;
}
[noinline]
bool targetStealth(inout Runtime s,uint who,uint64_t when)
{
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];
        if(definition_kind(s.inputBase,definition)==0 && definition_stat(s.inputBase,definition)==S_stealth && definition_enemyBuff(s.inputBase,definition)==0 && queryRecipient(s,row,who,when)) return true;
    }
    return false;
}
[noinline]
uint64_t bossTargetAttack(inout Runtime s,uint who,uint64_t when)
{
    // Native _effective_atk uses resident target membership and representative values.
    // It excludes HP-derived attack and does not re-evaluate runtime predicates.
    uint64_t percent=0,flat=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];
        if(definition_kind(s.inputBase,definition)!=0 || s.alive[row]==0 || !f64Less(when,s.end[row]) || (s.activeRecipients[row]&(1U<<who))==0) continue;
        uint stat=definition_stat(s.inputBase,definition);
        if(stat!=S_atk_pct && stat!=S_atk_flat && stat!=S_atk_caster_based_pct) continue;
        uint64_t value=scalarValue(s,row,who);
        if(stat==S_atk_pct) percent=f64Add(percent,value);
        else if(stat==S_atk_flat) flat=f64Add(flat,value);
        else flat=f64Add(flat,f64Mul(s.baseAttack[definition_owner(s.inputBase,definition)],f64Div(value,HUNDRED)));
    }
    return f64Add(f64Mul(s.baseAttack[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
}
[noinline]
void chooseEnemyVictims(inout Runtime s,uint step,uint64_t when)
{
    uint spec=enemyRuleAddress(s,step),rule=commands[spec],seats=commands[spec+1],slots=commands[spec+2],flags=commands[spec+3];
    uint rng=s.resourceOutput+P_ENEMY_RNG_BASE,before=results[rng+1];
    uint alive=31U & ~s.downMask,mask=0,order=0,count=0,taunt=0,poolMask=0;
    if(rule==0)
    { for(uint who=0;who<5;who++) if((alive&(1U<<who))!=0) { mask|=1U<<who;order|=(who+1)<<(3*count++); } }
    else
    {
        uint candidates=(flags&1)!=0 ? 0 : currentTaunters(s,when);
        for(uint who=0;who<5 && count<seats;who++) if((candidates&(1U<<who))!=0)
        { mask|=1U<<who;order|=(who+1)<<(3*count++); }
        taunt=mask;
        if(rule==1)
        {
            for(uint i=0;i<seats && count<seats;i++)
            {
                uint who=((slots>>(3*i))&7)-1,bit=1U<<who;
                if((alive&bit)!=0 && (mask&bit)==0) { mask|=bit;order|=(who+1)<<(3*count++); }
            }
        }
        else
        {
            uint rest=alive & ~mask;
            // Query stealth even if taunters filled every seat: native builds pool first.
            for(uint who=0;who<5;who++) if((rest&(1U<<who))!=0 && !targetStealth(s,who,when)) poolMask|=1U<<who;
            if(poolMask==0) poolMask=rest;
            uint population=0,pool[5];
            for(uint who=0;who<5;who++) if((poolMask&(1U<<who))!=0) pool[population++]=who;
            uint requested=min(seats-count,population),picked=0;
            if(requested!=0)
            {
                if(rule==2)
                {
                    uint sampled;mtSampleFive(rng,population,requested,sampled);
                    for(uint i=0;i<population;i++) if((sampled&(1U<<i))!=0) picked|=1U<<pool[i];
                }
                else
                {
                    uint sorted[5];uint64_t keys[5];uint size=0;
                    for(uint i=0;i<population;i++)
                    {
                        uint who=pool[i],pos=size;uint64_t key=bossTargetAttack(s,who,when);
                        if(!f64Finite(key)) { s.error=16;return; }
                        while(pos>0 && f64Less(keys[pos-1],key)) { keys[pos]=keys[pos-1];sorted[pos]=sorted[pos-1];pos--; }
                        keys[pos]=key;sorted[pos]=who;size++;
                    }
                    for(uint i=0;i<requested;i++) picked|=1U<<sorted[i];
                }
            }
            // Native sample/rank membership is projected back into squad order.
            for(uint who=0;who<5;who++) if((picked&(1U<<who))!=0) { mask|=1U<<who;order|=(who+1)<<(3*count++); }
        }
    }
    uint output=enemyQueryAddress(s,step);
    results[output]=mask;results[output+1]=order;results[output+2]=taunt;results[output+3]=poolMask;
    results[output+4]=before;results[output+5]=results[rng+1];results[output+6]=results[rng+3];results[output+7]=1;
}
[noinline]
bool validEnemyTargeting(inout Runtime s)
{
    uint meta=s.inputBase+P_ENEMY_TARGET_META_BASE,enabled=commands[meta],features=0;
    if(enabled>1 || enabled!=0 && s.combat==0) return false;
    for(uint i=3;i<8;i++) if(commands[meta+i]!=0) return false;
    if(enabled==0 && (commands[meta+1]!=0 || commands[meta+2]!=0)) return false;
    for(uint row=0;row<s.count;row++)
    {
        uint stat=definition_stat(s.inputBase,row);
        if(stat!=S_taunt && stat!=S_stealth) continue;
        Definition d=readDefinition(s.inputBase,row);
        features++;
        if(d.kind!=0 || !f64Finite(d.value) || d.alliedFlags!=0 || d.healthScaling!=0 || d.damageFlags!=0 || d.enemyBuff!=0 && d.stat!=S_taunt) return false;
        if(d.enemyBuff==0)
            for(uint j=0;j<P_DAMAGE_DEFINITION_WORDS;j++) if(commands[s.inputBase+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS+j]!=0) return false;
    }
    for(uint step=0;step<P_COMMANDS;step++)
    {
        uint at=s.inputBase+P_ENEMY_TARGET_COMMAND_BASE+step*4;
        bool active=step<commands[s.inputBase+2] && commands[s.inputBase+P_COMMAND_BASE+step*8]==32;
        if(!active) { for(uint j=0;j<4;j++) if(commands[at+j]!=0) return false;continue; }
        features++;
        uint rule=commands[at],count=commands[at+1],slots=commands[at+2],flags=commands[at+3];
        if(rule>3 || flags>1 || rule==0 && (count!=0 || slots!=0 || flags!=0) || rule!=0 && (count==0 || count>5)) return false;
        if(rule!=1 && slots!=0) return false;
        if(rule==1)
        {
            uint previous=0;
            for(uint i=0;i<5;i++)
            {
                uint encoded=(slots>>(3*i))&7;
                if(i>=count ? encoded!=0 : encoded==0 || encoded>5 || encoded<=previous) return false;
                previous=encoded;
            }
            if((slots>>15)!=0) return false;
        }
    }
    return (enabled!=0)==(features!=0 || worldFrameEnabled(s));
}
