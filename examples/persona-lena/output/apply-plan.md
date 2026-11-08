# Apply plan · Studio Nordlicht

Setup file `cavion-workspace.json` · revision 1 · nothing is deleted, automations start paused.


## You first

- [ ] Install Cavion for Mac and approve it — Manage › Computers
- [ ] Invite: Designer (member) — Manage › People
- [ ] Invite: Freelance developer (member) — Manage › People
- [ ] Connect Gmail (founder) — My apps › Add app
- [ ] Connect Google Calendar — My apps › Add app
- [ ] Choose how the workspace is paid for — Manage › AI
- [ ] Look for your invoicing tool in Add app — Finance › Apps › Add app

## Batch 1 · one Approve

- [ ] Set up the assistant: instructions, tools, apps — CAVION_EDIT_AGENT and CAVION_SET_AGENT_TOOLS (Allow once)
- [ ] Gmail (founder): Read allowed, Create and change ask, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Google Calendar: Read allowed, Create and change ask, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Memory for assistant: 3 user profile — ask the agent to remember each line (memory tool)
- [ ] Task Monday brief · Mondays at 8:30 (starts paused) — setup proposal step schedule_task, made in the task's own chat; a person turns it on

## Batch 2 · one Approve

- [ ] Knowledge: Studio/Brand voice (Company knowledge) — an admin asks the assistant to save it
- [ ] Knowledge: Studio/Services and prices (Company knowledge) — an admin asks the assistant to save it
- [ ] Knowledge: Processes/Client onboarding (Company knowledge) — an admin asks the assistant to save it

## Batch 3 · one Approve

- [ ] Create Space Clients (Open) — setup proposal step create_space (assistant), then Space › Settings for agent access
- [ ] Project Café website in Clients — CREATE_PROJECT (direct, with Undo)
- [ ] Project Bike shop website in Clients — CREATE_PROJECT (direct, with Undo)
- [ ] Project Physio practice website in Clients — CREATE_PROJECT (direct, with Undo)

## Batch 4 · one Approve

- [ ] Project Yoga studio website in Clients — CREATE_PROJECT (direct, with Undo)
- [ ] Add designer to Clients — ADD_SPACE_MEMBER (Allow once)
- [ ] Add developer to Clients — ADD_SPACE_MEMBER (Allow once)

## You, before batch 5

- [ ] Connect Notion (studio) — Space Clients › Apps › Add app
- [ ] Connect Slack (studio) — Space Clients › Apps › Add app
- [ ] Connect Figma — Space Clients › Apps › Add app

## Batch 5 · one Approve

- [ ] Set up the Clients manager: instructions, tools, apps — CAVION_EDIT_AGENT and CAVION_SET_AGENT_TOOLS (Allow once)
- [ ] Create specialist Launch QA — setup proposal step create_specialist
- [ ] Notion (studio): Read allowed, Create and change allowed, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Slack (studio): Read allowed, Create and change ask, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Figma: Read allowed, Create and change off, Send off — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Knowledge: Templates/Weekly status update (Space knowledge) — ask the agent to save it

## You, before batch 6

- [ ] Add the list of live client sites — Clients › Context

## Batch 6 · one Approve

- [ ] Knowledge: Processes/Website launch checklist (Space knowledge) — ask the agent to save it
- [ ] Skill launch-qa (saved as Knowledge until skill import exists) — save SKILL.md as a Knowledge doc and point the agent's instructions to it
- [ ] Memory for clients-manager: 3 agent notes — ask the agent to remember each line (memory tool)
- [ ] Task Friday client status drafts · Fridays at 14:00 (starts paused) — setup proposal step schedule_task, made in the task's own chat; a person turns it on
- [ ] Task Monday site health check · Mondays at 7:00 (starts paused) — setup proposal step schedule_task, made in the task's own chat; a person turns it on
- [ ] Check New call notes to tasks · every 30 min (starts off) — ask the agent in that chat to propose the check (CAVION_PROPOSE_CHECK); Cavion tests it once

