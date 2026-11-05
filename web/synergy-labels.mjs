import {elementLabels} from './roster-model.mjs';

const classes = {'화력형':'火力型','지원형':'支援型','방어형':'防御型'};
export const classLabel = value => classes[value] ?? value ?? '';
const traits = {pierce:'貫通',armor_break:'装甲破壊',explosion:'爆発',split:'分割',dot:'持続ダメージ',charge:'チャージ武器',mg:'MG',sg:'SG'};
const burstLabel = value => ({'1':'Ⅰ','2':'Ⅱ','3':'Ⅲ'}[value] ?? value);
export function selectorLabel(selector, labelOf = name => name) {
  const value = selector.value;
  let text;
  switch (selector.kind) {
    case 'element': text = `${elementLabels[value] ?? value}の味方`; break;
    case 'weapon': text = `${value}の味方`; break;
    case 'class': text = `${classes[value] ?? value}の味方`; break;
    case 'element_weapon': text = `${elementLabels[selector.element] ?? selector.element}の${selector.weapon}の味方`; break;
    case 'squad': text = '同じ部隊の味方'; break;
    case 'squad_burst': text = `同じ部隊のバースト${burstLabel(value)}`; break;
    case 'burst': text = `バースト${burstLabel(value)}の味方`; break;
    case 'name': text = `${labelOf(value)}を指定`; break;
    case 'trait': text = `${traits[value] ?? value}の味方${selector.rule ? '（条件で選ばれる対象）' : ''}`; break;
    case 'all': text = '味方全体'; break;
    case 'dynamic': text = '条件で選ばれる味方'; break;
    default: text = selector.kind;
  }
  return text + (selector.excl_self ? '（自分以外）' : '');
}
export function conditionLabel(condition) {
  let subject;
  switch (condition.kind) {
    case 'squad_member': subject = '同じ部隊の味方'; break;
    case 'has_burst': subject = `バースト${burstLabel(condition.value)}の味方`; break;
    case 'has_class': subject = `${classes[condition.value] ?? condition.value}の味方`; break;
    default: return condition.kind;
  }
  return `${subject}が${condition.negate ? 'いない' : 'いる'}と発動`;
}
const stats = {
  ammo_charge_flat:'弾薬回復（10発ごと）',cover_hp_pct:'遮蔽物の最大HP',outgoing_heal_pct:'与える回復量',
  named_buff_duration_extend:'バフ延長',remove_named_buff:'バフ解除',buff_stack_add:'スタック追加',buff_max_stack_add:'最大スタック増加',
  debuff_immune_count:'デバフ無効',cover_heal_pct:'遮蔽物回復',heal_overcharge_store:'余剰回復の保存',received_dmg_split:'被ダメ分担',received_dmg_split_even:'被ダメ分担',
  heal_split:'回復分配',effect_target_count_add:'対象数増加',effect_range_pct:'効果範囲',optimal_range_max_pct:'有効射程',burst_dmg_aoe_pct:'範囲バーストダメ',burst_dmg_single_pct:'単体バーストダメ',
  shield_dmg_pct:'シールドへのダメ',charge_dmg_mag_pct:'チャージダメ倍率',atk_from_hp_pct:'HP比例攻撃力',undying:'不屈',stun_immune:'スタン無効',cover_revive:'遮蔽物復活',cover_def_pct:'遮蔽物防御力',gauge_charge:'ゲージ増加',gauge_consume:'ゲージ消費',
  focus_fire:'集中攻撃',
  atk_pct:'攻撃力',atk_caster_based_pct:'攻撃力（発動者基準）',atk_dmg_pct:'攻撃ダメージ',crit_rate:'会心率',crit_dmg:'会心ダメージ',
  normal_atk_crit_rate:'通常攻撃の会心率',normal_atk_dmg_pct:'通常攻撃ダメージ',pierce_dmg_pct:'貫通ダメージ',armor_break_dmg_pct:'装甲破壊ダメージ',
  charge_dmg_pct:'チャージダメージ',charge_speed_pct:'チャージ速度',charge_speed_caster_based_pct:'チャージ速度（発動者基準）',charge_time_flat:'チャージ時間',
  element_bonus_pct:'優越コードダメージ',accuracy_pct:'命中率',max_ammo_pct:'最大装弾数',max_ammo_flat:'最大装弾数',reload_speed_pct:'リロード速度',ammo_charge_pct:'弾薬回復',attack_speed_pct:'攻撃速度',
  burst_cooldown_reduce:'バースト再使用時間短縮',burst_charge_pct:'バーストゲージ',burst_charge_speed_pct:'バーストゲージ増加',fullburst_duration:'フルバースト時間',burst_reentry:'バースト再使用',
  received_dmg_pct:'被ダメージ',def_pct:'防御力',def_caster_based_pct:'防御力（発動者基準）',max_hp_pct:'最大HP',hp_caster_based_pct:'最大HP（発動者基準）',hp_only_caster_based_pct:'最大HP（発動者基準）',
  heal_hp_pct:'HP回復',heal_received_pct:'被回復量',lifesteal_pct:'吸収',shield_from_max_hp_pct:'シールド',dot_dmg_pct:'持続ダメージ',projectile_explosion_dmg_pct:'飛翔体の爆発ダメージ',split_dmg_pct:'分割ダメージ',
  part_dmg_pct:'パーツダメージ',core_dmg_pct:'コアダメージ',intercept_dmg_pct:'迎撃ダメージ',mg_warmup_speed_pct:'MG予熱速度',pellet_count:'弾数',skill_cooldown_pct:'スキル再使用時間',revive:'復活',debuff_cleanse:'デバフ解除',invincible:'無敵',
};
export const statLabel = stat => stats[stat] ?? (stat || '特殊効果');
const shortStats = {
  named_buff_duration_extend:'バフ延長',remove_named_buff:'バフ解除',buff_stack_add:'スタック追加',buff_max_stack_add:'最大スタック増加',
  debuff_immune_count:'デバフ無効',cover_heal_pct:'遮蔽物回復',heal_overcharge_store:'余剰回復の保存',received_dmg_split:'被ダメ分担',received_dmg_split_even:'被ダメ分担',
  heal_split:'回復分配',effect_target_count_add:'対象数増加',effect_range_pct:'効果範囲',optimal_range_max_pct:'有効射程',burst_dmg_aoe_pct:'範囲バーストダメ',burst_dmg_single_pct:'単体バーストダメ',
  shield_dmg_pct:'シールドへのダメ',charge_dmg_mag_pct:'チャージダメ倍率',atk_from_hp_pct:'HP比例攻撃力',undying:'不屈',stun_immune:'スタン無効',cover_revive:'遮蔽物復活',cover_def_pct:'遮蔽物防御力',gauge_charge:'ゲージ増加',gauge_consume:'ゲージ消費',
  focus_fire:'集中攻撃',
  atk_pct:'攻撃力',atk_caster_based_pct:'攻撃力',atk_dmg_pct:'攻撃ダメ',crit_rate:'会心率',crit_dmg:'会心ダメ',
  normal_atk_crit_rate:'通常会心率',normal_atk_dmg_pct:'通常ダメ',pierce_dmg_pct:'貫通ダメ',armor_break_dmg_pct:'装甲破壊ダメ',
  charge_dmg_pct:'チャージダメ',charge_speed_pct:'チャージ速度',charge_speed_caster_based_pct:'チャージ速度',charge_time_flat:'チャージ時間',
  projectile_explosion_dmg_pct:'飛翔体爆発',projectile_dmg_pct:'飛翔体ダメ',split_dmg_pct:'分割ダメ',dot_dmg_pct:'持続ダメ',
  element_bonus_pct:'優越コード',accuracy_pct:'命中率',max_ammo_pct:'装弾数',max_ammo_flat:'装弾数',reload_speed_pct:'リロード',ammo_charge_pct:'弾薬回復',attack_speed_pct:'攻撃速度',
  burst_cooldown_reduce:'バースト短縮',burst_charge_pct:'バーストゲージ',burst_charge_speed_pct:'バーストゲージ',fullburst_duration:'フルバ時間',burst_reentry:'バースト再使用',
  def_pct:'防御力',def_caster_based_pct:'防御力',max_hp_pct:'最大HP',hp_caster_based_pct:'最大HP',hp_only_caster_based_pct:'最大HP',
  heal_hp_pct:'回復',heal_received_pct:'被回復',lifesteal_pct:'吸収',shield_from_max_hp_pct:'シールド',received_dmg_pct:'被ダメ',
  part_dmg_pct:'パーツダメ',core_dmg_pct:'コアダメ',intercept_dmg_pct:'迎撃ダメ',invincible:'無敵',revive:'復活',debuff_cleanse:'デバフ解除',
};
export const statShortLabel = stat => shortStats[stat] ?? statLabel(stat);
export const sourceLabel = source => ({'스킬1':'スキル1','스킬2':'スキル2','스킬3':'バースト'}[source] ?? source);
