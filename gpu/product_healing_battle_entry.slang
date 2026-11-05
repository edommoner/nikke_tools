// Product projection around the existing shared scheduler/ADD healing consumer.
#define PORTABLE_PRODUCT_ENEMY_HEALING
#define PORTABLE_ENEMY_HEALING
#include "enemy_healing_layout.slang"
#define portableEvents unusedProductHealingBaseEntry
#ifdef PORTABLE_PRODUCT_HEALING_GROUP
#include "product_group_battle_entry.slang"
#else
#include "product_battle_entry.slang"
#endif
#undef portableEvents
#include "enemy_healing_runtime.slang"
#include "product_healing_entry.slang"
