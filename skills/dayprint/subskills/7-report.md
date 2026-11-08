# 5 · Report

Goal: `dayprint-report.html`, one self-contained file in Cavion's brand that the person can open offline, print, and share. It has value even for someone who never uses Cavion: every workflow says how to do it in their own tools too.

## Render

```bash
python3 <skill>/scripts/render_report.py --findings <run>/findings.json --setup <run>/cavion-workspace.json \
  --read-log <run>/read-log.json --plan <run>/apply-plan.json --out <run>/dayprint-report.html
python3 <skill>/scripts/validate.py report <run>/dayprint-report.html
```

The report is built from fixed elements in `assets/report/elements.html`, one template per element, matching the `el/*` layers of the Paper design "Cavion · Onboarding report" (board OR02). The design follows the tasteskill rules: the hours inside the headline instead of a row of figures, the person's real week as the first picture, a flow diagram with real product logos for each job, lines instead of boxes, and one dark band for the Cavion workspace. The renderer only picks elements and fills them with this person's data, so do not hand-write HTML; improve the report by improving `findings.json` and the setup file. Sections, in order: the headline with what it is based on, the repeated week, how they work (an hour-by-hour strip of their average day from `day.json`, three or four tempo facts, and what they told you), each job (with its fit line under the hours), what was left out after the fit check, (hours, evidence, flow, "In Cavion", "In tools you already have", instructions for any agent), the Cavion workspace band, start with these, set it up, where the hours come from, what was read, and one line to cavion.io.

It also writes `agent-cards.md`: every agent card as plain Markdown, for people who build in ChatGPT or Claude projects, custom GPTs, n8n or Zapier.

## Review before showing

Open the HTML (or read it back) and check, as the person would:

- The headline is true, specific and modest. The hours range adds up to the table.
- No names, addresses, amounts tied to a person, or private topics appear anywhere. The validator catches patterns; you catch meaning (a client's name in a workflow title, a family member in a finding).
- Every "with Cavion" step uses real Cavion names (Spaces, Inbox, Allow once, Manage › AI …) and nothing marked planned.
- Every "in your own tools" list is something the person could start today.
- Text is short. Cut any sentence that does not help a decision.

## The second pause

Show the person the headline, the hour range, the quick wins and the file paths. Ask whether anything should change — a workflow that is wrong, a Space they would name differently, something to drop. Apply changes to the JSON files, raise nothing else, re-run validate, plan and render. When they are happy, set the approved objects' `status` to `approved` if they want the file ready to apply.
