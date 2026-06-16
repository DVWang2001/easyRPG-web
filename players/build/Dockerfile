# 建置 EasyRPG Player 網頁版(WASM)用的環境。
# 注意:用 glibc 基底(Debian slim),不可用 Alpine —— EasyRPG buildscripts 會下載
# 預編 emsdk 工具鏈(glibc 連結),在 musl/Alpine 上無法執行。
# debian:12-slim 比 ubuntu 小;真正佔空間的是 emsdk 與依賴(都在 /work volume,建置完即刪)。
FROM debian:12-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        git cmake python3 build-essential \
        unzip meson ninja-build pkg-config autoconf automake libtool \
        curl ca-certificates xz-utils bzip2 patch \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["sleep", "infinity"]
