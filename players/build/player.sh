#!/usr/bin/env bash
# 編 EasyRPG Player 網頁版(emscripten)。依賴需已由 deps.sh 建好。
# 輸出直接走 stdout(讓呼叫端/GUI 可即時顯示);要存檔的話由呼叫端自行重導。
set -e
echo "=== PLAYER BUILD START $(date) ==="
source /work/buildscripts/emscripten/emsdk-portable/emsdk_env.sh
export EASYRPG_BUILDSCRIPTS=/work/buildscripts
PREFIX=/work/buildscripts/emscripten

# 修補:buildscripts 的 3_cleanup 刪了 share/,連帶刪掉 nlohmann_json 的 cmake config
# (header-only,自己補一份最小 config 讓 find_package 找得到)。
NJ="$PREFIX/lib/cmake/nlohmann_json"
if [ ! -f "$NJ/nlohmann_jsonConfig.cmake" ]; then
  echo "=== patching nlohmann_json cmake config ==="
  mkdir -p "$NJ"
  cat > "$NJ/nlohmann_jsonConfig.cmake" <<'EOF'
if(NOT TARGET nlohmann_json::nlohmann_json)
  add_library(nlohmann_json::nlohmann_json INTERFACE IMPORTED)
  get_filename_component(_nj_inc "${CMAKE_CURRENT_LIST_DIR}/../../../include" ABSOLUTE)
  set_target_properties(nlohmann_json::nlohmann_json PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${_nj_inc}")
endif()
EOF
  cat > "$NJ/nlohmann_jsonConfigVersion.cmake" <<'EOF'
set(PACKAGE_VERSION "3.12.0")
if(PACKAGE_VERSION VERSION_LESS PACKAGE_FIND_VERSION)
  set(PACKAGE_VERSION_COMPATIBLE FALSE)
else()
  set(PACKAGE_VERSION_COMPATIBLE TRUE)
  if(PACKAGE_VERSION VERSION_EQUAL PACKAGE_FIND_VERSION)
    set(PACKAGE_VERSION_EXACT TRUE)
  endif()
endif()
EOF
fi

cd /work/Player
cmake --preset emscripten-release -DPLAYER_JS_OUTPUT_NAME=index
cmake --build --preset emscripten-release -j"$(nproc)"
echo "=== PLAYER_BUILD_DONE_OK $(date) ==="
echo "--- output files ---"
ls -la build/emscripten-release | grep -E 'index\.' || ls -la build/emscripten-release
