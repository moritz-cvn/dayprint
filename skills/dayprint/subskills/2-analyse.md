# 2 · Analyse

Goal: `findings.json` (schema in `schemas/dayprint.findings-0.1.schema.json`) — who this person is at work, what repeats, what costs time, and where things get stuck. Every claim carries counted, paraphrased evidence.

## First: their working day

Run `python3 <skill>/scripts/rhythm.py --run <run> --consent <run>/consent.json`. It writes `day.json` from timestamps only: when the Mac is in use, when they write to agents and how fast they answer, their commit times, and app time from Screen Time when allowed. Read it before anything else; it tells you the person's tempo:

- **typical**: start, end, active hours, how often they work past midnight;
- **hours** and **weekdays**: when work happens;
- **tempo**: messages a day, the share that are short decisions, how fast they answer (`reply_median_s`), how long agents wait on them a day;
- **apps**: where screen time goes, by category.

A person who answers in under two minutes and sends a hundred decisions a day is fast, and their agents are waiting on them; a weekly report is no help to them, removing the wait is. Keep this in mind for every finding. With subagents, a day analyst can do this part in parallel ([../references/subagents.md](../references/subagents.md)).

## Read in this order

1. `stats.json` — start with `repeated_requests` (each pattern is a candidate workflow), then `calendar.recurring`, `programs` (script names like `invoice_hours.py` are gold), `agent_tools` and `mcp_servers_used`, `apps_mentioned`, `document_kinds`, `rhythm`.
2. Memory notes (`digest/claude-code-memory.jsonl`, `codex-memory.jsonl`, the `memory` and `project` items in `claude-export.jsonl`) — they state the person's role, tools and preferences in their own words.
3. The other digests, to confirm and size each candidate: open the items behind a pattern, count them, note the dates and weekdays.

## What to look for

- **Workflows** — the same kind of request three or more times, a recurring calendar block, a script run on a rhythm, a template in Documents. Name it the way anyone would ("Weekly client status update", "Monthly invoicing", "Proposal from call notes").
- **Time sinks** — long or frequent sessions, many follow-up turns on the same draft ("shorter", "again", "now in English"), meeting hours, manual copy steps between tools.
- **Hand-offs** — work that moves between people or tools: notes → tasks, timesheet → invoice, inquiry → call booking, designer → developer.
- **Pain points** — the person's own words of frustration in memory or prompts ("hate chasing", "always forget", "again"), overdue reminders, repeated re-explaining of context (brand voice pasted each time).
- **Documents** — templates, checklists, processes, brand guides: these become Knowledge and skills.
- **People and roles** — team size and roles (designer, developer, accountant, clients), from memory and calendar attendee counts. Roles, never names.
- **Tools** — every app seen, with where it was seen; map it to a Composio toolkit slug when one obviously exists (see [../references/cavion-product.md](../references/cavion-product.md)).

Leave out private life (trips, health, family, hobbies) unless the person asked for it; list what you left out in `not_used` in one short line each, without detail.

## Sizing a workflow

For each workflow set `per_month` (count divided by the months the data actually covers — `stats.json › data_span.months`, not the requested window), `minutes_each` (from session durations, meeting length, or a stated estimate; say which in `saving.note`), and a `share_low`/`share_high` of the work Cavion could take over. Compute `hours_per_week = per_month / 4.33 × minutes_each / 60 × share` for both ends — `validate.py` checks the arithmetic. [../references/time-saved.md](../references/time-saved.md) has typical shares by kind of work. Prefer conservative numbers; the person will trust a modest, explained estimate more than a large one.

## Writing each workflow

- `steps_today` — how it is done now, 3–6 short steps, from the evidence.
- `with_cavion.steps` — concrete steps in Cavion's own words (which agent, which Space, which task or check, which app, who approves). Fill `setup_keys` after step 4 so the report can link them.
- `own_tools.steps` — how to get most of the benefit with tools the person already has, without Cavion: a saved prompt or custom GPT/Claude project, a calendar reminder, a template, a Zapier/Make/Apps Script/Shortcuts automation, a small script. Be specific and honest; this part must be useful on its own. Add a ready-to-use `prompt` where a prompt is the core of it.
- `quick_win: true` marks candidates that take under an hour to set up and pay back within a week. `quick_wins` is the short list the report shows: at most five, each pointing to its workflow, phrased as one action.
- `tools[].composio`: use a slug only when it is in the app list in [../references/cavion-product.md](../references/cavion-product.md) or you have verified it; otherwise `null` (the setup file then gets a manual step "Look for <app> in Add app").

## Evidence

`evidence` entries say where and how often, paraphrased, as one sentence with the numbers inside `observation` (the report shows that text; `count` and `period` are for machines): "28 follow-up requests to shorten a client update, all on Fridays, Aug–Nov" — not quotes, never names, addresses, amounts tied to a person, or anything from a secret. One strong evidence line beats three weak ones. Give each finding a `confidence`.

Add `watch_outs` for things that need care when automating: e-mails to clients should stay drafts until reviewed; invoices involve money; anything personal.

Then fill the two things the report opens with:

- `person.short`: how the header names them, without names ("a three-person design studio").
- `week`: their repeated week, the first picture in the report. One entry per recurring item: `day` (mon … sun, `month` for monthly work, `any` for work without a fixed day), a short `title`, `minutes`, `agent` (true when an agent could draft it, false for meetings and work that stays with them), and `logo`, the key of the tool used for it today from `assets/logos/index.json` (gmail, notion, slack, google-meet, zoom, openai, claude …) or null. Take the days from the evidence: calendar blocks, prompt weekdays, script dates. Up to four items a day.

Write the headline last: one or two plain sentences that name the repeated work and put the hours inside the sentence ("Client updates, proposals and invoicing come back every week. Agents can draft them and give you 3 to 4 hours back."). The report colours the hours.

## Copy

The report is read by people who see a lot of AI-written text, so it has to read like a person who knows their work wrote it:

- Facts, counts and dates instead of adjectives. Evidence is a sentence about them ("You wrote 11 proposals in three months, each with the same five parts.").
- No em dashes, no "seamless", "unlock", "empower", "powerful", "robust" or similar; `validate.py` flags them.
- No labels above headings, no "not X but Y", no closing quips, no invented numbers.
- Short where there is little to say; longer only where the evidence is rich.

Run `python3 <skill>/scripts/validate.py findings <run>/findings.json` and fix every problem before step 3.
