import test from 'node:test';
import assert from 'node:assert/strict';
import {selectorLabel,conditionLabel,statLabel,sourceLabel} from '../web/synergy-labels.mjs';

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
