// Generated from portable_enemy_healing_wire; literal declarations only.
static const uint EHL_MAGIC=1162366001U;
static const uint EHL_VERSION=1U;
#ifdef PORTABLE_PRODUCT_TYPED_HEALING
static const uint EHL_BASE=EMB_INPUT+CDF_WORDS;
#else
static const uint EHL_BASE=115680U;
#endif
static const uint EHL_HEADER=16U;
static const uint EHL_ROWS=32U;
static const uint EHL_ROW_WORDS=136U;
static const uint EHL_ROW_BASE=16U;
static const uint EHL_TARGET_BASE=4U;
static const uint EHL_TARGETS=127U;
static const uint EHL_WORDS=4368U;
#ifdef PORTABLE_PRODUCT_TYPED_HEALING
static const uint EHL_INPUT_WORDS=EMB_INPUT+CDF_WORDS+4368U;
#else
static const uint EHL_INPUT_WORDS=120048U;
#endif
#ifdef PORTABLE_PRODUCT_TYPED_HEALING
static const uint EHL_OUTPUT_BASE=EMB_OUTPUT+CDF_OUTPUT_WORDS-CDF_OUTPUT_BASE;
#else
static const uint EHL_OUTPUT_BASE=1867648U;
#endif
static const uint EHL_OUTPUT_HEADER=16U;
static const uint EHL_SEEN_BASE=16U;
static const uint EHL_RECEIPT_BASE=48U;
static const uint EHL_RECEIPTS=1024U;
static const uint EHL_RECEIPT_WORDS=32U;
#ifdef PORTABLE_PRODUCT_TYPED_HEALING
static const uint EHL_OUTPUT_WORDS=EMB_OUTPUT+CDF_OUTPUT_WORDS-CDF_OUTPUT_BASE+32816U;
#else
static const uint EHL_OUTPUT_WORDS=2032000U;
#endif
