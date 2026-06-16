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
echo "=== DEPS_DONE_OK $(date) ==="
