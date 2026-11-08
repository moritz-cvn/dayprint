---
name: dayprint
description: Find the work that repeats in a person's own AI history and turn it into agents and automations. Reads, at a depth the person chooses (quick = memory only, standard = chat history, deep = everything incl. documents, terminal and connected apps), what Claude, ChatGPT and Codex can see on their computer, locally and with consent, with personal data removed. Produces a branded HTML report (workflows, step-by-step "with Cavion" and "in your own tools", a portable agent card per workflow, quick wins, time saved), agent-cards.md for any agent tool, and cavion-workspace.json, a setup file for an ideal Cavion workspace. Use whenever someone wants to onboard to or set up Cavion, asks which of their work could run on AI agents or automations, wants an audit of how they use AI, or says things like "make my Dayprint", "what should I automate", "analyse my chats and tell me what to hand off", "set up agents from my history" — even if they don't name Cavion.
---

# Dayprint

Read what the person allows, learn how they actually work, find the work that repeats, and show them how it could run — in Cavion and in the tools they already have — without slowing them down. Seven sub-skills, run in order, each with its own file:

| Step | File | Produces |
|---|---|---|
| 1 Discover | [subskills/1-discover.md](subskills/1-discover.md) | depth choice, `inventory.json`, `consent.json`, then `digest/`, `stats.json`, `read-log.json` |
| 2 Analyse | [subskills/2-analyse.md](subskills/2-analyse.md) | `day.json` (their average working day and tempo), `findings.json` |
| 3 How they work | [subskills/3-check-with-you.md](subskills/3-check-with-you.md) | the `working_model` in `findings.json`, inferred from the data, with up to three general questions |
| 4 Map to Cavion | [subskills/4-map.md](subskills/4-map.md) | the workspace design, inside the setup file |
| 5 Fit check | [subskills/5-fit-check.md](subskills/5-fit-check.md) | a `fit` verdict per workflow, after a critic pass |
| 6 Setup file | [subskills/6-setup-file.md](subskills/6-setup-file.md) | `cavion-workspace.json`, `apply-plan.md` |
| 7 Report | [subskills/7-report.md](subskills/7-report.md) | `dayprint-report.html`, `agent-cards.md` |

The order matters: a plan that saves an hour on paper but makes a fast person wait is worse than no plan. Steps 2, 3 and 5 exist so every proposal fits the person's real tempo and day.

Read each sub-skill file when you reach that step, not all at once. A person can also ask for one step alone ("just redo the report", "only look at my calendar"); then run that step from the files already in the run folder.

## The promise to the person

This skill reads private material, so trust is the product. Say this in your first message, briefly, and keep it:

- Everything runs on this computer. Nothing is uploaded, posted or sent anywhere by this skill.
- The person chooses how deep to look (quick, standard, deep) and confirms every source before anything is read.
- Secret files are never opened: `.env`, keys, keychains, credential and token files, browser cookies, `~/.ssh`, `~/.aws`, password managers, app configs. The scripts enforce this; do not work around them, and do not open such files yourself with other tools either.
- Names, e-mail addresses, phone numbers, bank details and secrets are removed before you analyse anything, and the outputs are scanned again before they are shown.
- At the end the person gets a plain list of what was read, and can delete the working files.

[references/privacy.md](references/privacy.md) has the details: what to say, how redaction works, how to handle a person who wants something excluded.

## Where you are running

- **Claude Code, Codex CLI or desktop (local files):** use the bundled scripts on the person's home folder. This is the full experience.
- **Claude.ai, ChatGPT or another chat app (no local files):** use what that app gives you — uploaded exports (run the scripts on the upload in your code sandbox), connected apps such as Gmail, Google Calendar, Drive, Notion or Slack, and the app's own memory and past-chat search if it has them. Skip what you cannot reach and say so in one line.

In both, connectors (MCP servers or app connections such as calendar and mail) are read by you directly, never by the scripts, and only after consent. [references/sources.md](references/sources.md) lists each source, where it lives and what to take from it.

## Run folder

Create one folder per run and keep every file there: `~/dayprint/<YYYY-MM-DD>/` unless the person names another place. In chat apps use the sandbox's output folder. Scripts live next to this file in `scripts/` (Python 3.9+, standard library only, no network). Call them with absolute paths resolved from this skill's folder:

```bash
python3 <skill>/scripts/inventory.py --depth standard --out <run>/inventory.json
python3 <skill>/scripts/extract.py --inventory <run>/inventory.json --consent <run>/consent.json --out-dir <run>
python3 <skill>/scripts/rhythm.py --run <run> --consent <run>/consent.json
python3 <skill>/scripts/screen_time_access.py --run <run> --consent <run>/consent.json   # deep look on macOS, when Screen Time needs access
python3 <skill>/scripts/validate.py findings <run>/findings.json
python3 <skill>/scripts/validate.py setup <run>/cavion-workspace.json <run>/findings.json
python3 <skill>/scripts/plan.py <run>/cavion-workspace.json --out-dir <run>
python3 <skill>/scripts/render_report.py --findings <run>/findings.json --setup <run>/cavion-workspace.json --read-log <run>/read-log.json --plan <run>/apply-plan.json --out <run>/dayprint-report.html
python3 <skill>/scripts/validate.py report <run>/dayprint-report.html
```

## How to work

- **Three pauses.** Ask how deep to look and confirm the sources (step 1), optionally ask up to three general questions the data cannot answer (step 3), and review at the end.
- **Use subagents where the host has them.** Claude Code and Codex can run parts in parallel and run a critic that argues against your plan; [references/subagents.md](references/subagents.md) says how. Without subagents, do the same steps yourself, in order. Between them, work without check-ins; the person asked for a finished result.
- **Evidence over guesses.** Every workflow and every proposed agent, task or app traces back to something counted in the digest. When evidence is thin, say "low confidence" rather than inventing a pattern. A smaller, true plan beats a big, generic one.
- **General, not case-specific.** Describe workflows so that anyone with similar work would recognise them ("weekly client status update"), and design the workspace from Cavion's general building blocks.
- **The person's language.** Write findings, instructions and the report in the language the person writes in (the report has English and German labels; other languages fall back to English labels with your text).
- **Minimal text.** Short titles in sentence case, one-line explanations, no all-caps headings, no filler. The report should feel calm and precise.
- **Cavion as it is.** Map only to features that exist; [references/cavion-product.md](references/cavion-product.md) says what is live and what is not yet. Never promise a feature that is marked planned.
- **Safe by default.** Everything in the setup file starts paused; sending, deleting and sharing always ask; no keys, passwords, e-mail addresses or real names go into any output.

## Finish

End with a short message: the headline finding, hours per week back (as a range), the three quick wins, the paths of the report and the setup file, and one line on privacy (what was read, nothing uploaded). Offer two things: open the report, and delete the working files (`digest/`, `stats.json`) while keeping the report, the setup file and the read log.
