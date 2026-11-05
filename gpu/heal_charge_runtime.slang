// A scalar received-healing pool. The typed protection allocator owns storage;
// kind10 is never shield/decoy absorption or per-recipient excess-heal storage.
#if defined(PORTABLE_HEAL_SHARE_DIAGNOSTIC) || defined(PORTABLE_NATIVE_QUERY_DIAGNOSTIC)
#error Healing charge observations and heal-share diagnostic cannot share a bank
#endif
static const uint HEAL_CHARGE_DONE=262144U;
bool healChargeEnabled(inout Runtime s) { return (commands[s.inputBase+P_PROTECTION_META_BASE]&64U)!=0; }
#include "heal_charge_history.slang"
void traceHealCharge(inout Runtime s,uint kind,uint row,uint who,uint64_t when,uint64_t before,uint64_t after,uint64_t cap,uint64_t amount)
{
    if(!healChargeEnabled(s)) return;
    uint head=s.resourceOutput+771072,index=results[head+2];
    if(index>=1048576U) { s.error=64;return; }
    uint words[20];for(uint i=0;i<20;i++) words[i]=0;
    words[0]=kind;words[1]=row;words[2]=who;
    words[3]=uint(when);words[4]=uint(when>>32);words[5]=uint(before);words[6]=uint(before>>32);
    words[7]=uint(after);words[8]=uint(after>>32);words[9]=uint(cap);words[10]=uint(cap>>32);words[11]=uint(amount);words[12]=uint(amount>>32);
    results[head]=0x48434731U;results[head+2]=index+1;
    if(index<512)
    {
        results[head+1]=index+1;uint at=head+8+index*20;
        for(uint i=0;i<20;i++) results[at+i]=words[i];
    }
    else
    {
        uint tail=s.resourceOutput+HEAL_CHARGE_HISTORY_TAIL;
        if(index==512) beginHealChargeHistory(head,tail);
        hashHealChargeRecord(tail,words);results[head+6]=index+1-512;
    }
}
[noinline]
void sweepHealCharge(inout Runtime s)
{
    if(!healChargeEnabled(s)) return;
    for(uint object=0;object<P_PROTECTION_OBJECTS;object++)
    {
        uint at=protectionAddress(s,object),flags=results[at+22];if((flags&255U)!=10) continue;
        if(!protectionObjectActive(s,object) && ((flags&PROTECTION_ENDED)==0 || (flags&HEAL_CHARGE_DONE)!=0))
        { results[at+22]=0;storeNumber(at,0); }
    }
}
// Native retirement happens after recipient removal, before down notifications.
// Live persistent/shared carriers survive, even when their caster is down.
[noinline]
void retireHealChargeDown(inout Runtime s,uint who)
{
    if(!healChargeEnabled(s)) return;
    for(uint object=0;object<P_PROTECTION_OBJECTS;object++)
    {
        uint at=protectionAddress(s,object),flags=results[at+22];
        if((flags&255U)!=10 || protectionObjectActive(s,object)) continue;
        if(((flags>>10)&7)==who || (flags&PROTECTION_ENDED)==0 || (flags&HEAL_CHARGE_DONE)!=0)
        { results[at+22]=0;storeNumber(at,0); }
    }
}
void retainHealChargeEnd(inout Runtime s,uint slot)
{
    if(!healChargeEnabled(s) || definition_stat(s.inputBase,s.carrierDefinition[slot])!=76U) return;
    uint object=protectionObject(s,slot);if(object==PROTECTION_NONE) return;uint at=protectionAddress(s,object);
    if((results[at+22]&HEAL_CHARGE_DONE)==0 && (s.downMask&(1U<<definition_owner(s.inputBase,s.carrierDefinition[slot])))==0)
        results[at+22]|=PROTECTION_RESERVED|PROTECTION_ENDED;
}
[noinline]
void buildHealCharge(inout Runtime s,uint slot,uint64_t when)
{
    sweepHealCharge(s);Definition d=residentDefinition(s,slot);uint64_t values[64];
    uint saved=s.target;s.target=0;collectStats(s,d.owner,when,values);s.target=saved;
    uint64_t attack=f64Add(f64Mul(s.baseAttack[d.owner],f64Add(ONE,f64Div(values[S_atk_pct],HUNDRED))),values[S_atk_flat]);
    uint64_t cap=larger(0,f64Div(f64Mul(attack,scalarValue(s,slot,d.owner)),HUNDRED));
    if(!f64Finite(cap)) { s.error=16;return; }
    uint object=allocateProtection(s,slot,10U|(d.owner<<10));if(s.error!=0) return;uint at=protectionAddress(s,object);
    results[at+22]=10U|(d.owner<<10);results[at+4]=d.name;
    storeNumber(at,0);storeNumber(at+2,cap);
    traceHealCharge(s,1,s.carrierDefinition[slot],d.owner,when,0,0,cap,cap);
}
[noinline]
uint64_t healChargeCapacity(inout Runtime s,uint object,uint64_t when)
{
    uint at=protectionAddress(s,object),owner=(results[at+22]>>10)&7,name=results[at+4];uint64_t bonus=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind!=0 || d.stat!=77U || !queryRecipient(s,row,owner,when)) continue;
        if((protectionPolicy(s,s.carrierDefinition[row])&256U)!=0 && d.targetName!=name) continue;
        bonus=f64Add(bonus,scalarValue(s,row,owner));
    }
    return larger(0,f64Mul(protectionNumber(at+2),f64Add(ONE,f64Div(bonus,HUNDRED))));
}
[noinline]
void collectHealCharge(inout Runtime s,uint who,uint64_t amount,uint64_t when)
{
    if(!healChargeEnabled(s) || !f64Less(0,amount) || (s.downMask&(1U<<who))!=0) return;
    sweepHealCharge(s);
    for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass];if(definition_stat(s.inputBase,s.carrierDefinition[slot])!=76U || !queryRecipient(s,slot,who,when)) continue;
        uint object=protectionObject(s,slot);if(object==PROTECTION_NONE) continue;uint at=protectionAddress(s,object);
        if((results[at+22]&HEAL_CHARGE_DONE)!=0) continue;
        uint64_t cap=healChargeCapacity(s,object,when),before=protectionNumber(at);
        uint64_t after=f64Add(before,smaller(amount,larger(0,f64Add(cap,before^F64_SIGN))));
        if(!f64Finite(cap) || !f64Finite(after)) { s.error=16;return; }
        storeNumber(at,after);traceHealCharge(s,2,s.carrierDefinition[slot],who,when,before,after,cap,amount);
    }
}
[noinline]
uint64_t takeHealCharge(inout Runtime s,uint owner,uint name,uint row,uint64_t when)
{
    sweepHealCharge(s);uint64_t amount=0;uint previous=0;
    if((s.downMask&(1U<<owner))!=0) return 0;
    for(uint pass=0;pass<P_PROTECTION_OBJECTS;pass++)
    {
        uint selected=PROTECTION_NONE,best=0xffffffffU;
        for(uint object=0;object<P_PROTECTION_OBJECTS;object++)
        {
            uint at=protectionAddress(s,object),flags=results[at+22],order=results[at+20];
            if((flags&255U)!=10 || (flags&HEAL_CHARGE_DONE)!=0 || ((flags>>10)&7)!=owner || results[at+4]!=name || order<=previous || order>=best) continue;
            if(!protectionObjectActive(s,object) && (flags&PROTECTION_ENDED)==0) continue;
            selected=object;best=order;
        }
        if(selected==PROTECTION_NONE) break;previous=best;uint at=protectionAddress(s,selected);
        amount=f64Add(amount,protectionNumber(at));storeNumber(at,0);results[at+22]=(results[at+22]|HEAL_CHARGE_DONE)&~(PROTECTION_RESERVED|PROTECTION_ENDED);
    }
    if(!f64Finite(amount)) { s.error=16;return 0; }
    traceHealCharge(s,3,row,owner,when,amount,0,0,amount);return amount;
}
[noinline]
void advanceHealChargeDischarge(inout Runtime s,inout DISPATCH_FRAMES(frames),inout int depth,Frame f)
{
    uint encoded=f.cursor<21 ? uint(f.value>>(f.cursor*3))&7 : 0;
    if(encoded==0) { depth--;return; }frames[depth].cursor++;
    uint who=encoded-1;if((s.downMask&(1U<<who))!=0) return;
    uint64_t amount=f64Mul(f.healthValue,healMultiplier(s,who,f.owner,f.time));
    if(!f64Finite(amount)) { s.error=16;return; }
    if(healShareFrameEnabled(s)) { pushFrame(s,frames,depth,31,0,who,int(f.owner),f.time);if(s.error==0) BEGIN_DISPATCH_HEAL_SHARE(s,frames,depth,amount,f.owner); }
    else
    {
        uint64_t before=s.hp[who];s.hp[who]=storageBodyHeal(s,who,amount,f.time);
        s.healing[who]=f64Add(s.healing[who],larger(0,f64Add(s.hp[who],before^F64_SIGN)));syncHealthActor(s,who,f.time);
        pushFrame(s,frames,depth,0,16,who,int(f.owner),f.time);
    }
}
bool validHealCharge(inout Runtime s,uint row,Definition d,uint policy)
{
    uint kind=policy&255;
    if(kind<10 || kind>12 || (policy&~511U)!=0 || (policy&256U)!=0 && kind!=11 || s.combat==0 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U ||
       d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.quantityFlags!=0 || d.damageFlags!=0 || !f64Finite(d.value) || !f64Zero(d.interval)) return false;
    if(kind==10 && (d.kind!=0 || d.stat!=76U) || kind==11 && (d.kind!=0 || d.stat!=77U) || kind==12 && (d.kind!=32 || d.stat!=0 || uint(d.targetName)>=P_DEFINITIONS)) return false;
    if(kind==11 && (policy&256U)!=0 && uint(d.targetName)>=P_DEFINITIONS) return false;
    return validRecipientPlan(s.inputBase+P_RECIPIENT_BASE+row*8,false,s.inputBase);
}
