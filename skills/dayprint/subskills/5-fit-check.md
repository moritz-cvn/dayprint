# 5 · Fit check

Goal: every workflow in `findings.json` carries a `fit` verdict that a critic has tried to break. Time saved on paper means nothing if the person waits longer, loses control, or has to change how they like to work.

## For each workflow, answer

- `speed`: does the person, or anything waiting on them, get an answer `faster`, the `same`, or `slower` than today?
- `on_critical_path`: does other work stop until this is done? (An approval that unblocks an agent is on the critical path; a weekly report usually is not.)
- `who_waits`: who or what waits, and for how long, under the new setup.
- `if_wrong`: what happens when the agent gets it wrong, and who notices.
- `verdict`: `keep`, or `reshaped` after changing the proposal. A proposal that cannot be made to fit is removed from `workflows` and listed in `dropped` with one line on why.
- `note`: one sentence the report shows, in plain words ("Drafts are ready when you look; nothing waits for them.").

## Rules that decide most cases

- Never make something on the critical path `slower`. Batching, digests and fixed time slots are only for work nothing is waiting on.
- For a `fast` person, prefer proposals that remove a step or answer instantly over proposals that collect work for later. Raise their own rules into standing permissions (what may run without asking) before adding any review step.
- Respect `must_not_slow` and `off_limits` from step 3 literally, and use `blocking_share` and the reply times in `day.json`: where agents sit idle until the person answers, nothing may add waiting.
- If the evidence for a workflow is thin, say so in the note rather than inflating it.

## The critic

Run a critic before you finalise. With subagents (Claude Code, Codex), start one with the brief in [../references/critic.md](../references/critic.md), giving it `findings.json`, `day.json` and the draft setup file and nothing else. Without subagents, read that brief and do the pass yourself, in a separate step, arguing against your own plan.

Apply what holds up: reshape, drop, or keep with a clearer note. Apply a reshape everywhere it shows: the workflow's steps, its agent card (trigger, instructions, output) and the setup file's agents, tasks and checks. Then `python3 <skill>/scripts/validate.py findings <run>/findings.json` checks that nothing on the critical path got slower and that every workflow has a verdict.
