FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
LABEL authors="NootNoot"

WORKDIR /app

RUN apt-get update && apt-get install curl jq -y

# install rust
RUN curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# install twgpu dependencies
RUN apt-get install -y build-essential cmake pkg-config libclang-dev clang \
    llvm-dev libavcodec-dev libavutil-dev libavformat-dev libavfilter-dev \
    libavdevice-dev

RUN . "/root/.cargo/env" && cargo install twgpu-tools

COPY . .
COPY --chmod=755 install.sh entrypoint.sh ./

RUN ./install.sh --docker

ENTRYPOINT ["./entrypoint.sh"]
