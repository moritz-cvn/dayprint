# Mapping patterns

Recurring kinds of work and the Cavion blocks that fit them, with the do-it-yourself equivalent for the report. Use them as starting points; the evidence decides.

| Kind of work | Cavion | Own tools, without Cavion |
|---|---|---|
| **Recurring update to a client or team** (weekly status, project recap) | Space manager or specialist in the client Space; weekly scheduled task in the Space chat that reads the notes, tasks and mails of the week and drafts one update per active project; drafts wait for review (Send: Ask each time); Knowledge: update template, voice guide | A template + a saved prompt (custom GPT / Claude project with the template); a weekly calendar reminder; paste notes, review, send |
| **Document from notes in a fixed structure** (proposal, offer, brief, case study) | Specialist ("Proposal writer") with a skill holding the structure and a Knowledge price list; started from the chat after a call; output as a document | Claude project or custom GPT with the template and price list as files; one prompt per call; a document template |
| **Meeting notes → tasks** | Assistant or Space manager; task board app (Notion, Linear, Asana) with Create and change Ask each time; a check on new meeting notes, or the person drops notes in the chat | Prompt that outputs a task table; the task tool's e-mail-in or import; Zapier/Make from a notes folder |
| **Timesheet → invoice** | Members only Space "Finance"; weekly task with first-working-day rule reading the time-tracking app and the invoicing app (Read), drafting invoice lines and reminder mails for overdue ones; Send off or Ask | The existing script + a monthly calendar reminder; the invoicing tool's own reminder rules; spreadsheet pivot |
| **Overdue follow-ups** (invoices, replies, approvals) | Weekly task that lists what is waiting and drafts reminders; Knowledge: tone for reminders | Invoicing tool's dunning feature; mail "snooze until" or follow-up reminders |
| **Inbound triage** (inquiries, support, shared inbox) | Check on the shared inbox (every 10–30 min) in a Space; the manager sorts, drafts replies with booking link, flags hot leads in the Space chat; Send: Ask each time | Mail filters and labels; canned replies/templates; booking link in the auto-reply; form tool notifications |
| **Social and content** (LinkedIn posts, newsletters) | Specialist in a "Marketing" Space; weekly task proposing two drafts from recent wins (case studies, launches); Knowledge: voice, idea list | Idea list document; weekly reminder; saved prompt with voice guide; scheduling tool |
| **Checklist QA** (website launch, document review, release) | Specialist with a skill holding the checklist; runs on the Mac (browser, files); a task before each launch or on request; summary for the client as a draft | Checklist template; Lighthouse / link checker / validators; a script run weekly by cron or Shortcuts |
| **Monitoring** (sites up, broken links, SSL expiry, reviews) | Weekly or interval task (every 240 min in working hours) on a cloud computer if it must run while the Mac is off; reports only when something is wrong (notification: urgent) | Uptime monitor (free tiers exist); cron job; the script plus a calendar reminder |
| **Weekly planning** | Assistant; weekly task Monday morning reading calendar, task board and open threads; proposes the week's top three and blocks focus time (calendar write: Ask each time) | Calendar template block; a planning note template; a saved prompt |
| **Research and briefings** (before calls, competitor watch) | Assistant; check on the calendar for new external meetings → short brief on the company from the web; or a weekly digest | Saved prompt; browser bookmarks folder; news alerts |
| **Knowledge re-explained in every chat** (brand voice, prices, processes) | Company or Space knowledge documents; memory seeds for one-line rules; agents' instructions point to them | Custom instructions / project files in the AI tool; one shared "about us" document |
| **Hand-offs between people** (designer → developer, sales → delivery) | One Space per stream with members and a manager; Projects per client; @mentions in the Space chat; manager summarises status | Shared channel per project; a hand-off checklist template |

## Choosing scheduled task vs check vs chat

- Time-based ("every Friday", "first of the month", "every morning") → scheduled task.
- Arrival-based ("when a new inquiry comes in", "when notes are added") → check.
- Judgement-heavy, irregular, needs the person in the loop (a proposal after a call) → the person starts it in the chat; a skill makes it consistent.

## Choosing where results land

- Personal work → the assistant's private chat; the person sees it in Inbox › Results.
- Team work → the Space chat (shared) or a Project in the Space, so everyone sees the same thing.
- Anything that leaves the workspace (mail to clients, invoices, posts) → a draft and an Allow once card, always.
