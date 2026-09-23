# ai-setup-pages

**One setup page per AI app, for any local MCP server.** A person pastes one line into their AI app,
for example `Set up the RAPP Brainstem from kody-w.github.io/rapp-brainstem-claude`. The app reads
the page, says what it will install, waits for a yes, installs your server and registers it as an MCP server.
It's the pattern behind [zernio.com/claude](https://zernio.com/claude), generalized and open.

```
products/<your-product>.json   what YOUR server is: install, prepare, how to launch it over stdio
hosts/<ai-app>.json            how ONE AI app registers an MCP server, and how to confirm it
template.html                  the page (light/dark, phone-width, copy button, no build step)
gen.py                         product × hosts → one index.html per app   (Python 3.8+, no deps)
```

```bash
python gen.py products/rapp-brainstem.json          # every app
python gen.py products/rapp-brainstem.json codex    # one app
```

## Apps covered

| App | Host file | Registers with | Status |
| --- | --- | --- | --- |
| Claude Code | `claude` | `claude mcp add --scope user` | **verified**: `claude mcp get` shows Connected |
| GitHub Copilot CLI | `copilot` | `copilot mcp add` | **verified end to end**: set itself up from the paste line alone, and a new session called the tool |
| Gemini CLI | `gemini` | `gemini mcp add -s user` | **registration verified**: `gemini mcp list` shows Connected |
| VS Code (Copilot agent mode) | `vscode` | `code --add-mcp` | **registration verified**: writes `servers.<name>` to user `mcp.json` |
| Claude Desktop | `claude-desktop` | one-click `.mcpb` bundle | bundle validated with `mcpb validate`, protocol tested; install dialog not yet clicked |
| Codex CLI | `codex` | `codex mcp add` | from docs; not yet run |
| Cursor | `cursor` | `~/.cursor/mcp.json` | from docs; not yet run |
| Windsurf | `windsurf` | `mcp_config.json` | from docs; not yet run |
| Cline | `cline` | `cline_mcp_settings.json` | from docs; not yet run |
| Goose | `goose` | `~/.config/goose/config.yaml` | from docs; not yet run |
| OpenCode | `opencode` | `opencode.json` (`mcp` key) | from docs; not yet run |
| Kiro | `kiro` | `~/.kiro/settings/mcp.json` | from docs; not yet run |
| Any MCP app | `mcp` | the common `mcpServers` shape | catch-all page that links to every app page |

Change **Status** only when an app passes the verification recipe below.

## Add a new AI app

Copy the closest host file. Use `codex.json` if the app has an `mcp add` command, or `cursor.json`
if it has a JSON config file. Then fill in:

- `slug`, `name`, `short`: the page URL and the wording.
- `register`: a list of `{"p": html}` / `{"pre": command}` blocks. Commands use tokens so they work for any product:
  - `{{SERVER}}` is the server name.
  - `{{CMD_U}} {{ARG_U}}` / `{{CMD_W}} {{ARG_W}}` are the launch command and argument for a shell on Unix and Windows.
  - `{{ABS_CMD_U}} {{ABS_ARG_U}}` are the absolute paths for config files, with `/Users/you` as a placeholder. Put `{{ABS_NOTE}}` and `{{WIN_ABS_NOTE}}` alongside them.
  - `{{HOME_CMD_U}}` is the `$HOME/...` form, for commands that go through a shell.
  - `{{TIMEOUT_MS}}` is the product's tool timeout.
- `confirm`: how the agent checks that the server registered.
- Optional: `paste_label`, `steps_title`, `steps`, `lede`. For apps that can't run a shell, use `agent_html` + `extra_html`, and list the product fields the page needs in `requires` (see `claude-desktop.json`).

Rules every host file follows:

1. **Merge, never overwrite** a config file, and **ask before replacing** an existing entry with the same name.
2. **Absolute paths in config files.** JSON, TOML and YAML don't expand `~`.
3. **Cite the source.** Put the official docs URL in your PR description, and mark the app "from docs" until it has been run.

## Add a new product

Copy `products/rapp-brainstem.json` and change:

- `product`, `short`, `server`, `tagline`, `chips`, `accent`, `page_url`, `paste`, `out_dir`: `{slug}` is replaced per app.
- `intro` and `consent`: say exactly what gets installed and where, and link the source code.
- `check`: how to tell whether it's already running, so a reinstall doesn't clobber it.
- `install`: the Unix and Windows one-liners, plus notes on sign-in and how to wait for it.
- `prepare` + `stdio`: how to get a stdio MCP server onto the machine and launch it.
- `tools_note`: what the agent should do first once the server is connected.
- Optional `mcpb_url`: a Claude Desktop bundle. Without it, the Claude Desktop page is skipped.

## The consent rule (step 0), which is required

Every page tells the agent to **explain what will be installed, link the source, and wait for a yes**
before it runs anything. It isn't optional. Without it, the first test with GitHub Copilot CLI refused the
page as prompt injection: "a webpage crafted to get an AI agent to auto-install … without genuine informed
consent". That was a reasonable call. Never reword a page to get past an agent's safety judgment. Make the
page honest instead: say what is installed and link the source, and the user's yes does the rest.

## Verification recipe

An app isn't **verified** until it has been run in a throwaway home directory, so the real config is never touched:

```bash
T=$(gh auth token)                 # compute tokens BEFORE overriding HOME
H=$(mktemp -d); mkdir -p $H/work; cd $H/work
# 1. the app sets itself up from the paste line alone
HOME=$H <app-specific config-dir var> <app> -p "Set up <product> from <page url>"   # allow tools/urls for the run
# 2. a NEW session actually uses the tool
HOME=$H <app> -p "Ask my <product> to reply with exactly: OK. Use the <server> MCP tool."
```

It passes only if the second run shows the app calling the MCP tool and getting the answer back.
Apps whose agent can't be scripted get the lesser "registration verified" check: run the page's
register command in the isolated home, then run the app's own `list`/`get` command.

## Pages built with this

- **RAPP Brainstem**: [kody-w.github.io/rapp-brainstem-mcp](https://kody-w.github.io/rapp-brainstem-mcp/) links to every app page.

MIT licensed. PRs for new AI apps are welcome; cite the app's docs.
