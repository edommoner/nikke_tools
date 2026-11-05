import test from 'node:test';
import assert from 'node:assert/strict';
import {cubeEffectLabel,cubeEffectText,rangeValue,cubeEditorPatch} from '../web/growth-model.mjs';
import {statLabel} from '../web/synergy-labels.mjs';

test('cube effects show Japanese effects, direction, units and level', () => {
  const up = {stat:'max_ammo_pct',direction:'up',unit:'%',values:{1:14.84,15:29.69}};
  const down = {stat:'received_dmg_pct',direction:'down',unit:'%',values:{15:9.69}};
  const ammo = {stat:'ammo_charge_flat',direction:'up',unit:'発',values:{15:3}};
  assert.equal(cubeEffectLabel(up,statLabel),'最大装弾数 ▲');
  assert.equal(cubeEffectLabel(down,statLabel),'被ダメージ ▼');
  assert.equal(cubeEffectText(up,15,statLabel),'最大装弾数 +29.69%（Lv15）');
  assert.equal(cubeEffectText(up,1,statLabel),'最大装弾数 +14.84%（Lv1）');
  assert.equal(cubeEffectText(down,15,statLabel),'被ダメージ −9.69%（Lv15）');
  assert.equal(cubeEffectText(ammo,15,statLabel),'弾薬回復（10発ごと） +3発（Lv15）');
  assert.equal(cubeEffectText({...ammo,unit:''},15,statLabel),'弾薬回復（10発ごと） +3（Lv15）');
  assert.equal(cubeEffectText(up,0,statLabel),'');
  assert.equal(cubeEffectText(undefined,1,statLabel),'');
});

test('unknown slider positions are omitted until explicitly moved', () => {
  assert.equal(rangeValue('5',false,false),undefined);
  assert.equal(rangeValue('7',false,true),7);
  assert.equal(rangeValue('10',true,false),10);
  assert.equal(rangeValue('1',false,false),undefined);
  assert.equal(rangeValue('1',false,true),1);
});

test('cube patches preserve unknown levels and supply levels for changed cubes', () => {
  assert.equal(cubeEditorPatch('','cube',undefined,1),undefined);
  assert.deepEqual(cubeEditorPatch('__none__','cube',undefined,1),{name:'__none__',level:0});
  assert.deepEqual(cubeEditorPatch('cube','cube',undefined,1),{name:'cube'});
  assert.deepEqual(cubeEditorPatch('cube','cube',15,15),{name:'cube',level:15});
  assert.deepEqual(cubeEditorPatch('cube','cube',1,1),{name:'cube',level:1});
  assert.deepEqual(cubeEditorPatch('new','cube',undefined,1),{name:'new',level:1});
});

import {overloadValue,overloadOptionText,partsToEquipSkills,partsMatchEquipSkills,normalizeParts,duplicateEffects} from '../web/growth-model.mjs';

const table = {
  atk_pct: Array.from({length:15},(_,i)=>i===9 ? 0.1111 : 0.0477+i*0.001),
  max_ammo_pct: Array.from({length:15},(_,i)=>0.2778+i*0.01),
  charge_speed_pct: Array.from({length:15},(_,i)=>0.0101+i*0.00123),
};
const stats = Object.keys(table);

test('overload values convert decimals to rounded percents and option text', () => {
  assert.equal(overloadValue(table,'atk_pct',1),4.77);
  assert.equal(overloadValue(table,'atk_pct',10),11.11);
  assert.equal(overloadValue(table,'max_ammo_pct',15),41.78);
  assert.equal(overloadValue(table,'charge_speed_pct',2),1.13);
  assert.equal(overloadValue(table,'charge_speed_pct',15),2.73);
  assert.equal(overloadOptionText(table,'atk_pct',10),'+11.11%（Lv10）');
  assert.equal(overloadOptionText(table,'max_ammo_pct',1),'+27.78%（Lv1）');
  for(const lv of [0,16,1.5])assert.equal(overloadValue(table,'atk_pct',lv),undefined);
  assert.equal(overloadValue(table,'unknown',1),undefined);
});

test('part conversion keeps absent stats zero, single lines scalar and multiple lines ordered', () => {
  const parts = normalizeParts({다리:[['atk_pct',1]],팔:[['atk_pct',3]],머리:[['atk_pct',10],['atk_pct',2]],몸통:[['max_ammo_pct',15],['atk_pct',4]]});
  assert.deepEqual(partsToEquipSkills(parts,table,stats),{
    atk_pct:[11.11,4.87,5.07,4.97,4.77],max_ammo_pct:41.78,charge_speed_pct:0,
  });
  assert.deepEqual(partsToEquipSkills(normalizeParts(),table,stats),{atk_pct:0,max_ammo_pct:0,charge_speed_pct:0});
});

test('part matching accepts scalar sums, unordered lists, tolerance and absent zero values', () => {
  const parts = normalizeParts({머리:[['atk_pct',10]],몸통:[['atk_pct',1]]});
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:15.88},table,stats),true);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:15.89},table,stats),true);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:[4.77,11.11],max_ammo_pct:0},table,stats),true);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:[4.78,11.10]},table,stats),true);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:15.9},table,stats),false);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:[15.88]},table,stats),false);
  assert.equal(partsMatchEquipSkills(parts,{atk_pct:[4.77,11.2]},table,stats),false);
  assert.equal(partsMatchEquipSkills(parts,{},table,stats),false);
  assert.equal(partsMatchEquipSkills(normalizeParts(),{},table,stats),true);
  assert.equal(partsMatchEquipSkills(normalizeParts(),{atk_pct:1},table,stats),false);
  assert.equal(partsMatchEquipSkills(normalizeParts({머리:[['atk_pct',10]]}),{atk_pct:11.11},table,stats),true);
});

test('part normalization drops invalid entries, caps each part and returns independent entries', () => {
  const raw = {머리:[null,['unknown',10],['atk_pct','10'],['atk_pct',0],['atk_pct',16],['atk_pct',1.5],['atk_pct',1,'extra'],['atk_pct',1],['max_ammo_pct',15],['crit_rate',10],['def_pct',2]],몸통:'invalid',팔:[['charge_speed_pct',3]],other:[['atk_pct',2]]};
  const result = normalizeParts(raw);
  assert.deepEqual(result,{머리:[['atk_pct',1],['max_ammo_pct',15],['crit_rate',10]],몸통:[],팔:[['charge_speed_pct',3]],다리:[]});
  result.머리[0][1]=9;
  assert.equal(raw.머리[7][1],1);
  for(const value of [undefined,null,[],42])assert.deepEqual(normalizeParts(value),{머리:[],몸통:[],팔:[],다리:[]});
});

test('duplicates are reported once per effect in each part, never across parts', () => {
  assert.deepEqual(duplicateEffects(normalizeParts({머리:[['atk_pct',1],['atk_pct',2],['atk_pct',3]],몸통:[['atk_pct',10]],팔:[['crit_rate',1],['crit_rate',2]]})),[{part:'머리',stat:'atk_pct'},{part:'팔',stat:'crit_rate'}]);
  assert.deepEqual(duplicateEffects(normalizeParts({머리:[['atk_pct',1]],몸통:[['atk_pct',2]]})),[]);
  assert.deepEqual(duplicateEffects(normalizeParts()),[]);
});
