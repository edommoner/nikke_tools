// Reuse the complete skill entry, scheduler and weapon phases. Hooks are inert
// for all retained HSI1/HSI2 inputs and enabled only by an explicit HSI3 header.
#define PORTABLE_DESTRUCTIBLE_WEAPON
#define WEAPON_TYPED_DAMAGE(s,who,w,coefficient,when,legacy) (destructibleWeaponEnabled(s)?destructibleWeaponSample(s,who,w,coefficient,when):(legacy))
#define WEAPON_TYPED_PELLET(s,w,who,when,output,hit,amount) destructibleWeaponPellet(s,who,when,hit)
#define WEAPON_BODY_SUPPRESSED(s,who,hit) (destructibleWeaponEnabled(s)&&results[destructibleWeaponBank(s,who)+64+(hit)]!=0)
#define WEAPON_BODY_AMOUNT(s,who,legacy) destructibleWeaponBodyAmount(s,who,legacy)
#include "destructible_shield_battle_entry.slang"
#include "destructible_weapon_runtime.slang"
