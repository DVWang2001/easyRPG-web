// 觸控佈局純邏輯：驗證/夾限 localStorage 佈局（不可信輸入）＋編輯盤面定義。
// 供 touchpad.js 與 node --test 共用。
// spec: docs/superpowers/specs/2026-07-10-player-touch-editor-design.md

// 內建鍵 id（dpad＝整組方向鍵；其餘為 apad 圓鈕）
export const BUILTIN_IDS = ['dpad', 'apad-escape', 'apad-enter', 'apad-ff3', 'apad-ff10'];

// 編輯盤面可加入的自訂鍵（決定/取消/»/»» 由內建鍵 chips 提供，不在此重複）
export const PALETTE = [
  { key: 'ShiftLeft', label: 'Shift' },
  ...Array.from({ length: 10 }, (_, n) => ({ key: 'Digit' + n, label: String(n) })),
];

const LABELS = new Map(PALETTE.map((p) => [p.key, p.label]));
const clamp = (n) => Math.min(95, Math.max(0, n));

// raw（JSON.parse 後任意值）→ {v:1,buttons:[…]} 或 null（壞資料＝當作沒紀錄）。
// 合法項：{id∈BUILTIN_IDS,x,y} 或 {key∈盤面,x,y}（label 一律以盤面為準）；
// x/y 夾限 0–95；重複 id/key 取第一個。
export function normalizeLayout(raw) {
  if (!raw || typeof raw !== 'object' || !Array.isArray(raw.buttons)) return null;
  const seen = new Set();
  const buttons = [];
  for (const b of raw.buttons) {
    if (!b || typeof b !== 'object') continue;
    const x = Number(b.x);
    const y = Number(b.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    if (typeof b.id === 'string' && BUILTIN_IDS.includes(b.id) && !seen.has(b.id)) {
      seen.add(b.id);
      buttons.push({ id: b.id, x: clamp(x), y: clamp(y) });
    } else if (typeof b.key === 'string' && LABELS.has(b.key) && !seen.has(b.key)) {
      seen.add(b.key);
      buttons.push({ key: b.key, label: LABELS.get(b.key), x: clamp(x), y: clamp(y) });
    }
  }
  return { v: 1, buttons };
}