## Batch 7 · one Approve

- [ ] Create Space Finance (Members only) — setup proposal step create_space (assistant), then Space › Settings for agent access

## You, before batch 8

- [ ] Connect Toggl Track — Space Finance › Apps › Add app
- [ ] Connect Gmail (billing inbox) — Space Finance › Apps › Add app

## Batch 8 · one Approve

- [ ] Set up the Finance manager: instructions, tools, apps — CAVION_EDIT_AGENT and CAVION_SET_AGENT_TOOLS (Allow once)
- [ ] Toggl Track: Read allowed, Create and change off, Send off — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Gmail (billing inbox): Read allowed, Create and change ask, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Knowledge: Processes/Invoicing (Space knowledge) — ask the agent to save it
- [ ] Task Invoice lines and reminders · Weekdays at 9:00, acts only on the first working day (starts paused) — setup proposal step schedule_task, made in the task's own chat; a person turns it on

## Batch 9 · one Approve

- [ ] Create Space New business (Open) — setup proposal step create_space (assistant), then Space › Settings for agent access
- [ ] Add designer to New business — ADD_SPACE_MEMBER (Allow once)

## You, before batch 10

- [ ] Connect Gmail (contact inbox) — Space New business › Apps › Add app
- [ ] Confirm the studio has a shared contact inbox — New business › Apps

## Batch 10 · one Approve

- [ ] Set up the New business manager: instructions, tools, apps — CAVION_EDIT_AGENT and CAVION_SET_AGENT_TOOLS (Allow once)
- [ ] Create specialist Proposal writer — setup proposal step create_specialist
- [ ] Gmail (contact inbox): Read allowed, Create and change ask, Send ask — CAVION_SET_APP_PERMISSION (Allow once)
- [ ] Knowledge: Templates/Proposal structure (Space knowledge) — ask the agent to save it
- [ ] Knowledge: Templates/Inquiry replies (Space knowledge) — ask the agent to save it

## Batch 11 · one Approve

- [ ] Knowledge: Marketing/LinkedIn ideas (Space knowledge) — ask the agent to save it
- [ ] Skill proposal-from-call-notes (saved as Knowledge until skill import exists) — save SKILL.md as a Knowledge doc and point the agent's instructions to it
- [ ] Task Friday LinkedIn drafts · Fridays at 15:30 (starts paused) — setup proposal step schedule_task, made in the task's own chat; a person turns it on
- [ ] Check New website inquiries · every 15 min (starts off) — ask the agent in that chat to propose the check (CAVION_PROPOSE_CHECK); Cavion tests it once

## Paste into your Cavion assistant

```
Please set this up (part 1 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Set up the assistant: instructions, tools, apps
   Name: Assistant
   Apps: Gmail (founder), Google Calendar
   Instructions:
   You work for the founder of a three-person brand and web studio. Keep answers short. Write German to clients and English internally.
   
   Every Monday prepare the week: calls that need preparation, deadlines, open threads waiting on a reply, and three suggested priorities. During the week help with mail and the calendar: draft replies, find slots, summarise threads. Never send a mail or accept an invitation without asking first.
   
   Follow the Brand voice in Company knowledge for anything a client reads.
2. Gmail (founder): Read allowed, Create and change ask, Send ask
3. Google Calendar: Read allowed, Create and change ask, Send ask
4. Memory for assistant: 3 user profile
   - Founder and creative director of a three-person brand and web studio.
   - Writes German to clients and English internally; prefers short answers.
   - Plans the week on Monday at 9:00; client status mails go out on Friday afternoon.
5. Task Monday brief · Mondays at 8:30 (starts paused)
   When: Mondays at 8:30 (Europe/Berlin)
   Apps: Google Calendar (read allowed), Gmail (founder) (read allowed)
   Instruction: Read this week's calendar and the last week's unanswered mail. Write a short brief: calls that need preparation (with one line of context each), deadlines, threads waiting on a reply, and three suggested priorities for the week. Keep it under 200 words.
```

