// Original actual-shot groups and weighted landing share the same executor.
#define PORTABLE_WEIGHTED_INCOMING
#define PORTABLE_PRODUCT_UNSPECIFIED_WEIGHTED
#include "weighted_incoming_layout.slang"
#define portableEvents unusedProductWeightedGroupBaseEntry
#include "product_group_battle_entry.slang"
#undef portableEvents
#include "product_weighted_group_entry.slang"
