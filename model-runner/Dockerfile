FROM node:22-bookworm-slim

ARG CODEX_VERSION=0.156.1
ARG CLAUDE_VERSION=2.1.281

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && npm install --global "@openai/codex@${CODEX_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
 && mkdir -p /work /home/webby

WORKDIR /work
ENV HOME=/home/webby