```
Please set this up (part 2 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Knowledge: Studio/Brand voice (Company knowledge)
   # Brand voice
   
   - Warm, clear, concrete. Short sentences.
   - No buzzwords: innovative, leading, solutions, synergy.
   - German for clients unless they write in English; English internally.
   - Say what we did and what it changed, with one number when there is one.
   - Sign client mails as the studio.
2. Knowledge: Studio/Services and prices (Company knowledge)
   # Services and prices
   
   - Day rate: 850 EUR net.
   - Typical website project: 6–10k EUR, split into design and build.
   - Always offer a maintenance retainer after launch.
   
   Check with the founder before quoting anything outside these ranges.
3. Knowledge: Processes/Client onboarding (Company knowledge)
   # Client onboarding
   
   1. Kick-off call
   2. Shared Notion page
   3. Slack Connect channel
   4. Collect logo, photos and texts
   5. Time-tracking project
```

```
Please set this up (part 3 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Create Space Clients (Open)
   Purpose: Client website projects from kick-off to launch: weekly status, tasks from calls, design and build hand-offs, launch QA and site health.
   Agents from other Spaces: Can work with this Space
2. Project Café website in Clients
3. Project Bike shop website in Clients
4. Project Physio practice website in Clients
```

```
Please set this up (part 4 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Project Yoga studio website in Clients
2. Add designer to Clients
3. Add developer to Clients
```

```
Please set this up (part 5 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Set up the Clients manager: instructions, tools, apps
   Name: Clients
   Apps: Notion (studio), Slack (studio), Figma
   Instructions:
   You run the studio's client projects. Each client has a Project in this Space.
   
   After a call, when notes are posted or added to Notion, create tasks in Notion with an owner (founder, designer or developer) and a due date, then post the list in the chat.
   
   On Fridays draft one status update per active project from the week's Notion tasks, call notes and Slack threads. Use the Weekly status update template and the Brand voice; German, at most 120 words; done, next, what we need from the client. Post drafts in the chat; never send them.
   
   Ask Launch QA for launch checks and site problems.
2. Create specialist Launch QA
   Name: Launch QA
   Apps: none
   Instructions:
   You check client websites before launch and every Monday. Follow the launch QA skill and the Website launch checklist: speed scores above 90, German alt texts, broken links, meta titles and descriptions, favicon, 404 page, redirects from old URLs, cookie banner, Search Console.
   
   For launch checks post what needs fixing, most important first, and a short client summary as a draft. For the Monday health check of all live sites (links, SSL expiry, speed) stay quiet when everything is fine and post only problems.
   
   Use the browser to look at sites; never submit forms or change a site.
3. Notion (studio): Read allowed, Create and change allowed, Send ask
4. Slack (studio): Read allowed, Create and change ask, Send ask
5. Figma: Read allowed, Create and change off, Send off
6. Knowledge: Templates/Weekly status update (Space knowledge)
   # Weekly status update
   
   Hallo {Name},
   
   kurzes Update zu {Projekt}:
   - Erledigt:
   - Als Nächstes:
   - Wir brauchen von euch:
   
   Viele Grüße
   Studio Nordlicht
   
   At most 120 words. Add the staging link when there is one.
```

