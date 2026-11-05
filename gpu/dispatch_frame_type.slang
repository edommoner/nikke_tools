// Shared event frame definition for local and resource storage.
struct Frame
{
#ifdef PORTABLE_ATTACK_GROUPS
    uint attackGroup;
#endif
#ifdef PORTABLE_PARENT_FIXED_DAMAGE
    uint64_t notifyDealt;
#endif
    uint hitCrit;
    uint64_t skillCritRate,interruptAmount;
    uint interruptReach;
    uint mode, event, owner, cursor, target, repeatRow, repeatLeft, repeatPassive;
    int argument;
    uint64_t value, time, healthValue, healthPrevious, healthNext, gaugeFlat;
};
