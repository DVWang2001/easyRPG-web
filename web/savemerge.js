// 逐槽三方合併決策（純函式、零相依；瀏覽器與 node --test 共用）。
// local: { 檔名: {fp, mtime} }（mtime＝毫秒）
// cloud: { 檔名: {fp, updatedAt} }（updatedAt＝毫秒）
// last:  { 檔名: fp }＝上次同步完成時兩邊一致的指紋
// 回傳 { pull, push, deleteLocal, deleteCloud }（皆為檔名陣列）。
// spec: docs/superpowers/specs/2026-07-10-seamless-cloud-save-design.md 合併表
export function decideSlots(local, cloud, last) {
  const out = { pull: [], push: [], deleteLocal: [], deleteCloud: [] };
  const names = new Set([
    ...Object.keys(local), ...Object.keys(cloud), ...Object.keys(last),
  ]);
  for (const n of names) {
    const l = local[n]; const c = cloud[n]; const s = last[n];
    if (l && c) {
      if (l.fp === c.fp) continue;                                  // 已一致
      if (l.fp === s) out.pull.push(n);                             // 本機沒動 → 雲端勝
      else if (c.fp === s) out.push.push(n);                        // 雲端沒動 → 本機勝
      else (c.updatedAt > l.mtime ? out.pull : out.push).push(n);   // 雙邊衝突 → 較新者勝
    } else if (l) {
      // 雲端缺席：上次也沒有＝本機新增；上次有但本機又改＝改動勝；否則雲端刪除傳播
      if (s === undefined || l.fp !== s) out.push.push(n);
      else out.deleteLocal.push(n);
    } else if (c) {
      if (s === undefined || c.fp !== s) out.pull.push(n);
      else out.deleteCloud.push(n);
    }
    // 兩邊皆無、只剩 last 殘留 → 無事，下次寫同步點時自然清掉
  }
  return out;
}
