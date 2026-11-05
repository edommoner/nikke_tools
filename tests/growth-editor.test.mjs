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
