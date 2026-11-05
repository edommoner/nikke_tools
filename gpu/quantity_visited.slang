// Visited membership only; quantity values, flags and first-seen order stay separate.
struct QuantityVisited
{
    uint words[(P_DEFINITIONS + 31U) / 32U];
    [mutating] [ForceInline] void initialize(uint groups)
    {
        for (uint i = 0; i < (groups + 31U) / 32U; i++) words[i] = 0;
    }
    // Caller validates group < initialized group count <= P_DEFINITIONS.
    [mutating] [ForceInline] bool insert(uint group)
    {
        uint word = group >> 5U, bit = 1U << (group & 31U);
        bool fresh = (words[word] & bit) == 0;
        words[word] |= bit;
        return fresh;
    }
};
