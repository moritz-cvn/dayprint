# Dayprint

![A Dayprint report for a sample design studio](design/landing/hero.png)

A skill for Claude and Codex that reads what your AI tools know about your work — on your computer, with your consent per source — finds the work that repeats, and plans the Cavion workspace that would take it over.

First it asks how deep to look: **quick** (only what the AI tools remember), **standard** (plus chat history and calendar) or **deep** (everything, including documents, terminal history and connected apps).

You get three files:

- **`dayprint-report.html`** — a self-contained report in Cavion's design: what was read, what was found, each workflow with step-by-step "with Cavion" and "in your own tools", quick wins and time saved. Useful even if you never use Cavion. Works offline and prints on A4.
- **`agent-cards.md`** — one agent per workflow (instructions, trigger, tools, what you approve), ready for ChatGPT or Claude projects, custom GPTs, n8n, Zapier or Cavion.
- **`cavion-workspace.json`** — the workspace as a setup file (schema `cavion.workspace-setup/0.1`): Spaces, agents, app connections, Knowledge, memory, skills, scheduled tasks and checks. Cavion's setup tool will apply it automatically; until then `apply-plan.md` lists the steps and gives you messages to paste into your Cavion assistant.

## Privacy

- Runs locally. Nothing is uploaded, posted or sent.
- You choose the depth and confirm every source before anything is read.
- Secret files are never opened (`.env`, keys, keychains, credential and token files, cookies, `~/.ssh`, `~/.aws`, app configs).
- Names, e-mail addresses, phone numbers, bank details, URLs and secrets are removed before analysis, and every output is scanned again.
- `read-log.json` lists exactly what was read. Working files can be deleted at the end.

## Install

### Claude Code

In Claude Code:

```
/plugin marketplace add moritz-cvn/dayprint
/plugin install dayprint@cavion
```

Or from a terminal:

```bash
git clone --depth 1 https://github.com/moritz-cvn/dayprint.git && dayprint/install.sh --claude
```

### Codex (CLI, IDE, ChatGPT desktop app)

Ask Codex: `$skill-installer install https://github.com/moritz-cvn/dayprint/tree/main/skills/dayprint`, or run `install.sh --codex` from a clone. Restart Codex and type `$dayprint`.

### Claude and ChatGPT apps

Download [dayprint.zip](https://github.com/moritz-cvn/dayprint/releases/latest/download/dayprint.zip) and upload it as a skill (Claude: Settings › Capabilities › Skills). In the apps the skill works with uploaded exports (ChatGPT and Claude.ai data exports, calendar `.ics` files), connected apps such as Gmail, Calendar, Drive or Notion, and the app's own memory. Local files on your computer are only available in Claude Code and Codex.

## Use

Ask: *"Make my Dayprint"*, *"Plan my Cavion workspace from my work"*, *"What in my work could run on agents?"* or *"Analyse my ChatGPT history and tell me what to automate."* The skill asks how deep to look and which sources to use, rebuilds your average working day from timestamps (when your Mac is on, when you write to agents and how fast you answer, your commits, and Screen Time if allowed), learns your tempo, and only then proposes anything. Every proposal goes through a fit check, with a critic subagent where the tool has subagents, so nothing makes your work slower. Results go to `~/dayprint/<date>/`.

## What is inside

```
dayprint/
├── README.md, install.sh, plugin.json, .claude-plugin/, .codex-plugin/
├── skills/dayprint/        the skill (this is what gets installed)
│   ├── SKILL.md                     the main flow and the privacy promise
│   ├── subskills/                   1-discover, 2-analyse, 3-check-with-you, 4-map, 5-fit-check, 6-setup-file, 7-report
│   ├── references/                  privacy, sources, Cavion product, mapping patterns, time saved, critic, subagents
│   ├── schemas/                     JSON Schemas for the setup file and the findings
│   ├── scripts/                     inventory, extract, rhythm, validate, plan, render_report (Python 3.9+, no packages, no network)
│   ├── assets/                      report elements (from the Paper design), Inter, Cavion mark, Lucide glyphs, real product logos (CC0)
│   ├── agents/openai.yaml           Codex app metadata
│   └── evals/                       test cases
├── examples/persona-lena/           synthetic test persona and its full sample output
└── install.sh --zip                 builds the zip for the Claude and ChatGPT apps
```

## Sample

`examples/persona-lena/` is an invented founder of a three-person design studio: ChatGPT and Claude.ai exports, Claude Code and Codex sessions, terminal history, a calendar, documents, and decoy secret files that must never be read. `make_persona.py` rebuilds it; `output/` holds the full run: `dayprint-report.html`, `agent-cards.md`, `cavion-workspace.json`, `findings.json`, `apply-plan.md`, `read-log.json`.

## Design

The report is built from the templates in `skills/dayprint/assets/report/elements.html`: real product logos, the person's real week first, one dark band, no filler.

## Licence

Dayprint is MIT licensed (`LICENSE`). Bundled third-party files keep their own licences: Inter: SIL Open Font License 1.1 (`assets/fonts/Inter-OFL.txt`). Lucide icons: ISC (`assets/LICENSE-lucide.txt`). Product logos: gilbarbara/logos and simple-icons, both CC0 (`assets/logos/index.json`); every mark is its owner's trademark.
