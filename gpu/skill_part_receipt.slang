// Full projectile-world tail, after the complete heal-share diagnostic log.
// Two words per immutable landing; never aliases the periodic at+7 snapshot.
static const uint SKILL_PART_BASE=781328;
uint skillPartReceiptAddress(uint at)
{
    uint output=(at/P_OUTPUT_WORDS)*P_OUTPUT_WORDS;
    uint index=(at-output-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    return output+SKILL_PART_BASE+index*2;
}
void storeSkillPartAmount(uint at,uint64_t amount)
{ storeNumber(skillPartReceiptAddress(at),amount); }
uint64_t loadSkillPartAmount(uint at)
{ return sourceNumber(skillPartReceiptAddress(at)); }