```
Please set this up (part 6 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Knowledge: Processes/Website launch checklist (Space knowledge)
   # Website launch checklist
   
   - Speed scores above 90
   - Alt texts in German
   - 404 page
   - Favicon
   - Meta titles and descriptions
   - Redirects from old URLs
   - Cookie banner
   - Search Console set up
2. Skill launch-qa (saved as Knowledge until skill import exists)
   Save this as a Knowledge document named after the skill and follow it:
   ---
   name: launch-qa
   description: Check a client website before launch against the studio's checklist and write the fix list and a client summary. Use before every launch and for site problems.
   ---
   
   # Launch QA
   
   1. Open the staging or live address in the browser.
   2. Run a speed test for mobile and desktop; note scores below 90.
   3. Check every page for missing or English alt texts, broken links, missing meta titles and descriptions.
   4. Check favicon, 404 page, cookie banner and redirects from the old site.
   5. Check Search Console access.
   6. Post the fixes, most important first, with the page for each.
   7. Draft a five-line summary for the client in German.
3. Memory for clients-manager: 3 agent notes
   - The team: founder (sales, client contact), designer (Figma, icons), freelance developer (Webflow builds, forms).
   - Sites are designed in Figma and built in Webflow.
   - Each client has one Project in this Space; status drafts are per Project.
4. Task Friday client status drafts · Fridays at 14:00 (starts paused)
   When: Fridays at 14:00 (Europe/Berlin)
   Apps: Notion (studio) (read allowed), Slack (studio) (read allowed)
   Instruction: For each active client Project, read this week's Notion tasks and call notes and the project's Slack threads. Draft one status update per client with the Weekly status update template and the Brand voice: German, at most 120 words, done / next / what we need. Post all drafts here, one message per client. Do not send anything. If a project had no activity, say so in one line.
5. Task Monday site health check · Mondays at 7:00 (starts paused)
   When: Mondays at 7:00 (Europe/Berlin)
   Apps: none
   Instruction: Check every live client site listed in the Clients Space for broken links, SSL certificates expiring within 30 days, and mobile speed scores below 80. Post only problems, one line each with the site and what to fix. If everything is fine, end without a message.
6. Check New call notes to tasks · every 30 min (starts off)
   App: Notion (studio), every 30 minutes
   Looks at: new pages in the call notes database
   Instruction: For each new call note, create Notion tasks with owner and due date and post the list in the client's Project.
```

```
Please set this up (part 7 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Create Space Finance (Members only)
   Purpose: Monthly invoice lines from time tracking, overdue invoices and reminders. Money matters stay with the founder.
   Agents from other Spaces: Members only
```

```
Please set this up (part 8 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Set up the Finance manager: instructions, tools, apps
   Name: Finance
   Apps: Toggl Track, Gmail (billing inbox)
   Instructions:
   You prepare the studio's invoicing. On the first working day of the month read last month's hours from Toggl Track and make one invoice line per client project at the day rate in Services and prices. Flag entries without a project. Then list invoices unpaid for more than 14 days and draft a polite German reminder for each in the billing inbox. Post the lines as a table the founder can paste into the invoicing tool. You never send mails, book invoices or move money.
2. Toggl Track: Read allowed, Create and change off, Send off
3. Gmail (billing inbox): Read allowed, Create and change ask, Send ask
4. Knowledge: Processes/Invoicing (Space knowledge)
   # Invoicing
   
   - First working day of the month.
   - Hours from the time-tracking export, one line per client project.
   - Day rate from Services and prices.
   - Reminders after 14 days, polite, in German.
   - The founder books and sends invoices.
5. Task Invoice lines and reminders · Weekdays at 9:00, acts only on the first working day (starts paused)
   When: Weekdays at 9:00, acts only on the first working day (Europe/Berlin)
   Apps: Toggl Track (read allowed), Gmail (billing inbox) (read allowed)
   Instruction: Act only on the first working day of the month; on any other day end without a message. Then: read last month's hours from Toggl Track, group them per client project, and make invoice lines at the day rate from Services and prices. Flag entries without a project. List invoices unpaid for more than 14 days and draft a polite German reminder for each in the billing inbox. Post the invoice lines as a table and the list of reminder drafts here.
```

```
Please set this up (part 9 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Create Space New business (Open)
   Purpose: Website inquiries, discovery calls, proposals, case studies and LinkedIn posts.
   Agents from other Spaces: Can work with this Space
2. Add designer to New business
```

