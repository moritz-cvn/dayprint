# 1 · Discover

Goal: let the person choose how deep to look, confirm the sources, then read only those into a redacted digest.

## 1. Depth (the first question)

Before anything is listed, ask how deep to go. Three options, in one short question (in Claude Code use the question tool):

- **Quick** — only what the AI tools already remember: Claude and Codex memory and instructions, Claude.ai projects and memory, and the ChatGPT memory if the person pastes it (ChatGPT › Settings › Personalization › Memory › Manage, select all, copy). A few minutes; a first impression.
- **Standard** (recommended) — plus chat history from ChatGPT, Claude.ai, Claude Code and Codex, and the calendar. This is where repeated work shows.
- **Deep** — everything that can be found: documents and notes, terminal history, installed apps, Screen Time (which app is in front, by name; needs Full Disk Access for the terminal app), and every connected app (mail, Drive, Notion, Slack, CRM).

Standard and deep also include two timestamp-only sources for the working day: when the Mac's display is on (the power log) and the times of the person's own commits. They show the rhythm, never content.

Each source carries its level in the inventory. The chosen level preselects sources; the person can still remove any of them in the next step.

## 2. Inventory (metadata only)

Run `scripts/inventory.py --depth <level> --out <run>/inventory.json`. It lists sources with counts, sizes and dates and opens nothing: zip exports are recognised by their file list, secret paths are skipped and not even counted. Add `--extra <path>` for an export or folder the person points you to (a ChatGPT or Claude.ai export zip, a notes vault, an `.ics` file).

Then add what only you can see — your own connectors. Look at the tools available to you for mail, calendar, documents, notes, chat, CRM, tasks (for example Gmail, Google Calendar, Google Drive, Outlook, Notion, Slack, Linear, HubSpot MCP servers or app connections). Add one entry per connector to `inventory.json` with `"kind": "connector"`, `"status": "found"`, the tool name as label and what you would read (see [../references/sources.md](../references/sources.md)). Do not call them yet.

In a chat app without local files, the inventory is: uploaded files, your connectors, and your memory or past-chat tools. Ask for exports if none are there: ChatGPT (Settings › Data controls › Export data) and Claude.ai (Settings › Privacy › Export data) send a zip by e-mail; the person uploads it.

Connectors you add get `"depth": "deep"` (calendar connectors `"standard"`; your own memory or past-chat search `"quick"` for memory, `"standard"` for chat search) and `"preselected"` by the same rule.

### Full Disk Access (deep look only)

If the person chose **deep** and the inventory marks `screen-time` with `"access": "needs_full_disk_access"`, do not explain settings in chat and do not hand over a command. macOS has no prompt an agent can raise for Full Disk Access, so the skill brings the switch one click away instead. After `extract.py`, run:

`python3 <skill>/scripts/screen_time_access.py --run <run> --consent <run>/consent.json`

It shows a macOS dialog (what is read: app names and minutes, never the screen), opens System Settings at Full Disk Access, waits for **Continue**, then reads Screen Time in a new Terminal window and waits for `day.json`. The agent's own app never needs a restart. Tell the person in one line that a dialog is coming. Then act on the JSON it prints:

- `read`: go on; `day.json` now holds app time.
- `skipped`: go on without it; the report says app time was not read.
- `restart_needed`: the agent itself runs in Terminal. The run folder keeps everything; the person says "continue" after the restart.
- `failed`: go on without it and mention it in one line.

Never ask for Full Disk Access on a quick or standard look, and never outside macOS.

## 3. Confirm (one pause)

Show the preselected sources in one compact list: label, how much (files; the dates are when files changed, not how far back the content goes), and the one-line note of what is taken from it. Mention in one line what the next level would add. Ask the person to confirm or untick; in Claude Code use the question tool with multi-select, with the preselected ones first; elsewhere accept "ok", "all except …", or a list.

Also ask, in the same message, two optional things:
- a time window (default: the last 6 months),
- names to hide (clients, colleagues, family, their own company if they like) — they become `[name]` in the working files too. Without this, business names stay in the working files (never in the outputs, where you write roles instead).

Write the answer to `<run>/consent.json`:

```json
{"schema": "dayprint.consent/0.1", "depth": "standard", "since_days": 180,
 "sources": {"claude-code-transcripts": true, "chatgpt-export": true, "shell-history": false, "connector:google-calendar": true},
 "mask_names": ["Anna", "Kaffeebar Ost"]}
```

Sources not mentioned are false. Nothing outside the chosen level is read, even if found. If the person pasted their ChatGPT memory, save it as `digest/connector-pasted-memory.jsonl` (one `{"kind": "memory", "source": "chatgpt-memory", "text": ...}` line, redacted) and add `"connector:pasted-memory": true`.

## 4. Read

First the connectors, because only you can reach them. For each consented connector, read metadata-first and write `<run>/digest/connector-<name>.jsonl` (the source id with `:` replaced by `-`), one JSON object per line with `"kind"`, `"source"` and short redacted text. Good defaults:

- **Calendar:** the last 8 weeks and next 4: titles, start, duration, repeat rule, attendee count, whether attendees are external. Not descriptions.
- **Mail:** the last 30 days, metadata only: counts per label or folder, sender domains as categories (client, tool notification, newsletter, internal), recurring subjects. Bodies only if the person explicitly allowed them, and then the first lines of at most 20 threads.
- **Docs and notes (Drive, Notion, Confluence):** titles, folders, last edited, and the first lines of documents that look like templates, processes or checklists.
- **Chat (Slack, Teams):** channel names, message counts per channel per week, recurring bot posts. No message bodies by default.
- **Your own memory or past-chat search (chat apps):** search for recurring requests ("every week", "again", "template", "report", "follow up", "invoice", "summary") and record titles and dates.

Write names as roles and leave addresses out. Then run `python3 <skill>/scripts/validate.py report <run>/digest/connector-<name>.jsonl`; it flags any address or secret you missed — fix the file until it is clean.

Then run `scripts/extract.py --inventory <run>/inventory.json --consent <run>/consent.json --out-dir <run>`. It reads the local sources and writes:

- `digest/<source>.jsonl` — one redacted item per conversation, session, event or file: titles, first prompts, short follow-ups, tool and program names, durations. Assistant replies, tool output, command arguments and Office file bodies are never included.
- `stats.json` — counts that make good evidence: repeated requests (the strongest signal), keywords, weekday and hour rhythm, tools and MCP servers used, programs and script names, projects, apps mentioned, document kinds, recurring meetings and meeting hours. (Connector items are not in these counts; read them from their digest.)
- `read-log.json` — exactly what was read, per source, including your connector files. The report's privacy section comes from here.

## 5. Check

Read `read-log.json` and confirm `secret_files_opened` is 0 and only consented sources show `"read": true`. Then go to [2-analyse.md](2-analyse.md). Do not open raw files to "look closer" — if the digest is not enough for a question, ask the person or mark the finding low confidence.
