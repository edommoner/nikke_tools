// Ordered seven-factor product. Slots7/8 are captured no-core/part factors.
// This function reads values only; it cannot query stats or sample a hit again.
uint64_t damageFactorProduct(uint64_t factors[9], bool part)
{
    uint64_t raw = f64Mul(f64Div(factors[0],HUNDRED),factors[1]);
    raw = f64Mul(raw,part ? factors[7] : factors[2]);
    raw = f64Mul(raw,factors[3]);
    raw = f64Mul(raw,part ? factors[8] : factors[4]);
    raw = f64Mul(raw,factors[5]); raw = f64Mul(raw,factors[6]);
    return raw;
}
