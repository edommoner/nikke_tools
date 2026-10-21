// Generated from app/portable_specs.py; do not hand-edit.
#if defined(PORTABLE_WORLD_FRAME) && defined(PORTABLE_WIDE_LANDINGS)
#error World and wide-landing diagnostic layouts cannot be combined.
#endif
#ifdef PORTABLE_WORLD_PENDING_SKILLS
static const uint PORTABLE_ABI = 1346721411U;
#elif defined(PORTABLE_WORLD_SKILLS)
static const uint PORTABLE_ABI = 1346721410U;
#elif defined(PORTABLE_COUNTER_FIELDS)
static const uint PORTABLE_ABI = 1346721409U;
#elif defined(PORTABLE_COUNTER_CONTEXT)
static const uint PORTABLE_ABI = 1346721408U;
#elif defined(PORTABLE_COUNTER_LANDINGS)
static const uint PORTABLE_ABI = 1346721407U;
#elif defined(PORTABLE_TARGET_COUNTERS)
static const uint PORTABLE_ABI = 1346721406U;
#elif defined(PORTABLE_WORLD_ACTOR_STACKS)
static const uint PORTABLE_ABI = 1346721405U;
#elif defined(PORTABLE_WORLD_ACTOR_STATUS)
static const uint PORTABLE_ABI = 1346721404U;
#elif defined(PORTABLE_WORLD_ACTOR_RECIPIENTS)
static const uint PORTABLE_ABI = 1346721403U;
#elif defined(PORTABLE_WORLD_ACTOR_MUTATION)
static const uint PORTABLE_ABI = 1346721402U;
#elif defined(PORTABLE_WORLD_ACTOR_STATE)
static const uint PORTABLE_ABI = 1346721401U;
#elif defined(PORTABLE_WORLD_ACTOR_FIELDS)
static const uint PORTABLE_ABI = 1346721400U;
#elif defined(PORTABLE_WORLD_ACTOR_POOLS)
static const uint PORTABLE_ABI = 1346721399U;
#elif defined(PORTABLE_WORLD_ACTORS)
static const uint PORTABLE_ABI = 1346721398U;
#elif defined(PORTABLE_WORLD_OVERLAYS)
static const uint PORTABLE_ABI = 1346721397U;
#elif defined(PORTABLE_WORLD_FRAME)
static const uint PORTABLE_ABI = 1346721396U;
#else
static const uint PORTABLE_ABI = 1346721395U;
#endif
static const uint P_PROTECTION_OBJECTS = 1024U;
static const uint P_PROTECTION_OBJECT_WORDS = 24U;
static const uint P_REMOVALS = 4096U;
static const uint P_LANDINGS = 2048U;
#ifdef PORTABLE_WIDE_LANDINGS
static const uint P_LANDING_WORDS = 12U;
#else
static const uint P_LANDING_WORDS = 8U;
#endif
static const uint P_SOURCES = 64U;
static const uint P_SOURCE_SLOTS = 32U;
static const uint P_SOURCE_DEFINITION_WORDS = 72U;
static const uint P_SOURCE_STATE_WORDS = 12U;
static const uint P_RESOURCE_KEYS = 256U;
static const uint P_BATCH = 2048U;
static const uint P_PENDING = 512U;
static const uint P_TRIGGERS = 8U;
static const uint P_CONDITIONS = 3U;
static const uint P_DEFINITIONS = 256U;
static const uint P_CARRIERS = 512U;
static const uint P_LAZY_CACHE = 1024U;
static const uint P_COMMANDS = 64U;
static const uint P_DEPTH = 32U;
static const uint P_TRACE = 128U;
static const uint P_BURST_TRACE = 128U;
static const uint P_DEFINITION_WORDS = 32U;
static const uint P_DAMAGE_DEFINITION_WORDS = 8U;
static const uint P_CARRIER_WORDS = 23U;
static const uint P_QUERY_WORDS = 32U;
static const uint P_TRACE_WORDS = 8U;
static const uint P_INCOMING_WORDS = 4U;
static const uint P_INCOMING_QUERY_WORDS = 20U;
static const uint P_HEALTH_WORDS = 8U;
static const uint P_HEALTH_DEFINITION_WORDS = 4U;
static const uint P_HEALTH_QUERY_WORDS = 50U;
static const uint P_DEFINITION_EXTRA_WORDS = 8U;
static const uint P_WEAPON_QUANTITY_WORDS = 4U;
static const uint P_WEAPON_MECHANICS_WORDS = 28U;
static const uint P_MODE_TIMING_WORDS = 8U;
static const uint P_WEAPON_STATE_WORDS = 16U;
static const uint P_EVENT_WORDS = 64U;
static const uint P_CONDITION_WORDS = 12U;
static const uint P_MODE_WORDS = 32U;
static const uint P_WEAPON_WORDS = 16U;
static const uint P_TARGET_WORDS = 8U;
static const uint P_COMBAT_QUERY_WORDS = 40U;
static const uint P_COMBAT_STATE_QUERY_WORDS = 128U;
static const uint P_MASK_WORDS = 8U;
static const uint P_RECIPIENT_NODES = 256U;
static const uint P_COVER_BASE = 32U;
static const uint P_DEFINITION_BASE = 56U;
static const uint P_COMMAND_BASE = 8248U;
static const uint P_WEAPON_BASE = 8760U;
static const uint P_TARGET_BASE = 8840U;
static const uint P_WEAPON_EXTRA_BASE = 8904U;
static const uint P_MODE_BASE = 8928U;
static const uint P_EVENT_BASE = 17120U;
static const uint P_CONDITION_BASE = 33504U;
static const uint P_ATTACK_CONTEXT_BASE = 36576U;
static const uint P_WEAPON_MECHANICS_BASE = 36584U;
static const uint P_MODE_TIMING_BASE = 36728U;
static const uint P_DEFINITION_EXTRA_BASE = 38776U;
static const uint P_WEAPON_QUANTITY_BASE = 40824U;
static const uint P_HEALTH_BASE = 40848U;
static const uint P_HEALTH_DEFINITION_BASE = 40888U;
static const uint P_INCOMING_BASE = 41912U;
static const uint P_FORCE_BASE = 42168U;
static const uint P_RECIPIENT_BASE = 44216U;
static const uint P_BULLET_DEFINITION_BASE = 46264U;
static const uint P_DAMAGE_DEFINITION_BASE = 46776U;
static const uint P_PENDING_EXCLUDE_BASE = 48824U;
static const uint P_DURATION_DEFINITION_BASE = 50872U;
static const uint P_EVENT_CANDIDATE_BASE = 51384U;
static const uint P_TARGET_ATTACK_BASE = 51896U;
static const uint P_AIM_POLICY_BASE = 51912U;
static const uint P_PERIODIC_DEFINITION_BASE = 51920U;
static const uint P_RESOURCE_META_BASE = 52432U;
static const uint P_RESOURCE_DEFINITION_BASE = 52440U;
static const uint P_RESOURCE_CONDITION_BASE = 55000U;
static const uint P_REFERENCE_DEFINITION_BASE = 55768U;
static const uint P_RESOURCE_NAME_BASE = 56792U;
static const uint P_SOURCE_DEFINITION_BASE = 57048U;
static const uint P_STAGED_DEFINITION_BASE = 75480U;
static const uint P_STAGED_INDEX_BASE = 77528U;
static const uint P_LANDING_META_BASE = 77792U;
static const uint P_STATUS_META_BASE = 77800U;
static const uint P_PROTECTION_META_BASE = 77808U;
static const uint P_PROTECTION_DEFINITION_BASE = 77816U;
#ifdef PORTABLE_TARGET_COUNTERS
static const uint P_INPUT_WORDS = 97464U;
#elif defined(PORTABLE_WORLD_ACTOR_STATE)
static const uint P_INPUT_WORDS = 92336U;
#elif defined(PORTABLE_WORLD_ACTOR_POOLS)
static const uint P_INPUT_WORDS = 92208U;
#elif defined(PORTABLE_WORLD_ACTORS)
static const uint P_INPUT_WORDS = 90536U;
#elif defined(PORTABLE_WORLD_OVERLAYS)
static const uint P_INPUT_WORDS = 89376U;
#elif defined(PORTABLE_WORLD_FRAME)
static const uint P_INPUT_WORDS = 88848U;
#else
static const uint P_INPUT_WORDS = 86016U;
#endif
static const uint P_RECIPIENT_META_BASE = 81920U;
static const uint P_RECIPIENT_NODE_BASE = 81928U;
static const uint P_WORLD_META_BASE = 51913U;
static const uint P_WORLD_META_WORDS = 7U;
static const uint P_GEOMETRY_BASE = 83976U;
static const uint P_GEOMETRY_WORDS = 1592U;
static const uint P_BURST_REFERENCE_BASE = 85568U;
static const uint P_BURST_REFERENCE_WORDS = 32U;
static const uint P_QUERY_BASE = 16U;
static const uint P_TRACE_BASE = 2064U;
static const uint P_STATE_BASE = 3088U;
static const uint P_TIMER_TARGET_BASE = 5648U;
static const uint P_BURST_TRACE_BASE = 6160U;
static const uint P_COMBAT_QUERY_BASE = 7184U;
static const uint P_TARGET_STATE_BASE = 9744U;
static const uint P_COMBAT_STATE_QUERY_BASE = 9824U;
static const uint P_COUNTER_STATE_BASE = 18016U;
static const uint P_PERIOD_STATE_BASE = 20064U;
static const uint P_WEAPON_STATE_BASE = 21088U;
static const uint P_HEALTH_QUERY_BASE = 21168U;
static const uint P_HEALTH_STATE_BASE = 24368U;
static const uint P_INCOMING_QUERY_BASE = 24424U;
static const uint P_INCOMING_STATE_BASE = 25704U;
static const uint P_TIMER_MASK_BASE = 25728U;
static const uint P_CARRIER_STATE_BASE = 26240U;
static const uint P_DAMAGE_TRACE_BASE = 38016U;
static const uint P_DAMAGE_ACCOUNTING_QUERY_BASE = 39296U;
static const uint P_DAMAGE_ACCOUNTING_STATE_BASE = 41856U;
static const uint P_COVER_QUERY_BASE = 41912U;
static const uint P_COVER_STATE_BASE = 44472U;
static const uint P_PENDING_QUERY_BASE = 44512U;
static const uint P_PENDING_STATE_BASE = 44768U;
static const uint P_PENDING_TRACE_BASE = 48872U;
static const uint P_PERIODIC_STATE_BASE = 49384U;
static const uint P_RESOURCE_STATE_BASE = 52456U;
static const uint P_RESOURCE_QUERY_BASE = 58856U;
static const uint P_RESOURCE_HEADER_BASE = 59624U;
static const uint P_RESOURCE_TRACE_BASE = 59632U;
static const uint P_RESOURCE_STEP_HEAD_BASE = 60656U;
static const uint P_RESOURCE_STEP_NEXT_BASE = 61936U;
static const uint P_REFERENCE_CAPTURE_BASE = 63984U;
static const uint P_SOURCE_HEADER_BASE = 65520U;
static const uint P_SOURCE_STATE_BASE = 65528U;
static const uint P_SOURCE_LOOKUP_BASE = 66296U;
static const uint P_SOURCE_QUERY_BASE = 67576U;
static const uint P_STAGED_HEADER_BASE = 68088U;
static const uint P_STAGED_STATE_BASE = 68096U;
static const uint P_LANDING_HEADER_BASE = 69632U;
static const uint P_LANDING_STATE_BASE = 69640U;
#ifdef PORTABLE_WIDE_LANDINGS
static const uint P_REMOVAL_QUEUE_BASE = 94216U;
#else
static const uint P_REMOVAL_QUEUE_BASE = 86024U;
#endif
#ifdef PORTABLE_WIDE_LANDINGS
static const uint P_STACK_NOTICE_VALUE_BASE = 96264U;
#else
static const uint P_STACK_NOTICE_VALUE_BASE = 88072U;
#endif
static const uint P_IMMUNITY_USED_BASE = 92168U;
static const uint P_IMMUNITY_SCRATCH_BASE = 98824U;
static const uint P_PROTECTION_HIT_BASE = 99848U;
static const uint P_PROTECTION_QUERY_BASE = 104968U;
static const uint P_PROTECTION_STATE_BASE = 108168U;
static const uint P_PROTECTION_MAP_BASE = 108224U;
static const uint P_PROTECTION_SELECTION_BASE = 108736U;
static const uint P_PROTECTION_OBJECT_BASE = 109248U;
static const uint P_PROTECTION_BUILD_BASE = 133824U;
#ifdef PORTABLE_WORLD_ACTOR_RECIPIENTS
static const uint P_OUTPUT_WORDS = 524288U;
#elif defined(PORTABLE_WORLD_ACTOR_FIELDS)
static const uint P_OUTPUT_WORDS = 262144U;
#elif defined(PORTABLE_WORLD_ACTOR_POOLS)
static const uint P_OUTPUT_WORDS = 253952U;
#elif defined(PORTABLE_WORLD_FRAME)
static const uint P_OUTPUT_WORDS = 225280U;
#else
#ifdef PORTABLE_WIDE_LANDINGS
static const uint P_OUTPUT_WORDS = 167936U;
#else
static const uint P_OUTPUT_WORDS = 159744U;
#endif
#endif
static const uint P_SPLIT_HIT_BASE = 135168U;
static const uint P_RECIPIENT_ORDER_BASE = 155648U;
#ifdef PORTABLE_WIDE_LANDINGS
static const uint P_PROBABILITY_STATE_BASE = 164864U;
#else
static const uint P_PROBABILITY_STATE_BASE = 156672U;
#endif
static const uint P_PROBABILITY_STATE_WORDS = 2560U;
static const uint P_MODE_ENTRY_STATE_BASE = 159232U;
static const uint P_MODE_ENTRY_STATE_WORDS = 10U;
static const uint P_ENEMY_TARGET_META_BASE = 85600U;
static const uint P_ENEMY_TARGET_COMMAND_BASE = 85608U;
static const uint P_ENEMY_RNG_BASE = 133840U;
static const uint P_ENEMY_RNG_WORDS = 632U;
static const uint P_ENEMY_TARGET_QUERY_BASE = 134472U;
static const uint P_WORLD_FRAME_ABI = 1346721396U;
static const uint P_WORLD_FRAME_INPUT_BASE = 86016U;
static const uint P_WORLD_FRAME_PAYLOAD_BASE = 88336U;
static const uint P_WORLD_FRAME_INPUT_WORDS = 88848U;
static const uint P_WORLD_FRAME_OUTPUT_BASE = 159744U;
static const uint P_WORLD_FRAME_OUTPUT_WORDS = 225280U;
static const uint P_WORLD_FRAME_TARGET_BASE = 174864U;
static const uint P_WORLD_FRAME_HIT_BASE = 183056U;
static const uint P_WORLD_OVERLAY_ABI = 1346721397U;
static const uint P_WORLD_OVERLAY_INPUT_BASE = 88848U;
static const uint P_WORLD_OVERLAY_NODE_BASE = 88864U;
static const uint P_WORLD_OVERLAY_INPUT_WORDS = 89376U;
static const uint P_WORLD_OVERLAY_STATE_BASE = 215824U;
static const uint P_WORLD_OVERLAY_PAUSE_BASE = 216112U;
static const uint P_WORLD_OVERLAY_CHARGE_BASE = 216152U;
static const uint P_WORLD_OVERLAY_STATE_WORDS = 368U;
static const uint P_WORLD_ACTOR_ABI = 1346721398U;
static const uint P_WORLD_ACTORS = 128U;
static const uint P_WORLD_ACTOR_INPUT_BASE = 89376U;
static const uint P_WORLD_ACTOR_NODE_BASE = 89384U;
static const uint P_WORLD_ACTOR_BINDING_BASE = 89512U;
static const uint P_WORLD_ACTOR_INPUT_WORDS = 90536U;
static const uint P_WORLD_ACTOR_STATE_BASE = 216192U;
static const uint P_WORLD_ACTOR_QUERY_BASE = 217224U;
static const uint P_WORLD_ACTOR_STATE_WORDS = 1544U;
static const uint P_WORLD_SKILL_ABI = 1346721410U;
static const uint P_WORLD_PENDING_ABI = 1346721411U;
static const uint P_WORLD_SKILL_HEAD_BASE = 512184U;
static const uint P_WORLD_SKILL_TRACE_BASE = 512192U;
static const uint P_COUNTER_FIELD_ABI = 1346721409U;
static const uint P_COUNTER_FIELD_WORK_BASE = 512176U;
static const uint P_COUNTER_CONTEXT_ABI = 1346721408U;
static const uint P_COUNTER_CONTEXT_BASE = 511080U;
static const uint P_COUNTER_LANDING_ABI = 1346721407U;
static const uint P_COUNTER_LANDING_PACKET_BASE = 509488U;
static const uint P_COUNTER_LANDING_SHOT_BASE = 509504U;
static const uint P_COUNTER_LANDING_PART_BASE = 509544U;
static const uint P_COUNTER_LANDING_EXTRA_BASE = 510568U;
static const uint P_TARGET_COUNTER_ABI = 1346721406U;
static const uint P_TARGET_COUNTER_INPUT_BASE = 92336U;
static const uint P_TARGET_COUNTER_INPUT_WORDS = 97464U;
static const uint P_TARGET_COUNTER_HEAD = 413712U;
static const uint P_TARGET_COUNTER_RESOURCE_BASE = 413744U;
static const uint P_TARGET_COUNTER_READY_BASE = 421936U;
static const uint P_TARGET_COUNTER_DEAD_BASE = 503856U;
static const uint P_TARGET_COUNTER_TRACE_BASE = 505392U;
static const uint P_TARGET_COUNTER_QUERY_BASE = 508464U;
static const uint P_WORLD_ACTOR_STACK_ABI = 1346721405U;
static const uint P_WORLD_ACTOR_STATUS_ABI = 1346721404U;
static const uint P_WORLD_ACTOR_RECIPIENT_ABI = 1346721403U;
static const uint P_WORLD_ACTOR_RECIPIENT_BASE = 262144U;
static const uint P_WORLD_ACTOR_RECIPIENT_WORDS = 168U;
static const uint P_WORLD_ACTOR_RECIPIENT_OUTPUT_WORDS = 524288U;
static const uint P_WORLD_ACTOR_WIDE_IMMUNITY_BASE = 348176U;
static const uint P_WORLD_ACTOR_MUTATION_ABI = 1346721402U;
static const uint P_WORLD_ACTOR_STATE_ABI = 1346721401U;
static const uint P_WORLD_ACTOR_STATE_INPUT_BASE = 92208U;
static const uint P_WORLD_ACTOR_STATE_INPUT_WORDS = 92336U;
static const uint P_WORLD_ACTOR_FIELDS_ABI = 1346721400U;
static const uint P_WORLD_ACTOR_POOL_ABI = 1346721399U;
static const uint P_WORLD_ACTOR_POOL_INPUT_BASE = 90536U;
static const uint P_WORLD_ACTOR_POOL_DEF_BASE = 90544U;
static const uint P_WORLD_ACTOR_LAND_INPUT_BASE = 92080U;
static const uint P_WORLD_ACTOR_POOL_INPUT_WORDS = 92208U;
static const uint P_WORLD_ACTOR_POOL_OUTPUT_BASE = 225280U;
static const uint P_WORLD_ACTOR_POOL_STATE_BASE = 225304U;
static const uint P_WORLD_ACTOR_SETS = 32U;
static const uint P_WORLD_ACTOR_SET_WORDS = 520U;
static const uint P_WORLD_ACTOR_SET_BASE = 227352U;
static const uint P_WORLD_ACTOR_POOL_QUERY_BASE = 243992U;
static const uint P_WORLD_ACTOR_RECEIPT_BASE = 245016U;
static const uint P_WORLD_ACTOR_NOTICE_BASE = 245528U;
static const uint P_WORLD_ACTOR_NOTICES = 1024U;
static const uint P_WORLD_ACTOR_POOL_OUTPUT_WORDS = 253952U;
static const uint P_WORLD_ACTOR_FIELDS_BASE = 253952U;
static const uint P_WORLD_ACTOR_FIELD_KEY_BASE = 253968U;
static const uint P_WORLD_ACTOR_FIELD_QUERY_BASE = 256016U;
static const uint P_WORLD_ACTOR_FIELD_ALL_BASE = 257040U;
static const uint P_WORLD_ACTOR_FIELDS_OUTPUT_WORDS = 262144U;
static const uint D_OWNER = 0U;
static const uint D_KIND = 1U;
static const uint D_STAT = 2U;
static const uint D_NAME = 3U;
static const uint D_MAX_STACK = 4U;
static const uint D_BUDGET = 5U;
static const uint D_VALUE = 6U;
static const uint D_DURATION = 8U;
static const uint D_INTERVAL = 10U;
static const uint D_IMMEDIATE = 12U;
static const uint D_PRESERVE = 13U;
static const uint D_EVENT = 14U;
static const uint D_THRESHOLD = 15U;
static const uint D_COUNT_MODE = 16U;
static const uint D_EVENT_NAME = 17U;
static const uint D_TARGET_NAME = 18U;
static const uint D_FORCE_MASK = 19U;
static const uint D_RECIPIENTS = 20U;
static const uint D_TARGET = 21U;
static const uint D_STAGE_ARG = 22U;
static const uint D_STAGE_OVERRIDE = 23U;
static const uint D_REENTRY = 24U;
static const uint D_TOGGLE = 25U;
static const uint D_TRIGGER_COUNT = 26U;
static const uint D_CONDITION_COUNT = 27U;
static const uint D_FLAGS = 28U;
static const uint D_PERIOD = 29U;
static const uint D_DAMAGE_FLAGS = 31U;
static const uint C_TARGET_STATE = 16U;
static const uint C_NOT_TARGET_STATE = 17U;
static const uint C_TARGET_STACK = 6U;
static const uint C_CORE = 35U;
static const uint C_OPTIMAL_RANGE = 33U;
static const uint C_PROB = 26U;
static const uint C_SHIELD = 12U;
static const uint C_GAUGE_ABOVE = 18U;
static const uint C_GAUGE_BELOW = 19U;
static const uint C_GAUGE_EQ = 20U;
static const uint C_GAUGE_MOD = 21U;
static const uint C_COVER_ALIVE = 36U;
static const uint C_COVER_BROKEN = 37U;
static const uint C_FULL = 1U;
static const uint C_NOT_FULL = 2U;
static const uint C_SELF_STATE = 3U;
static const uint C_NOT_SELF_STATE = 4U;
static const uint C_SELF_STACK = 5U;
static const uint C_BACK_ROW = 7U;
static const uint C_STAT_ABOVE = 8U;
static const uint C_HP_ABOVE = 9U;
static const uint C_HP_BELOW = 10U;
static const uint C_HP_MAX = 11U;
static const uint C_NOT_SELF_HEAL = 13U;
static const uint C_CAST = 14U;
static const uint C_NOT_CAST = 15U;
static const uint C_STATIC = 25U;
static const uint C_CHARGING = 29U;
static const uint C_BURST1_ALLY = 31U;
static const uint C_NO_BURST1_ALLY = 32U;
static const uint C_ALLY_HP_BELOW = 34U;
static const uint C_TARGET_CODE = 44U;
static const uint C_ENEMIES_ABOVE = 40U;
static const uint C_ENEMIES_BELOW = 41U;
static const uint C_TARGET_BOSS = 42U;
static const uint C_TARGET_ADD = 43U;
static const uint S_atk_pct = 0U;
static const uint S_atk_flat = 1U;
static const uint S_enemy_def_down_pct = 2U;
static const uint S_enemy_def_down_flat = 3U;
static const uint S_def_ignore_pct = 4U;
static const uint S_crit_rate = 5U;
static const uint S_crit_dmg = 6U;
static const uint S_core_dmg_pct = 7U;
static const uint S_charge_dmg_pct = 8U;
static const uint S_charge_dmg_mag_pct = 9U;
static const uint S_atk_dmg_pct = 10U;
static const uint S_normal_atk_dmg_pct = 11U;
static const uint S_received_dmg_pct = 12U;
static const uint S_burst_dmg_pct = 13U;
static const uint S_sequential_dmg_pct = 14U;
static const uint S_projectile_attachment_dmg_pct = 15U;
static const uint S_projectile_explosion_dmg_pct = 16U;
static const uint S_element_bonus = 17U;
static const uint S_max_ammo_pct = 18U;
static const uint S_reload_speed_pct = 19U;
static const uint S_charge_speed_pct = 20U;
static const uint S_accuracy_pct = 21U;
static const uint S_normal_atk_crit_rate = 22U;
static const uint S_normal_atk_crit_dmg = 23U;
static const uint S_crit_rate_skill = 24U;
static const uint S_crit_dmg_skill = 25U;
static const uint S_atk_caster_based_pct = 26U;
static const uint S_split_dmg_pct = 27U;
static const uint S_fullburst_duration = 29U;
static const uint S_attack_speed_pct = 30U;
static const uint S_mg_warmup_speed_pct = 31U;
static const uint S_burst_cooldown = 32U;
static const uint S_max_ammo_flat = 33U;
static const uint S_charge_time_flat = 34U;
static const uint S_pierce_dmg_pct = 35U;
static const uint S_pierce_enabled = 36U;
static const uint S_charge_speed_caster_based_pct = 37U;
static const uint S_max_hp_pct = 38U;
static const uint S_hp_caster_based_pct = 39U;
static const uint S_hp_only_caster_based_pct = 40U;
static const uint S_max_hp_only_pct = 41U;
static const uint S_heal_received_pct = 42U;
static const uint S_lifesteal_pct = 44U;
static const uint S_def_caster_based_pct = 46U;
static const uint S_reload_ratio_pct = 49U;
static const uint S_dot_dmg_pct = 50U;
static const uint S_armor_break_dmg_pct = 51U;
static const uint S_armor_break_enabled = 52U;
static const uint S_charge_time_fixed = 53U;
static const uint S_part_dmg_pct = 54U;
static const uint S_intercept_dmg_pct = 55U;
static const uint S_burst_dmg_aoe_pct = 56U;
static const uint S_burst_dmg_single_pct = 57U;
static const uint S_infinite_ammo = 59U;
static const uint S_burst_charge_speed_pct = 60U;
static const uint S_optimal_range_min = 61U;
static const uint S_optimal_range_max_pct = 62U;
static const uint S_invincible = 67U;
static const uint S_undying = 68U;
static const uint S_cover_hp_pct = 70U;
static const uint S_outgoing_heal_pct = 73U;
static const uint S_max_hp_from_max_hp_pct = 84U;
static const uint S_element_code_override = 88U;
static const uint S_atk_from_hp_pct = 89U;
static const uint S_stealth = 65U;
static const uint S_taunt = 66U;
static const uint H_BURST = 1U;
static const uint H_SEQUENTIAL = 2U;
static const uint H_ATTACHMENT = 4U;
static const uint H_EXPLOSION = 8U;
static const uint H_SPLIT = 16U;
static const uint H_CHARGE = 32U;
static const uint H_PIERCE = 64U;
static const uint H_DOT = 128U;
static const uint H_ARMOR = 512U;
static const uint H_PART = 1024U;
static const uint H_INTERCEPT = 2048U;
static const uint H_AOE_BURST = 4096U;
static const uint H_SINGLE_BURST = 8192U;
static const uint H_CORE = 16384U;
static const uint P_TARGET_INHERIT_0 = 256U;
static const uint P_TARGET_INHERIT_1 = 662863872U;
