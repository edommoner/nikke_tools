import {elementLabels} from './roster-model.mjs';

const classes = {'화력형':'火力型','지원형':'支援型','방어형':'防御型'};
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
    case 'trait': text = `${traits[value] ?? value}の味方`; break;
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
  atk_pct:'攻撃力',atk_caster_based_pct:'攻撃力（発動者基準）',atk_dmg_pct:'攻撃ダメージ',crit_rate:'会心率',crit_dmg:'会心ダメージ',
  normal_atk_crit_rate:'通常攻撃の会心率',normal_atk_dmg_pct:'通常攻撃ダメージ',pierce_dmg_pct:'貫通ダメージ',armor_break_dmg_pct:'装甲破壊ダメージ',
  charge_dmg_pct:'チャージダメージ',charge_speed_pct:'チャージ速度',charge_speed_caster_based_pct:'チャージ速度（発動者基準）',charge_time_flat:'チャージ時間',
  element_bonus_pct:'優越コードダメージ',accuracy_pct:'命中率',max_ammo_pct:'最大装弾数',max_ammo_flat:'最大装弾数',reload_speed_pct:'リロード速度',ammo_charge_pct:'弾薬回復',attack_speed_pct:'攻撃速度',
  burst_cooldown_reduce:'バースト再使用時間短縮',burst_charge_pct:'バーストゲージ',burst_charge_speed_pct:'バーストゲージ増加',fullburst_duration:'フルバースト時間',burst_reentry:'バースト再使用',
  received_dmg_pct:'被ダメージ',def_pct:'防御力',def_caster_based_pct:'防御力（発動者基準）',max_hp_pct:'最大HP',hp_caster_based_pct:'最大HP（発動者基準）',hp_only_caster_based_pct:'最大HP（発動者基準）',
  heal_hp_pct:'HP回復',heal_received_pct:'被回復量',lifesteal_pct:'吸収',shield_from_max_hp_pct:'シールド',dot_dmg_pct:'持続ダメージ',projectile_explosion_dmg_pct:'爆発ダメージ',split_dmg_pct:'分割ダメージ',
  part_dmg_pct:'パーツダメージ',core_dmg_pct:'コアダメージ',intercept_dmg_pct:'迎撃ダメージ',mg_warmup_speed_pct:'MG予熱速度',pellet_count:'弾数',skill_cooldown_pct:'スキル再使用時間',revive:'復活',debuff_cleanse:'デバフ解除',invincible:'無敵',
};
export const statLabel = stat => stats[stat] ?? stat;
export const sourceLabel = source => ({'스킬1':'スキル1','스킬2':'スキル2','스킬3':'バースト'}[source] ?? source);
