import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeLayout, PALETTE, BUILTIN_IDS } from '../web/touchlayout.js';

test('盤面＝Shift＋0–9，共 11 鍵', () => {
  assert.equal(PALETTE.length, 11);
  assert.deepEqual(PALETTE[0], { key: 'ShiftLeft', label: 'Shift' });
  assert.deepEqual(PALETTE[10], { key: 'Digit9', label: '9' });
});

test('內建 id 固定五個', () => {
  assert.deepEqual(BUILTIN_IDS,
    ['dpad', 'apad-escape', 'apad-enter', 'apad-ff3', 'apad-ff10']);
});

test('合法輸入原樣通過', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'dpad', x: 2, y: 60 },
    { key: 'Digit1', label: '1', x: 52, y: 88 },
  ] });
  assert.deepEqual(r, { v: 1, buttons: [
    { id: 'dpad', x: 2, y: 60 },
    { key: 'Digit1', label: '1', x: 52, y: 88 },
  ] });
});

test('非物件／缺 buttons → null', () => {
  assert.equal(normalizeLayout(null), null);
  assert.equal(normalizeLayout('x'), null);
  assert.equal(normalizeLayout({ v: 1 }), null);
  assert.equal(normalizeLayout({ buttons: 'x' }), null);
});

test('空 buttons 合法（＝全部隱藏）', () => {
  assert.deepEqual(normalizeLayout({ v: 1, buttons: [] }), { v: 1, buttons: [] });
});

test('壞項被丟：未知 id、未知 key、非數字座標', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'hack', x: 1, y: 1 },
    { key: 'KeyZ', label: 'Z', x: 1, y: 1 },
    { key: 'Digit1', label: '1', x: 'a', y: 1 },
    { id: 'dpad', x: 3, y: 4 },
  ] });
  assert.deepEqual(r.buttons, [{ id: 'dpad', x: 3, y: 4 }]);
});

test('座標夾限 0–95', () => {
  const r = normalizeLayout({ v: 1, buttons: [{ id: 'dpad', x: -5, y: 120 }] });
  assert.deepEqual(r.buttons, [{ id: 'dpad', x: 0, y: 95 }]);
});

test('重複 id/key 取第一個', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'dpad', x: 1, y: 1 }, { id: 'dpad', x: 9, y: 9 },
    { key: 'Digit1', x: 2, y: 2 }, { key: 'Digit1', x: 8, y: 8 },
  ] });
  assert.equal(r.buttons.length, 2);
  assert.equal(r.buttons[0].x, 1);
  assert.equal(r.buttons[1].x, 2);
});

test('label 一律以盤面為準（存壞了也矯正）', () => {
  const r = normalizeLayout({ v: 1, buttons: [{ key: 'ShiftLeft', label: '<img>', x: 1, y: 1 }] });
  assert.equal(r.buttons[0].label, 'Shift');
});
