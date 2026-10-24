// HSI4 preserves original skill selectors and burst flags. All old headers keep
// the exact existing weapon/skill paths; no backend-specific implementation.
#define PORTABLE_DESTRUCTIBLE_ROSTER_SKILL
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(rosterShieldSkillsEnabled(s)?rosterShieldSkillDefinition(s,d):(d.damageFlags&~(H_NAMED_SKILL|524288U))==0))
#define DF_ROUTE_VALID(s,d) (rosterShieldSkillsEnabled(s)?((d).damageRoute>=1&&(d).damageRoute<=9):((d).damageRoute==1))
#define DF_CAPTURE_BODY(s,d,f) (!rosterShieldSkillsEnabled(s)||rosterShieldSkillBody(s,d,f))
#include "destructible_weapon_shield_entry.slang"
#include "destructible_roster_skill_runtime.slang"
