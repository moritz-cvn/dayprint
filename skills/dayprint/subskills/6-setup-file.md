# 4 · Setup file

Goal: `cavion-workspace.json` — the design from step 3 as a machine-readable blueprint (schema `cavion.workspace-setup/0.1`, file `schemas/cavion.workspace-setup-0.1.schema.json`), plus `apply-plan.md`, the same thing as a checklist for people.

## Why it looks the way it does

A future Cavion MCP will read this file and set the workspace up. Three properties make that safe:

- **Idempotent.** Every object has a `key` (lowercase, hyphens, unique across the file). The applier keeps a ledger of `setup_id/section/key → Cavion id`, so applying the same file again changes nothing, and a raised `revision` shows only what changed. Choose a `setup_id` once (e.g. `onb-2026-11-07-studio`) and keep it when you edit the file.
- **Reviewable.** Each object has `status` (`proposed` until the person approves it; `skipped` to keep it in the file without applying), a one-line `why`, `evidence` ids from `findings.json`, and a `confidence`. The applier works in batches of at most six steps — the size of one Cavion setup proposal — each approved by the person.
- **Never risky.** `apply_policy.prune` is always false (nothing is deleted), `automations_start` is always `paused`, `send_delete_share` is never Allowed, `autonomous_sending` is always false. No credentials, e-mail addresses or real names anywhere: members are roles (`"title": "Designer"`), invitations are typed by a person later.

## Writing it

Fill the sections in this order; each refers to keys defined before it.

1. `workspace` — name (ask, or use "<organisation kind> workspace"), timezone, `run_with`, optional `keys` (provider and a suggested monthly budget, never the key), `talk`, `allowed_websites` (domains the agents' browser will need, from the evidence).
2. `members` — the person as `owner` with `invite: "self"`, then one entry per role seen (`invite: "later"`).
3. `spaces` — name, purpose (one or two sentences an agent can act on), colour, `agent_access`, members (owner first), `projects` for long-running streams (one per client or campaign when the evidence shows them; use roles or client types, not client names, unless the person agreed).
4. `connections` — one per app account: `type` composio (with the Composio toolkit slug) or mcp, `scope` personal (with `owner`) or space (with `space`), `permissions`.
5. `agents` — the personal assistant (`owner`), each Space manager (`space`), specialists. Instructions are the heart: who they work for, what they do, which Knowledge to follow, what they must never do without asking. Up to 4,000 characters; usually 600–1,500 is right. Give each agent only the apps it needs.
6. `knowledge` — Markdown documents, drafted from the person's own material. Keep them short and useful: a checklist, a price list, a voice guide, a template.
7. `memory_seeds` — a few one-sentence facts per agent (role of the person, language preferences, standing rules).
8. `skills` — `SKILL.md` with frontmatter `name` and `description`, then steps. `fallback: "knowledge"`.
9. `scheduled_tasks` — `title`, `agent`, `conversation` (`private` for the assistant, `space_shared` for a Space chat, with `space` and optional `project`), `kind` (`scheduled_task`, or `responsibility` for an ongoing duty), `instruction` (what to do, where to look, what to deliver, when to stay quiet), `timing`, `preparation` (`read_only` for reports, `cavion_deliverables` when it drafts documents), `apps` with per-task permissions (only apps the agent has), `knowledge` keys, `notification` (`meaningful` by default).
10. `checks` — `app` (a connection the agent has, with Read allowed), `reads` in plain words, `instruction`, `every_minutes`.
11. `event_automations` — only when an instant trigger would clearly be better than a check; always with `available: false` and its fallback check.
12. `devices`, `manual_steps`, `provenance`. `plan.py` already turns `devices`, `members` (invitations), `workspace.run_with`/`keys` and every connection into steps for the person, so `manual_steps` is only for what else the person must do or decide (a choice of funding when `run_with` is undecided, a list of sites to add, an app to look for) — each with the exact place in Cavion and `unblocks` naming the keys it is needed for, so the plan puts it right before them. `provenance` (file names, `sources_read` from the read log, `uploaded: false`).

Then go back to `findings.json` and fill each workflow's `with_cavion.setup_keys`.

## Validate and plan

```bash
python3 <skill>/scripts/validate.py setup <run>/cavion-workspace.json <run>/findings.json
python3 <skill>/scripts/plan.py <run>/cavion-workspace.json --out-dir <run>
```

Fix every problem the validator reports (unknown keys, apps not assigned to an agent, memory over budget, timing rules, leaks). `plan.py` writes `apply-plan.json` and `apply-plan.md`: the steps for the person (money, devices, sign-ins, invitations) and the agent steps in batches, each with a message the person can paste into their Cavion assistant today to have it propose that batch.
