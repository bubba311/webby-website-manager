FROM public.ecr.aws/e1h7x4a2/plow-cloud-agents:base-1e73c82c4b3e0c9f76935bc0cc45061875b34aee@sha256:5f8ef7c3762b037420cd8843a767a7ab7e2433b1c8319e7cfe2ad1bdef5dee8a

LABEL org.opencontainers.image.title="Webby Website Manager" \
      org.opencontainers.image.description="Built to win the agentic economy: distinctive websites with clear answers and usable actions built in" \
      org.opencontainers.image.licenses="MIT"

USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gh jq python3-minimal \
 && rm -rf /var/lib/apt/lists/* \
 && install -d -m 0700 -o node -g node /var/lib/plow/gh /var/lib/plow/sites

RUN npm install --global @openai/codex@0.157.1 @anthropic-ai/claude-code@2.1.281 \
 && npm cache clean --force

RUN npm install --prefix /opt/webby/browser --no-audit --no-fund --save-exact playwright@1.63.0 \
 && PLAYWRIGHT_BROWSERS_PATH=/opt/webby/browser/browsers /opt/webby/browser/node_modules/.bin/playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*

ENV AGENT_ID=webby-website-manager \
    AGENT_NAME="Webby Website Manager" \
    AGENT_BLURB="Built to win the agentic economy. Webby creates distinctive websites from chat, with clear answers for AI search and usable actions for browsing agents built in. Choose your models; review every change." \
    GH_CONFIG_DIR=/var/lib/plow/gh \
    WEBBY_SITES_DIR=/var/lib/plow/sites \
    WEBBY_MODEL_STATE_DIR=/var/lib/plow/models \
    WEBBY_BROWSER_MODULE=/opt/webby/browser/node_modules/playwright \
    PLAYWRIGHT_BROWSERS_PATH=/opt/webby/browser/browsers

COPY prompt/AGENTS.md /opt/plow/prompt/AGENTS.md
COPY skills/ /opt/plow/skills/
COPY starter-site/ /opt/webby/starter-site/
COPY scripts/webby-github-login /usr/local/bin/webby-github-login
COPY scripts/webby-site-audit /usr/local/bin/webby-site-audit
COPY scripts/webby-model-draft /usr/local/bin/webby-model-draft
COPY scripts/webby-model-connect /usr/local/bin/webby-model-connect
COPY scripts/webby-render-check /usr/local/bin/webby-render-check
USER node
