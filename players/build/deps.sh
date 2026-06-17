#!/usr/bin/env bash
# 在容器內建置 EasyRPG emscripten 依賴工具鏈(emsdk 5.0.5 + 所有函式庫 + liblcf)。
exec > /work/deps.log 2>&1
set -e
echo "=== DEPS START $(date) ==="
cd /work
[ -d buildscripts ] || git clone --depth 1 https://github.com/EasyRPG/buildscripts
[ -d Player ]       || git clone --depth 1 https://github.com/EasyRPG/Player
cd /work/buildscripts/emscripten
export BUILD_LIBLCF=1
./0_build_everything.sh
# 防呆：ICU data 應是 EasyRPG 過濾版（~700KB）。若意外變成數十 MB，代表過濾版
# icudata 沒套到（常因下載不穩 → 用了 ICU 完整 data），emscripten 靜態 ICU 會
# 無法載入，遊戲會報「Invalid encoding: Big5」。此時請確認網路後重跑。
ICUDATA=/work/buildscripts/emscripten/lib/libicudata.a
SZ=$(stat -c%s "$ICUDATA" 2>/dev/null || echo 0)
echo "libicudata.a = $SZ bytes"
if [ "$SZ" -gt 5000000 ]; then
  echo "!!! ICU data 異常過大（$SZ bytes）→ 過濾版未套用，Big5 會壞。請確認網路後重跑 deps。"
  exit 3
fi
echo "=== DEPS_DONE_OK $(date) ==="
