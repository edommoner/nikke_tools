import test from 'node:test';
import assert from 'node:assert/strict';
import {selectorLabel,conditionLabel,statLabel,statShortLabel,sourceLabel} from '../web/synergy-labels.mjs';

test('every selector kind has Japanese target labels and self exclusion', () => {
  const cases = [
    [{kind:'element',value:'수냉'},'水冷の味方'],
    [{kind:'weapon',value:'SG'},'SGの味方'],
    [{kind:'class',value:'화력형'},'火力型の味方'],
    [{kind:'class',value:'지원형'},'支援型の味方'],
    [{kind:'class',value:'방어형'},'防御型の味方'],
    [{kind:'element_weapon',element:'전격',weapon:'MG'},'電撃のMGの味方'],
    [{kind:'squad'},'同じ部隊の味方'],
    [{kind:'squad_burst',value:'3'},'同じ部隊のバーストⅢ'],
    [{kind:'burst',value:'3'},'バーストⅢの味方'],
    [{kind:'name',value:'헬름'},'ヘルムを指定'],
    [{kind:'all'},'味方全体'],
    [{kind:'dynamic'},'条件で選ばれる味方'],
    ...Object.entries({pierce:'貫通',armor_break:'装甲破壊',explosion:'爆発',split:'分割',dot:'持続ダメージ',charge:'チャージ武器',mg:'MG',sg:'SG'}).map(([value,label])=>[{kind:'trait',value},`${label}の味方`]),
  ];
  for(const [selector,expected] of cases){
    assert.equal(selectorLabel(selector,()=> 'ヘルム'),expected);
    assert.equal(selectorLabel({...selector,excl_self:true},()=> 'ヘルム'),expected+'（自分以外）');
  }
});

test('every condition kind and negation use Japanese labels', () => {
  for(const [condition,subject] of [
    [{kind:'squad_member'},'同じ部隊の味方'],
    [{kind:'has_burst',value:'1'},'バーストⅠの味方'],
    [{kind:'has_burst',value:'2'},'バーストⅡの味方'],
    [{kind:'has_class',value:'방어형'},'防御型の味方'],
    [{kind:'has_class',value:'화력형'},'火力型の味方'],
    [{kind:'has_class',value:'지원형'},'支援型の味方'],
  ]){
    assert.equal(conditionLabel(condition),subject+'がいると発動');
    assert.equal(conditionLabel({...condition,negate:true}),subject+'がいないと発動');
  }
});

test('stat labels include caster basis, flat values and unknown fallback', () => {
  assert.equal(statLabel('atk_pct'),'攻撃力');
  assert.equal(statLabel('charge_speed_caster_based_pct'),'チャージ速度（発動者基準）');
  assert.equal(statLabel('max_ammo_flat'),'最大装弾数');
  assert.equal(statLabel('hp_only_caster_based_pct'),'最大HP（発動者基準）');
  assert.equal(statLabel('debuff_cleanse'),'デバフ解除');
  assert.equal(statLabel('future_stat'),'future_stat');
});

test('source labels translate skills and preserve unknown values', () => {
  assert.equal(sourceLabel('스킬1'),'スキル1');
  assert.equal(sourceLabel('스킬2'),'スキル2');
  assert.equal(sourceLabel('스킬3'),'バースト');
  assert.equal(sourceLabel('other'),'other');
});

test('all cube stats have Japanese effect labels', () => {
  const labels = {
    reload_speed_pct:'リロード速度',ammo_charge_flat:'弾薬回復（10発ごと）',
    charge_speed_pct:'チャージ速度',burst_charge_speed_pct:'バーストゲージ増加',
    received_dmg_pct:'被ダメージ',part_dmg_pct:'パーツダメージ',
    cover_hp_pct:'遮蔽物の最大HP',outgoing_heal_pct:'与える回復量',
    max_hp_pct:'最大HP',def_pct:'防御力',pierce_dmg_pct:'貫通ダメージ',
    armor_break_dmg_pct:'装甲破壊ダメージ',split_dmg_pct:'分割ダメージ',
    accuracy_pct:'命中率',charge_dmg_pct:'チャージダメージ',max_ammo_pct:'最大装弾数',
  };
  for (const [stat,label] of Object.entries(labels)) assert.equal(statLabel(stat),label);
});

test('slot stat labels cover compact Japanese names including shared labels', () => {
  const cases = {
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
  for (const [stat,expected] of Object.entries(cases)) assert.equal(statShortLabel(stat),expected,stat);
});

test('slot stat labels fall back to full Japanese labels and preserve unknown stats', () => {
  assert.equal(statShortLabel('mg_warmup_speed_pct'),'MG予熱速度');
  assert.equal(statShortLabel('skill_cooldown_pct'),statLabel('skill_cooldown_pct'));
  assert.equal(statShortLabel('future_stat'),'future_stat');
  assert.equal(statLabel('atk_caster_based_pct'),'攻撃力（発動者基準）');
  assert.equal(statLabel('projectile_explosion_dmg_pct'),'飛翔体の爆発ダメージ');
});

test('additional effect stats have full and compact Japanese labels', () => {
  const cases = {
    named_buff_duration_extend:'バフ延長',remove_named_buff:'バフ解除',buff_stack_add:'スタック追加',buff_max_stack_add:'最大スタック増加',
    debuff_immune_count:'デバフ無効',cover_heal_pct:'遮蔽物回復',heal_overcharge_store:'余剰回復の保存',
    received_dmg_split:'被ダメ分担',received_dmg_split_even:'被ダメ分担',heal_split:'回復分配',effect_target_count_add:'対象数増加',
    effect_range_pct:'効果範囲',optimal_range_max_pct:'有効射程',burst_dmg_aoe_pct:'範囲バーストダメ',burst_dmg_single_pct:'単体バーストダメ',
    shield_dmg_pct:'シールドへのダメ',charge_dmg_mag_pct:'チャージダメ倍率',atk_from_hp_pct:'HP比例攻撃力',undying:'不屈',
    stun_immune:'スタン無効',cover_revive:'遮蔽物復活',cover_def_pct:'遮蔽物防御力',gauge_charge:'ゲージ増加',gauge_consume:'ゲージ消費',
  };
  for(const [stat,expected] of Object.entries(cases)){
    assert.equal(statLabel(stat),expected,stat);
    assert.equal(statShortLabel(stat),expected,stat);
  }
});

test('empty and missing stats display special effect in both label lengths', () => {
  for(const stat of ['',undefined,null]){
    assert.equal(statLabel(stat),'特殊効果');
    assert.equal(statShortLabel(stat),'特殊効果');
  }
});

test('conditional trait selectors retain their full explanatory suffix', () => {
  assert.equal(selectorLabel({kind:'trait',value:'explosion',rule:'conditional'}),'爆発の味方（条件で選ばれる対象）');
});

test('classLabel translates character classes', async () => {
  const {classLabel} = await import('../web/synergy-labels.mjs');
  assert.equal(classLabel('지원형'), '支援型');
  assert.equal(classLabel('화력형'), '火力型');
  assert.equal(classLabel(undefined), '');
});
