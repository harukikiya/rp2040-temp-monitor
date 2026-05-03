FROM ubuntu:24.04

# UTF-8ロケール
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# 基本ツール + Clang/LLVM ツールチェイン + デバッガ + デバッガ通信
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    make \
    git \
    curl \
    wget \
    ca-certificates \
    unzip \
    xz-utils \
    python3 \
    libpython3-dev \
    clang \
    clang-tidy \
    clang-format \
    lld \
    llvm \
    gdb-multiarch \
    openocd \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

# ARM GNU Toolchain (Arm社公式バイナリ、aarch64用)
# gcc, newlib を主に使用。同梱のgdbは古いncursesに依存し動かないため、
# デバッグには代わりに gdb-multiarch を使う。
ARG GCC_ARM_VERSION=14.2.rel1
RUN cd /opt && \
    wget -q https://developer.arm.com/-/media/Files/downloads/gnu/${GCC_ARM_VERSION}/binrel/arm-gnu-toolchain-${GCC_ARM_VERSION}-aarch64-arm-none-eabi.tar.xz && \
    tar xJf arm-gnu-toolchain-${GCC_ARM_VERSION}-aarch64-arm-none-eabi.tar.xz && \
    rm arm-gnu-toolchain-${GCC_ARM_VERSION}-aarch64-arm-none-eabi.tar.xz && \
    mv arm-gnu-toolchain-${GCC_ARM_VERSION}-aarch64-arm-none-eabi /opt/gcc-arm-none-eabi
ENV PATH="/opt/gcc-arm-none-eabi/bin:${PATH}"

# svdconv のインストール
ARG SVDCONV_VERSION=3.3.47
RUN mkdir -p /opt/svdconv && \
    cd /tmp && \
    wget -q https://github.com/Open-CMSIS-Pack/devtools/releases/download/tools%2Fsvdconv%2F${SVDCONV_VERSION}/svdconv-${SVDCONV_VERSION}-linux-arm64.tbz2 && \
    tar xjf svdconv-${SVDCONV_VERSION}-linux-arm64.tbz2 -C /opt/svdconv && \
    chmod +x /opt/svdconv/svdconv && \
    ln -s /opt/svdconv/svdconv /usr/local/bin/svdconv && \
    rm svdconv-${SVDCONV_VERSION}-linux-arm64.tbz2

WORKDIR /workspace

CMD ["bash"]