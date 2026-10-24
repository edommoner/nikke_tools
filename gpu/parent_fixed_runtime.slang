// Notification-local quantity, not an ATK coefficient or another named hit.
bool validParentFixed(inout Runtime s,uint row,Definition d)
{
    if((d.damageFlags&262144U)==0) return true;
    if(d.damageFlags!=262144U || d.damageHits!=1 || d.damageNormal!=0 || d.damagePending!=0 || !f64Zero(d.damageGauge) || d.periodicFlags!=0 || !f64Zero(d.interval) || skillHPBasisMode(s,row)!=0 || referenceScaleMode(s,row)!=0 || (commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4]&3)!=0) return false;
    s.quantityMask|=0x01000000U;return true;
}
void enqueueParentFixed(inout Runtime s,Definition d,uint row,Frame frame,int depth)
{
    uint64_t raw=f64Div(f64Mul(frame.notifyDealt,d.value),HUNDRED);
    if(!f64Finite(raw)) { s.error=16;return; }
    if(!f64Less(0,raw)) return;
    uint status;uint64_t amount=f64ToI64(raw,1,status);
    if(status!=0) { s.error=16;return; }
    // A positive fraction truncates to0 yet still makes the native packet.
#ifdef PORTABLE_COORDINATE_PHYSICAL
    captureCoordinatePhysicalBodyOnly(s,row,uint(depth));
    if(s.error!=0)return;
#endif
    enqueueLanding(s,row,frame.target,0xffffffffU,0,f64FromI64(amount),frame.time,1,1,uint(depth+1),s.enemyEpoch);
}
