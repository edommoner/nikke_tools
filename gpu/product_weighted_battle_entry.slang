// Original product scheduler and shared weighted landing; literal bank only.
#define PORTABLE_WEIGHTED_INCOMING
#define PORTABLE_PRODUCT_UNSPECIFIED_WEIGHTED
#include "weighted_incoming_layout.slang"
#define portableEvents unusedProductWeightedBaseEntry
#include "product_battle_entry.slang"
#undef portableEvents
#include "product_weighted_entry.slang"
