# Sources

What `inventory.py` looks for, where it lives, and what is taken from it. Ids are the keys used in `consent.json`.

| Id | Where | Taken | Strong signals |
|---|---|---|---|
| `claude-code-transcripts` | `~/.claude/projects/<project>/*.jsonl` | the person's messages, session length, project folder name, tool and MCP names | repeated asks per project, MCP servers already in use (Gmail, Notion …) |
| `claude-code-memory` | `~/.claude/projects/*/memory/*.md`, `~/.claude/CLAUDE.md` | text, frontmatter dropped, 2,000 characters per file | role, tools, standing rules, processes in their own words |
| `claude-code-history` | `~/.claude/history.jsonl` | prompts with date and project | rhythm, repeats |
| `codex-sessions` | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, `~/.codex/archived_sessions` | the person's messages, program and script names of commands run | scripts run on a rhythm |
| `codex-history` | `~/.codex/history.jsonl` | prompts with date | repeats |
| `codex-memory` | `~/.codex/AGENTS.md`, `~/.codex/memories/` | text | standing rules |
| `chatgpt-export` | export zip or folder in Downloads, Desktop, Documents (`conversations*.json`, `chat.html`, `user.json`) | title, date, the person's messages (first 280 characters, then up to four follow-ups of 160), custom-GPT flag | the biggest source of repeated drafting work |
| `claude-export` | Claude.ai export (`conversations.json`, `projects.json`, `memories.json`, `users.json`) | titles, the person's messages, project names, descriptions and instructions, memory text | projects = workflows the person already packaged |
| `shell-history` | `~/.zsh_history`, `~/.bash_history`, fish history | program names, and script names after `python`/`node` | `python3 invoice_hours.py` on the 1st = a monthly workflow |
| `calendar-files` | `.ics` exports in Downloads, Desktop, Documents | title, start, duration, repeat rule, attendee count, external attendees, video tool | recurring blocks are workflows; meeting hours |
| `documents` | Documents, Desktop, Downloads, Notes, Obsidian, iCloud Drive (5 levels, hidden folders skipped, 400 files) | folder, name, type, date; text/Markdown first 500 characters; CSV header | templates, checklists, processes, brand guides |
| `mac-activity` | `pmset -g log` (macOS, this Mac's own user) | display on and off, sleep and wake times | real start, end and breaks of the working day |
| `git-activity` | local repositories under Documents, Desktop, Developer, code, Projects | commit times of the person's own commits (filtered by their git e-mail, which is never written) | when work lands, weekend and night work |
| `screen-time` | `~/Library/Application Support/Knowledge/knowledgeC.db` | minutes per app in front, by app name; never window titles | where the day goes; needs Full Disk Access, skipped without it |
| `installed-apps` | `/Applications`, `~/Applications` | app names | tools in use |
| `connector:<name>` | your own MCP servers or app connections | see [../subskills/1-discover.md](../subskills/1-discover.md) | calendar rhythm, mail volume by kind, docs that are processes |

Not read on purpose: browser history, cookies and saved passwords, Messages, Mail.app's local store, Photos, Contacts, Keychain, Cursor and other editors' databases, any file the secret rules block. If the person wants another tool included (Cursor, Gemini CLI, Obsidian vault elsewhere), point `--extra` at an export or folder; Markdown and text files there are handled like documents.

## Exports

- **ChatGPT:** Settings › Data controls › Export data. A zip arrives by e-mail.
- **Claude.ai:** Settings › Privacy › Export data. A zip arrives by e-mail.
- **Google Calendar:** Settings › Import and export › Export (a zip of `.ics` files). **Apple Calendar:** File › Export.

Zips are read in place; nothing is unpacked to disk.
