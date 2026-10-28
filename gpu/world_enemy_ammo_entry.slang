#define PORTABLE_ENEMY_AMMO
// The original roster consumes a named resource and emits ammo events through
// the existing resource executor. Keep the actor/landing gate opt-in; resource
// wire validation and the common consume handler remain authoritative.
#define WORLD_ENEMY_AMMO_RESOURCE_KIND(s,row,d,legacy) (d.kind==11 && worldSkillsEnabled(s) && resourceDefinition(s,row).op==3 && (resourceDefinition(s,row).flags&2)!=0 ? false : (legacy))
#include "enemy_ammo_layout.slang"
#include "world_add_attack_battle_entry.slang"
#include "enemy_ammo_runtime.slang"
