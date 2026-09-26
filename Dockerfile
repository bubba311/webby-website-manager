FROM public.ecr.aws/e1h7x4a2/plow-cloud-agents:base-1e73c82c4b3e0c9f76935bc0cc45061875b34aee@sha256:5f8ef7c3762b037420cd8843a767a7ab7e2433b1c8319e7cfe2ad1bdef5dee8a

LABEL org.opencontainers.image.title="Webby Website Manager" \
      org.opencontainers.image.description="Beautiful GitHub-backed sites with search and AI-agent readability built in" \
      org.opencontainers.image.licenses="MIT"

USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gh jq python3-minimal \
 && rm -rf /var/lib/apt/lists/* \
 && install -d -m 0700 -o node -g node /var/lib/plow/gh /var/lib/plow/sites

ENV AGENT_ID=webby-website-manager \
    AGENT_NAME="Webby Website Manager" \
    AGENT_BLURB="Build a beautiful startup website from chat. Clear pages for people, search, and AI agents come built in; review every change." \
    GH_CONFIG_DIR=/var/lib/plow/gh \
    WEBBY_SITES_DIR=/var/lib/plow/sites

COPY prompt/AGENTS.md /opt/plow/prompt/AGENTS.md
COPY skills/ /opt/plow/skills/
COPY starter-site/ /opt/webby/starter-site/
COPY scripts/webby-github-login /usr/local/bin/webby-github-login
COPY scripts/webby-site-audit /usr/local/bin/webby-site-audit
USER node
