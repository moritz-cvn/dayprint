# 3 · Map to Cavion

Goal: design the smallest Cavion workspace that serves the workflows found in step 2. Read [../references/cavion-product.md](../references/cavion-product.md) first (what each building block is, what is live) and [../references/mapping-patterns.md](../references/mapping-patterns.md) (which block fits which kind of work).

## Design rules

0. **Fit their day and tempo first.** Time every scheduled task inside their measured day (`day.json`: after `typical.start`, on the weekdays they actually work, weekends included if they work then). Prefer the person's own action or an instant trigger over polling for anything someone waits on. Keep scripts and tools that already work and let agents build on their output instead of replacing them. Each new approval card is a decision the person has to make; for a fast person, prefer standing permissions for low-risk internal actions. Add a connection only when the evidence shows the app in use. Use what the tool does natively (auto-merge, filters, rules) before an agent or a polling check. Every agent's promise must be doable with its tools, apps and allowed websites; if not, narrow the promise. If checks or tasks run while the person works and the computer may sleep, say where they run.

    Read `working_model` (step 3). Never design anything that makes `must_not_slow` slower or touches `off_limits`. For a fast person, standing permissions (what agents may do without asking) and instant handling beat digests and fixed review slots; batching is only for work nothing waits on.

1. **Start from the workflows, not from features.** Every object you add serves at least one workflow or finding; put those ids in its `evidence`. If nothing needs it, leave it out.
2. **The personal assistant does personal work.** Inbox, calendar, personal follow-ups, the person's own drafts. It gets the person's own apps (My apps).
3. **A Space per area of shared work**, not per tool: "Clients", "Finance", "Marketing". One person working alone can still benefit from Spaces when areas have different apps, Knowledge and tasks. Two to four Spaces is typical for a small team; one is fine.
4. **Open or Members only.** Open (agents from other Spaces can work with it) is the default for collaborative areas. Members only for finance, HR, legal, or anything with client-confidential material.
5. **Specialists only for a distinct, repeated job** (they cannot create specialists, speak in Space chats on their own, manage scheduled tasks or learn skills; a fixed-schedule task may still run as a specialist) with its own instructions and apps (for example a "Proposal writer" or "Launch QA" agent). The Space manager handles general work in its Space. At most two or three specialists per Space to start.
6. **Apps where the account lives.** When the evidence does not say whether a mailbox or workspace is personal or shared, choose personal for the assistant and ask in the final review. A personal mailbox is a personal app; a shared inbox, the team's Notion, the invoicing account are Space apps. Personal apps cannot be given to Space agents.
7. **Permissions: read wide, act narrow.** Read Allowed where agents need context; Create and change Ask each time to start (Allowed only for low-risk internal tools like a task board); Send, delete and share always Ask each time (or Off).
8. **Knowledge for what agents must know every time:** brand voice, process checklists, price lists, templates, client overviews. Draft them from the person's own documents and memory (paraphrased, no personal data). Company knowledge for the whole team, Space knowledge for one area, My knowledge for the person.
9. **Memory seeds for short facts** an agent needs every run: one sentence each, within budget (agent notes 2,200 characters, user profile 1,375). Longer material is Knowledge; procedures are skills.
10. **Skills for procedures** the person repeats with the same steps (a proposal structure, a launch checklist run). Write a proper `SKILL.md` (name, description, steps). Today Cavion learns skills from chats, so the setup file also saves each skill as Knowledge (`fallback: "knowledge"`).
11. **Scheduled tasks for time-based work**, checks for "when something new arrives". Cavion timing is once, weekly (up to six times a day), or every 30/60/120/240 minutes inside working hours — there is no monthly rule: for monthly work use a weekly task on all weekdays (1–5) whose instruction says to act only on the first working day of the month and to end without a message otherwise. Checks look at an app every 5, 10, 15, 30 or 60 minutes and wake the agent only for new items. Instant event triggers are not available yet; if one would be ideal, add it to `event_automations` with `available: false` and a fallback check.
12. **Computers.** Recommend Cavion for Mac when work touches local files, the agent's browser, or the person uses the Mac all day. Recommend a cloud computer when tasks must run while the Mac sleeps (early-morning reports, checks overnight). Funding: Subscriptions (each person's own ChatGPT plan) or API keys (workspace keys with budgets); set `run_with: "undecided"` unless the evidence is clear, and explain the choice in a manual step.

## Agent cards — for any tool

Before the Cavion design, write one `agent_card` per workflow in `findings.json`. It describes the agent without naming Cavion, so a person can build it in ChatGPT or Claude projects, a custom GPT, n8n, Zapier or a script:

- `name` and a one-line `role`;
- `trigger`: `schedule` (with when), `new_item` (what arrives where) or `on_request`;
- `instructions`: the agent's instructions, ready to paste — what to read, what to do, what to deliver, when to stay quiet, what never to do;
- `inputs`, `tools` (app and access: read, draft or write), `knowledge` (documents it needs);
- `output` and `approval` — what a person checks before anything leaves.

The Cavion design then gives each card a home: which Space, which agent, which task or check. The report shows the cards, and `render_report.py` also writes them to `agent-cards.md` for people who build elsewhere.

## Check the design

Before writing the file, walk each workflow through the design: who starts it, which agent does it, which apps and Knowledge it uses, where the result lands, who approves anything that leaves the workspace. Fix gaps. Then make the design as small as it can be while every workflow still works.
