# Estimating time saved

`hours per week = per_month ÷ 4.33 × minutes_each ÷ 60 × share`

- **per_month** — counted occurrences ÷ the months the data actually covers (`stats.json › data_span.months`). A 12-month window over 3 months of history is 3 months. For calendar blocks use the repeat rule.
- **minutes_each** — in order of preference: the length of a calendar block for it; agent session length (first to last message); the person's own estimate in memory or prompts; a typical value below. Say which in `saving.note`.
- **share** — how much of the work the agent takes over once set up, as a low–high range. The person still reviews, decides and approves.

| Kind of work | Share low–high | Why |
|---|---|---|
| Drafting from notes in a fixed structure (status mails, proposals, case studies) | 0.5–0.7 | first draft and formatting go away; review stays |
| Collecting and reporting on a schedule (weekly summaries, KPI digests) | 0.6–0.85 | runs unattended; reading the result stays |
| Moving data between tools (timesheet → invoice lines, notes → tasks) | 0.6–0.8 | copy work goes; checking amounts stays |
| Checks and QA against a checklist (site launch, document review) | 0.4–0.6 | the run is automatic; fixes need judgement |
| Triage of incoming items (leads, support mail) | 0.3–0.5 | sorting and first replies; real answers stay |
| Follow-ups and reminders | 0.6–0.8 | tracking and drafting; the decision to send stays |
| Meetings themselves | 0 | count only preparation and follow-up |
| Creative work, strategy, relationships | 0–0.2 | do not claim these |

Typical minutes when nothing better exists: status e-mail 15–25, proposal 90–180, meeting notes to tasks 10–20, invoice run 60–120 a month, reply to an inquiry 10–15, social post 30–45, launch QA 60–120.

Count each piece of work in one workflow only: if short approvals are a workflow of their own, do not count the release approvals among them again.

Round to one decimal. Show ranges, never a single big number. If evidence covers fewer than three occurrences, mark the workflow low confidence and use the low end.
