# Cavion, as it is

What a Cavion workspace has, the exact names people see, and what is live. Use only live features in the setup file and the report. State as of November 2026.

## Contents
- People and roles · Agents · Spaces and Projects · Inbox · Knowledge · Memory · Skills
- Scheduled tasks · Checks · Event triggers · Apps · Permissions · Computers · Funding · Talk
- Navigation · Limits · Not yet available

## People and roles
A workspace has one owner, admins and members. People join by invitation (Manage › People › Invite: name, e-mail, role). Admins manage people, Spaces, AI and keys, computers, apps across Spaces and websites, but never see anyone's private chats, My knowledge, personal apps or memory. Each person has a team profile (job title, responsibilities).

## Agents
- **Personal assistant** — one per person, automatic, private to its owner, on Home. Does personal work and can set things up for its person.
- **Space manager** — one per Space, automatic, named after the Space. Answers in the Space chat, coordinates specialists, can propose setups in its Space.
- **Specialist** — a focused agent inside a Space, created through an approved setup proposal. Can be @mentioned in a Space chat; can also work in further Spaces. Cannot create specialists, speak in Space chats unasked, manage scheduled tasks or learn skills; a fixed-schedule task may run as a specialist.
- Settings per agent: name, instructions (up to 4,000 characters), apps (an explicit list; empty means no apps), tools (presets Assistant, Document worker, Automation worker), model and reasoning effort for chats and automations, runs on (which computer), Learned (memory, skills, "Remember notes" Off/Read only/On, "Learn skills from chats"), and for specialists Autonomous sending (off by default, a person's choice).
- Tools: search and read Knowledge, update Knowledge, use assigned apps, ask other agents, create specialists, speak in Space chats, search past conversations, remember facts, use and learn skills, keep a checklist, ask you a question, scheduled tasks, open, create and edit files (docx, xlsx, pptx, pdf), look at images, run code, search the web, browse websites (the browser starts signed out; the person logs in themselves in the live view when needed).

## Spaces and Projects
- A Space has a name, purpose, colour, owner, members (added by hand), a manager agent and specialists. Tabs: Overview, Work, Context (Space knowledge), People, Agents, Apps, Settings.
- Space chats are shared with all members; private chats with Space agents are only yours.
- **Agents from other Spaces** (Space › Settings): *Can work with this Space* (Open, default) — any member's agent may ask this Space's manager; or *Members only* — only agents working for members, answers stay with members.
- **Projects** group chats inside a Space (one per client, campaign, stream). Private projects live under My work and can be moved into a Space later.

## Inbox
Unread, All, Needs you (approvals and proposals), Results, Problems, Mentions. Scheduled-task results and approvals land here.

## Knowledge
Markdown documents in folders, in three places: **My knowledge** (you and your assistant), **Space knowledge** (Space › Context; members and Space agents), **Company knowledge** (under Team; everyone). People edit directly; agents save when asked (Company knowledge only when an admin asked). Links between documents survive renames.

## Memory
Each agent keeps short notes per audience (personal, private Space chat, shared Space): *agent notes* (what it learned about the work, up to 2,200 characters) and a *user profile* (about the person or team, up to 1,375 characters), as one-sentence entries. People can correct or remove entries on the agent's Learned page. Longer or shared material belongs in Knowledge; procedures in skills.

## Skills
Packages in the open Agent Skills layout: a `SKILL.md` with `name` and `description`, plus optional files. Scoped personal, Space or company. Cavion agents learn skills from chats ("Learned: …" in the chat) and a person can share a skill to another agent. There is no upload of a ready-made skill yet, so the setup file also stores each skill as a Knowledge document the agent is told to follow.

## Scheduled tasks
Made in a chat; results come back to that chat (private or a shared Space chat). Fields: title, instruction, timing, preparation (read only, or may create documents), the task's apps with their own Read / Create and change / Send settings, Knowledge documents to use, notification (meaningful or urgent).
Timing: **once** (date, time); **weekly** (days, up to six times a day, at least 30 minutes apart); **every 30, 60, 120 or 240 minutes** inside working hours. No monthly rule: use a weekly task that only acts on the right day. A person always turns a task on. Task runs may read the agent's other apps whose Read is Allowed (read wide, act narrow).

## Checks
For "when something new arrives": Cavion looks at an app every 5, 10, 15, 30 or 60 minutes (default 10) and starts the agent only for new items; quiet checks cost nothing. The agent proposes a check in the chat, Cavion tests it once and shows a card; in a shared Space chat the Space owner or an admin turns it on. Works with app connections and MCP servers.

## Event triggers
Instant triggers from apps (webhooks) are **not available yet**. Use a check.

## Apps
- Connected through Composio (about 1,600 apps; slugs like `gmail`, `googlecalendar`, `googledrive`, `googledocs`, `googlesheets`, `outlook`, `notion`, `slack`, `hubspot`, `pipedrive`, `linear`, `jira`, `asana`, `trello`, `clickup`, `github`, `figma`, `calendly`, `stripe`, `airtable`, `dropbox`, `zoom`, `webflow`, `shopify`, `mailchimp`). Only a person completes a connection (sign-in in Composio's hosted page).
- **My apps** — personal, one person, given to their assistant automatically. **Space apps** — shared accounts in Space › Apps, added by the Space owner, usable by that Space's agents; an admin can add a Space app to more Spaces (Manage › Apps). Personal apps cannot be given to Space agents. One connection per app per place.
- **MCP servers** — Apps › MCP › Add MCP server by public HTTPS address; personal or Space.
- Each app has three permission groups: **Read**, **Create and change**, **Send, delete and share** — each *Allowed*, *Ask each time* or *Off*. Send, delete and share is never silently allowed in chats; automatic sending needs both the task's Send Allowed and the specialist's Autonomous sending.

## Permissions and approvals
An agent acts as the person who started the work, never with more rights. Approvals appear as cards: **Allow once** / **Don't allow** (sends, deletes and shares expire after 15 minutes, setup changes after 24 hours); app cards may also offer *Always allow* except for sending. Some steps are always the person's: connecting apps and subscriptions, approving computers, inviting people, deleting Spaces or agents, switching on Autonomous sending. Admins choose which websites agents may use (Manage › Websites).

## Setup proposals
A personal assistant (in its own chat) or a Space manager (in its Space) can propose a setup: up to six steps — create a Space (one, assistant only), create a specialist, schedule a task, connect an app, share a skill. Approve runs them as the person; Undo removes what was made. Connecting apps and turning on tasks are handed to the person. Changing an existing agent, app permissions, Knowledge and checks are separate approval cards.

## Computers
- **Cavion for Mac** — runs the agents on the person's Mac: files (PDF, scans, Office), making documents, the agent's browser in a native view (watch, take over, log in), the microphone for Talk. Several Macs: one runs the agents, others stand by. The Mac must be awake with the app running. Download and approve in Manage › Computers.
- **Cloud computer** — one per person, runs agents when the Mac is off; wakes for due work, sleeps after 15 idle minutes, optional Always on. Monthly cost guard per workspace (default 10 USD per cloud computer). Manage › Computers › Connect a cloud computer.

## Funding
Manage › AI › **Run this workspace with**: **Subscriptions** (each person's own ChatGPT plan pays for their work, on their Mac or cloud computer) or **API keys** (workspace OpenAI or Anthropic keys pay for everyone; up to five per provider, each with an optional monthly budget; allowed models list). Agents never connect subscriptions or spend money.

## Talk
Voice conversations with your agent on web, Mac and iPhone. An admin switches it on in Manage › AI › Talk; needs a workspace OpenAI key.

## Navigation
Sidebar: Home, My work, My knowledge, My apps, Inbox, Spaces (+), Team, Manage (admins), Account.
Manage: People, Spaces, AI (Run this workspace with · Keys · Models · Talk), Computers, Apps, Websites, Workspace.
Account: profile, Your computers (connect a subscription), Workspace, Notifications, Privacy.
Space: Overview · Work · Context · People · Agents · Apps · Settings. Agent: Overview · Settings (name, instructions, model, runs on, Apps › Select apps, tools, Learned, Spaces, Autonomous sending).
Apps: My apps (or Space › Apps) › Add app or MCP › app › Manage (Read · Create and change · Send, delete and share).

## Limits
Agent name 120, instructions 4,000 characters; task title 120, instruction 2,000 in a proposal; apps per agent or task 50; Knowledge sources per task 50; up to 6 steps and one new Space per proposal; up to 3 specialists per request; files 10 per message, 50 MB each.

## Not yet available — do not promise
Instant event triggers from apps · monthly schedules · uploading a ready-made skill · saved sign-ins for the agent's browser · the Cavion MCP setup tools (the setup file is ready for them; until then the person pastes each batch into their assistant).
