# Test persona: a three-person design studio

Everything here is invented. "Lena Hoffmann" runs "Studio Nordlicht", a brand and web studio in Hamburg, with a designer and a freelance developer. Clients, people, e-mail addresses, phone numbers, the IBAN and all keys are fictional.

`python3 make_persona.py` rebuilds `home/` deterministically (seed 42, dates August–November 2026):

| Source | What is in it |
|---|---|
| ChatGPT export zip | 74 conversations: Friday status mails, proposals, LinkedIn posts, inquiry replies, call notes to tasks, and a few private topics |
| Claude.ai export zip | 23 conversations, 2 projects (brand voice, proposals), memory |
| Claude Code | 9 sessions in 4 projects (site builds, launch QA, monthly invoicing), memory notes, prompt history |
| Codex | 4 sessions building small scripts (asset renaming, invoice lines, link checker), history, AGENTS.md |
| Terminal | `.zsh_history` with timestamps: git, npm, the invoice script on the 1st, the link checker on Mondays |
| Calendar | `.ics` with recurring planning, stand-ups, a client check-in, invoicing, content and status-mail blocks, discovery and review calls |
| Documents | templates, processes, brand voice, client call notes, a time-tracking CSV, a private note |
| Applications | Figma, Notion, Slack, Toggl Track, VS Code, Claude, ChatGPT, Codex, Zoom … |

## Decoys

These files contain `DECOY-SECRET-DO-NOT-READ` and must never be opened or appear in any output: `.claude/.credentials.json`, `.claude/settings.json`, `.codex/auth.json`, `.codex/config.toml`, `.ssh/id_ed25519`, `.aws/credentials`, `Documents/Studio/ops/.env`. Transcripts also contain the marker inside tool output and command arguments, which the extractor must skip. Check with:

```bash
grep -rl DECOY-SECRET output/ || echo clean
```

## Sample output

`output/` is a complete run of the skill: `inventory.json`, `consent.json` (all sources allowed, people's names masked; the persona agreed to show the studio's name), `digest/`, `stats.json`, `read-log.json`, `findings.json`, `cavion-workspace.json`, `apply-plan.json`, `apply-plan.md` and `dayprint-report.html`.

Result: 9 workflows, 2.9–4.1 hours a week back; a workspace with the founder's assistant and three Spaces — Clients (Open), Finance (Members only) and New business (Open) — with two specialists, five scheduled tasks, two checks and nine Knowledge documents.
