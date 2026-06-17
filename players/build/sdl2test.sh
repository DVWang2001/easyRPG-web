#!/usr/bin/env bash
set -e
source /work/buildscripts/emscripten/emsdk-portable/emsdk_env.sh >/dev/null 2>&1
export EASYRPG_BUILDSCRIPTS=/work/buildscripts
# 確保 nlohmann config 在（player.sh 會建，這裡保險）
NJ=/work/buildscripts/emscripten/lib/cmake/nlohmann_json
if [ ! -f "$NJ/nlohmann_jsonConfig.cmake" ]; then echo "nlohmann config 缺，先跑 player.sh 一次"; fi
cd /work/Player
cmake --preset emscripten-sdl2-release -DPLAYER_JS_OUTPUT_NAME=index 2>&1 | tail -25
