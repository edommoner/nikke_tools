// Two disjoint padding banks preserve all64 full binary64 dictionary cells.
uint nativeNumericCell(uint output,uint index)
{
    uint bank=index<P_NATIVE_QUERY_BANK_COUNT ? P_NATIVE_QUERY_BANK0_BASE : P_NATIVE_QUERY_BANK1_BASE;
    return output+bank+(index%P_NATIVE_QUERY_BANK_COUNT)*P_NATIVE_QUERY_CELL_WORDS;
}
