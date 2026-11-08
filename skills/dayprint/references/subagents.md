# Subagents

Claude Code (the Agent tool) and Codex (sub-agents) can run parts of this skill in parallel and give you a second opinion. Use them when the person chose the standard or deep look; for a quick look, work alone.

## What runs where

The scripts stay the privacy layer: subagents read only the run folder's redacted files (`digest/`, `stats.json`, `day.json`), never the person's raw sources. Tell each subagent that, and give it the run folder path.

After `extract.py` and `rhythm.py`, start these together:

1. **Day analyst.** Reads `day.json` and `stats.json`. Returns: the typical day in five lines, the tempo facts for `working_model.facts`, and two or three hypotheses about what matters to the person (speed, interruptions, what they keep).
2. **Workflow miner.** Reads `stats.json` and `digest/`. Returns: candidate workflows with counts, dates, minutes and one evidence sentence each, plus pain points and hand-offs. No proposals yet.
3. **Tools and documents.** Reads the tool, app, document and memory digests. Returns: the tools in use with Composio slugs where certain, the documents that should become Knowledge, and the person's own written rules.

Merge their answers into `findings.json` yourself; you own the result.

After the map (step 4), start the **critic** with [critic.md](critic.md) and the three files it names.

## Brief template

> Read only these files in `<run>`: … Do not open anything else on this computer. Return plain JSON-friendly lists, short sentences, no names or contact details. Private life (health, family, money, leisure, travel, devices at home): count it only, as one number, and never name or describe its topics. Name workflows by the kind of work, not by product, client or project names. Your job: …

## Workflows

If the person asks for a full multi-agent run and the host offers a workflow tool, the same four roles map to one workflow: three analysts in parallel, then the critic. Without that request, plain subagents are enough.
