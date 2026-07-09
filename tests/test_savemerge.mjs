import test from 'node:test';
import assert from 'node:assert/strict';
import { decideSlots } from '../web/savemerge.js';

const EMPTY = { pull: [], push: [], deleteLocal: [], deleteCloud: [] };
const L = (fp, mtime = 0) => ({ fp, mtime });
const C = (fp, updatedAt = 0) => ({ fp, updatedAt });

test('雙方一致 → 無事', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, { a: C('x') }, { a: 'x' }), EMPTY);
});

test('本機沒動、雲端變了 → 拉', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, { a: C('y') }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('本機變了、雲端沒動 → 推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y') }, { a: C('x') }, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('雙邊衝突 → 雲端較新則拉', () => {
  assert.deepEqual(
    decideSlots({ a: L('y', 100) }, { a: C('z', 200) }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('雙邊衝突 → 本機較新則推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y', 300) }, { a: C('z', 200) }, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('本機獨有、上次沒有 → 新增推', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, {}, {}), { ...EMPTY, push: ['a'] });
});

test('雲端獨有、上次沒有 → 新增拉', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('x') }, {}), { ...EMPTY, pull: ['a'] });
});

test('本機刪了、雲端沒動 → 刪雲端', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('x') }, { a: 'x' }),
    { ...EMPTY, deleteCloud: ['a'] });
});

test('雲端刪了、本機沒動 → 刪本機', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, {}, { a: 'x' }),
    { ...EMPTY, deleteLocal: ['a'] });
});

test('雲端刪了但本機又改過 → 改動勝，推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y') }, {}, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('本機刪了但雲端又改過 → 改動勝，拉', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('y') }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('兩邊皆無、只剩 last 殘留 → 無事', () => {
  assert.deepEqual(decideSlots({}, {}, { a: 'x' }), EMPTY);
});
