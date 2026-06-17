#!/usr/bin/env bash
set -e
source /work/buildscripts/emscripten/emsdk-portable/emsdk_env.sh >/dev/null 2>&1
P=/work/buildscripts/emscripten
cd /tmp
emcc /scripts/icutest.cpp -DU_STATIC_IMPLEMENTATION \
  -I"$P/include" -L"$P/lib" -licui18n -licuuc -licudata \
  -o icutest.js -sEXIT_RUNTIME=1 -sALLOW_MEMORY_GROWTH=1
echo "--- run ---"
node icutest.js
