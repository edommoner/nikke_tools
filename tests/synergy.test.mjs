import test from 'node:test';
import assert from 'node:assert/strict';
import {selectorMatches, conditionEffect, synergyRelations, rankSynergyCandidates} from '../web/synergy-model.mjs';

const character = (name, extra = {}) => ({name, element: '전격', weapon: 'SG', class: '방어형',
  squad: 'squad', burst: '3', synergy: {traits: ['pierce'], provides: [], conditions: []}, ...extra});
const provides = (tier = 'A', selector = {kind: 'weapon', value: 'SG'}) =>
  ({tier, selector, stat: 'atk_pct', source: 'skill', name: 'buff', favorite: false});
const condition = (negate = false) => ({kind: 'has_class', value: '방어형', negate, source: 'skill', name: 'condition', favorite: true});

test('every selector kind matches and rejects mismatches', () => {
  const owner = character('owner'), receiver = character('receiver');
  const selectors = [
    {kind: 'element', value: '전격'}, {kind: 'weapon', value: 'SG'},
    {kind: 'class', value: '방어형'}, {kind: 'element_weapon', element: '전격', weapon: 'SG'},
    {kind: 'squad'}, {kind: 'squad_burst', value: '3'}, {kind: 'burst', value: '3'},
    {kind: 'name', value: 'receiver'}, {kind: 'trait', value: 'pierce'},
    {kind: 'all'}, {kind: 'dynamic', rule: 'allies_top_atk'},
  ];
  for (const selector of selectors) {
    assert.equal(selectorMatches(selector, owner, receiver), true, selector.kind);
    assert.equal(selectorMatches({...selector, excl_self: true}, owner, {...owner}), false, selector.kind);
    if (!['all', 'dynamic'].includes(selector.kind)) {
      assert.equal(selectorMatches(selector, owner, {name: 'other', synergy: {}}), false, selector.kind);
    }
  }
  assert.equal(selectorMatches({kind: 'element_weapon', element: '전격', weapon: 'AR'}, owner, receiver), false);
  assert.equal(selectorMatches({kind: 'element_weapon', element: '수냉', weapon: 'SG'}, owner, receiver), false);
  assert.equal(selectorMatches({kind: 'squad'}, character('empty', {squad: ''}), character('empty2', {squad: ''})), false);
  assert.equal(selectorMatches({kind: 'unknown'}, owner, receiver), false);
});

test('burst A matches any burst stage including squad burst', () => {
  for (const kind of ['burst', 'squad_burst']) {
    for (const value of ['1', '2', '3']) {
      assert.equal(selectorMatches({kind, value}, character('p'), character('r', {burst: 'A'})), true);
      assert.equal(selectorMatches({kind, value}, character('p'), character('r', {burst: '2'})), value === '2');
    }
  }
});

test('conditions report satisfied, broken or null and exclude owner', () => {
  const owner = character('owner'), other = character('other');
  for (const c of [{kind: 'squad_member'}, {kind: 'has_burst', value: '3'}, condition()]) {
    assert.equal(conditionEffect(c, owner, [other]), 'satisfied');
    assert.equal(conditionEffect({...c, negate: true}, owner, [other]), 'broken');
    assert.equal(conditionEffect(c, owner, [owner]), null);
    assert.equal(conditionEffect(c, owner, []), null);
  }
  assert.equal(conditionEffect({kind: 'has_burst', value: '1'}, owner, [character('a', {burst: 'A'})]), 'satisfied');
  assert.equal(conditionEffect(condition(), owner, [character('a', {class: '지원형'})]), null);
  assert.equal(conditionEffect({kind: 'unknown'}, owner, [other]), null);
});

test('relations include both directions, provenance, conditions and tier filtering', () => {
  const a = character('a'), b = character('b');
  a.synergy.provides = [provides(), provides('B', {kind: 'trait', value: 'pierce'}), provides('C', {kind: 'all'})];
  b.synergy.provides = [provides()];
  a.synergy.conditions = [condition()];
  b.synergy.conditions = [condition(true)];
  const relations = synergyRelations([a], b);
  assert.equal(relations.length, 5);
  assert.ok(relations.some(r => r.from === a && r.to === b && r.kind === 'provides'));
  assert.ok(relations.some(r => r.from === b && r.to === a && r.effect === 'broken' && r.favorite));
  assert.ok(relations.some(r => r.from === a && r.effect === 'satisfied'));
  assert.ok(relations.every(r => r.source === 'skill' && r.name));
  assert.equal(synergyRelations([a], b, {tiers: ['C']}).length, 1);
  assert.equal(synergyRelations([a], b, {tiers: ['B']}).length, 1);
  assert.equal(synergyRelations([a], b, {tiers: ['A', 'B', 'C']}).length, 6);
  assert.deepEqual(synergyRelations([a], b, {tiers: []}), []);
  assert.deepEqual(synergyRelations([a], {...a}), []);
  assert.deepEqual(synergyRelations([character('no-profile', {synergy: null})], character('other', {synergy: null})), []);
});

test('ranking prioritizes distinct basis members, relation count, then input order', () => {
  const a = character('a'), b = character('b', {weapon: 'AR'});
  const candidate = (name, entries) => character(name, {synergy: {provides: entries}});
  const one = candidate('one', [provides(), provides(), provides()]);
  const two = candidate('two', [provides('A', {kind: 'all'})]);
  const tie = candidate('tie', [provides('A', {kind: 'all'})]);
  const many = candidate('many', [provides('A', {kind: 'all'}), provides()]);
  const broken = character('broken', {synergy: {conditions: [condition(true)]}});
  const ranked = rankSynergyCandidates([a, b], [one, two, tie, broken, many, a]);
  assert.deepEqual(ranked.map(e => [e.character.name, e.basisCount]), [['many', 2], ['two', 2], ['tie', 2], ['one', 1]]);
  one.synergy.conditions = [condition(true)];
  const [entry] = rankSynergyCandidates([a, b], [one]);
  assert.equal(entry.basisCount, 1);
  assert.equal(entry.relations.filter(r => r.effect === 'broken').length, 2);
  assert.deepEqual(rankSynergyCandidates([], [one]), []);
});

test('ranking uses tier weights after basis count and ignores broken conditions in score', () => {
  const basis = character('basis');
  const candidate = (name, entries, conditions = []) => character(name, {synergy: {provides: entries, conditions}});
  const a = candidate('a', [provides('A')]);
  const b = candidate('b', [provides('B')]);
  const c = candidate('c', [provides('C'), provides('C')]);
  const broken = candidate('broken', [provides('C')], [condition(true), condition(true), condition(true)]);
  const rank = options => rankSynergyCandidates([basis], [c, b, broken, a], options).map(e => e.character.name);
  assert.deepEqual(rank({tiers:['A','B','C']}), ['a','c','b','broken']);
  assert.deepEqual(rank({tiers:['A','B','C'],weights:{A:1,B:5,C:1}}), ['b','c','broken','a']);
  assert.deepEqual(rankSynergyCandidates([basis], [a,b]).map(e=>e.character.name), ['a','b']);
  const second = character('second', {weapon:'AR'});
  const broad = candidate('broad',[provides('C',{kind:'all'})]);
  assert.deepEqual(rankSynergyCandidates([basis,second],[a,broad],{tiers:['A','C'],weights:{A:100,C:1}}).map(e=>e.character.name),['broad','a']);
});