```
Please set this up (part 10 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Set up the New business manager: instructions, tools, apps
   Name: New business
   Apps: Gmail (contact inbox), Notion (studio)
   Instructions:
   You look after new business. For each new project inquiry in the contact inbox, draft a reply following Inquiry replies (thank them, two lines on how we work, the booking link) and post a one-line summary in the chat. Ignore newsletters and tool mails.
   
   On Fridays draft two LinkedIn posts from launches and case studies of the past two weeks, each with three alternative hooks, in the Brand voice. Ask the Proposal writer for proposals. Never send or post anything yourself.
2. Create specialist Proposal writer
   Name: Proposal writer
   Apps: Notion (studio)
   Instructions:
   You turn discovery-call notes into proposals. Follow the proposal skill and the Proposal structure: goals, scope, timeline, price, next steps. Prices come from Services and prices; split design and build; always offer the maintenance retainer. Write German unless asked; add an English scope section when the client has an English-speaking co-founder or asks for it. Deliver a Word document for review. Ask one question when budget or deadline is missing instead of guessing.
3. Gmail (contact inbox): Read allowed, Create and change ask, Send ask
4. Knowledge: Templates/Proposal structure (Space knowledge)
   # Proposal structure
   
   1. Goals — what the client wants to achieve
   2. Scope — pages, features, design and build
   3. Timeline — phases and launch date
   4. Price — day rate, design and build split, maintenance retainer
   5. Next steps — call, signature, kick-off
5. Knowledge: Templates/Inquiry replies (Space knowledge)
   # Inquiry replies
   
   - Thank them and repeat what they asked for in one line.
   - Two lines on how we work: discovery call, proposal, design, build, launch.
   - Booking link for a 30-minute call: <add your booking link>.
   - German unless they wrote in English. Sign as the studio.
```

```
Please set this up (part 11 of 11 of my Dayprint file onb-2026-11-07-studio-nordlicht). Propose it as one setup where you can, and ask me before each change:

1. Knowledge: Marketing/LinkedIn ideas (Space knowledge)
   # LinkedIn ideas
   
   - Launch stories: problem, what we built, one result
   - Before and after of a redesign
   - How we price websites
2. Skill proposal-from-call-notes (saved as Knowledge until skill import exists)
   Save this as a Knowledge document named after the skill and follow it:
   ---
   name: proposal-from-call-notes
   description: Turn discovery-call notes into a studio proposal (goals, scope, timeline, price, next steps). Use for every new website or brand project inquiry after a call.
   ---
   
   # Proposal from call notes
   
   1. Read the notes. If budget, deadline or page count is missing, ask one question.
   2. Goals: two or three sentences in the client's words.
   3. Scope: pages and features; split design and build.
   4. Timeline: phases with weeks; launch date.
   5. Price: days × day rate from Services and prices, design and build separately, then the maintenance retainer as an option.
   6. Next steps: call to discuss, signature, kick-off date.
   7. German by default; add an English scope section when asked.
   8. Deliver a Word document and a three-line summary in the chat.
3. Task Friday LinkedIn drafts · Fridays at 15:30 (starts paused)
   When: Fridays at 15:30 (Europe/Berlin)
   Apps: Notion (studio) (read allowed)
   Instruction: Look at launches and case studies from the past two weeks in Notion and in this Space. Draft two LinkedIn posts (at most 120 words each): the client's problem, what we built, one result. Give three alternative opening hooks for each. Use the Brand voice and LinkedIn ideas. Post them here; never post to LinkedIn.
4. Check New website inquiries · every 15 min (starts off)
   App: Gmail (contact inbox), every 15 minutes
   Looks at: new e-mails to the studio's contact inbox
   Instruction: If the mail is a new project inquiry, draft a reply following Inquiry replies and post a one-line summary (what they want, budget if stated). Skip newsletters, invoices and tool notifications.
```
