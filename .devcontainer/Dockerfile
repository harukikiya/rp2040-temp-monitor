FROM debian:bookworm-slim

# 基本ツール + PlantUML（Java依存）
RUN apt-get update && apt-get install -y \
    make \
    git \
    curl \
    ca-certificates \
    plantuml \
    default-jre-headless \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# UTF-8ロケール(slimでもC.UTF-8は標準で利用可能)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# uvインストール(公式インストーラ)
ADD https://astral.sh/uv/install.sh /tmp/uv-install.sh
RUN sh /tmp/uv-install.sh && rm /tmp/uv-install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

COPY pyproject.toml uv.lock* /tmp/build/
RUN cd /tmp/build && (uv sync --frozen || uv sync)

CMD ["bash"]