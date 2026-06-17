#!/usr/bin/env bash
echo "=== official SDL ==="
grep -aoE 'SDL[0-9][.0-9]+|libSDL[0-9]|SDL_[A-Za-z]+' /tmp/official.wasm | sort | uniq -c | sort -rn | head -5
echo "=== custom SDL ==="
grep -aoE 'SDL[0-9][.0-9]+|libSDL[0-9]|SDL_[A-Za-z]+' /work/Player/build/emscripten-release/index.wasm | sort | uniq -c | sort -rn | head -5
echo "=== deps: 有沒有 SDL2 ==="
ls /work/buildscripts/emscripten/lib/ | grep -iE 'sdl' || echo none
ls /work/buildscripts/emscripten/lib/cmake/ | grep -iE 'sdl' || echo none
