# Choose who makes each part of a site

Webby can accept a simple instruction such as “Use Codex for the whole website” or “Codex builds the layout and Claude Code writes the FAQ.” Codex and Claude Code are coding agents. A selected agent writes its assigned files; Webby reviews the result, runs the site's checks, and opens the usual pull request. The site owner still decides when to publish.

The companion runner here is **optional and local**. The hosted Plow Webby does not yet run these coding agents. It can prepare the assignment plan, while a local operator with Docker and the relevant subscriptions runs the plan. No API key is required for this local route; each agent uses its own subscription login. Codex requires ChatGPT/Codex access, and Claude Code requires an eligible Claude plan. Each plan step only runs when its agent is connected.

## One-time setup

From the Webby repository, build the separate runner image. It contains the Codex and Claude Code CLIs and no GitHub credential or Webby cloud state:

```sh
docker build -f model-runner/Dockerfile -t webby-model-runner:local .
```

Connect only the agents you want to use. The first command prints a Codex device-login code; [OpenAI's setup guide](https://learn.chatgpt.com/docs/auth#preferred-device-code-authentication-beta) says personal accounts must enable device-code login in ChatGPT security settings, or a workspace admin must enable it in workspace permissions. The second starts Claude Code's subscription browser login. Each login is stored in a separate, private directory under `~/.local/share/webby-model-runner/` on this computer. Do not paste tokens into chat or commit them.

```sh
python3 scripts/webby-model-runner login codex
python3 scripts/webby-model-runner login claude
python3 scripts/webby-model-runner doctor
```

`doctor` reports each agent separately and succeeds when at least one is ready. Use `doctor codex` or `doctor claude` to check the agent requested for a particular site. Before every run, Webby checks only the agents in that plan. Codex also needs its Linux sandbox to start inside Docker; if Docker blocks that nested sandbox, the runner stops before touching the website. It will not switch to unrestricted Codex execution while the subscription login is present.

The runner needs Docker on the machine doing the work. Keep that machine's Docker daemon and subscription login directories under the owner's control. The runner has access to the selected subscription credential and site source while it works, but does not mount the Plow volume, the host home directory, a GitHub token, or the Docker socket into the coding-agent container.

## Give each agent a job

Save a plan outside the website checkout, for example `/tmp/webby-site-plan.json`:

```json
{
  "brief": "Create a clear, visually distinctive site for Acme. It helps independent shops manage inventory. The main action is an email link to hello@example.com.",
  "steps": [
    {
      "agent": "codex",
      "task": "Build the page structure and visual system.",
      "paths": ["site/**"]
    },
    {
      "agent": "claude",
      "task": "Refine the FAQ answers using only the supplied company facts.",
      "paths": ["site/faq.html"]
    }
  ]
}
```

For a whole-site choice, use one step with the chosen agent and `"paths": ["site/**"]`. For split work, later steps see earlier ones. The runner refuses changes outside each step's assigned paths, so assign the actual files the agent may edit. Start with a clean Git branch in the website repository, then run:

```sh
python3 scripts/webby-model-runner run /tmp/webby-site-plan.json \
  --repo /path/to/website-repo --patch /tmp/webby-site.patch
git -C /path/to/website-repo apply --check /tmp/webby-site.patch
```

Review the patch before applying it. The runner does not edit the original checkout. After review, apply the patch, run the website's checks and preview, then open a pull request through Webby's ordinary GitHub workflow. A patch does not prove the site is live or improve its placement in any search product. The useful outcome is the owner's ability to pick creative contributors while Webby keeps the resulting website coherent and easy to use.
