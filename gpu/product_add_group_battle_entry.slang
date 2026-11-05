#define PORTABLE_ADD_ATTACK_BATTLE
#define PORTABLE_ADD_SELF_DESTRUCT
#include "world_add_attack_battle_layout.slang"
#include "add_self_destruct_layout.slang"
#define portableEvents unusedProductAddBaseEntry
#include "product_group_battle_entry.slang"
#undef portableEvents
static const uint PRODUCT_ADD_PREFIX=104408U;
#include "product_add_entry.slang"
