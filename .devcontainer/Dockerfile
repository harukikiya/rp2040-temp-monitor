FROM debian:bookworm-slim

# 基本ツール
RUN apt-get update && apt-get install -y \
    make \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uvインストール（公式インストーラ）
ADD https://astral.sh/uv/install.sh /tmp/uv-install.sh
RUN sh /tmp/uv-install.sh && rm /tmp/uv-install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

# pyproject.tomlとuv.lockをコピーして依存をインストール
# （postCreateCommandでも実行されるが、イメージレイヤキャッシュのため先行実行）
COPY pyproject.toml uv.lock* /tmp/build/
RUN cd /tmp/build && uv sync --frozen || uv sync

CMD ["bash"]