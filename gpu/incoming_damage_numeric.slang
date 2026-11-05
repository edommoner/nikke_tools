// Ordered binary64 quantities shared by declared cover and body damage.
static const uint64_t INCOMING_NUMERIC_ONE=uint64_t(0x3ff00000)<<32;
static const uint64_t INCOMING_NUMERIC_HUNDRED=uint64_t(0x40590000)<<32;
uint64_t incomingNumericMax(uint64_t a,uint64_t b) { return f64Less(a,b)?b:a; }
uint64_t incomingDefensePercentage(uint64_t base,uint64_t percent)
{ return f64Mul(base,f64Add(INCOMING_NUMERIC_ONE,f64Div(percent,INCOMING_NUMERIC_HUNDRED))); }
uint64_t incomingDefendedQuantity(uint64_t attack,uint64_t coefficient,uint64_t defense,uint64_t received)
{
    uint64_t amount=incomingNumericMax(f64Add(attack,defense^F64_SIGN),0);
    amount=f64Div(f64Mul(amount,coefficient),INCOMING_NUMERIC_HUNDRED);
    amount=f64Mul(amount,incomingNumericMax(0,f64Add(INCOMING_NUMERIC_ONE,f64Div(received,INCOMING_NUMERIC_HUNDRED))));
    return incomingNumericMax(amount,INCOMING_NUMERIC_ONE);
}
