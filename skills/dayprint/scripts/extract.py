#!/usr/bin/env python3
"""Step 2 of discover: read ONLY the sources the user agreed to, and write a
redacted digest the model can analyse without ever seeing raw data.

  python3 extract.py --inventory inventory.json --consent consent.json --out-dir <run>/

consent.json:  {"sources": {"claude-code-transcripts": true, "shell-history": false, ...},
                "since_days": 180, "mask_names": ["Anna", "Kaffeebar Ost"]}

Writes:
  <run>/digest/<source>.jsonl   one redacted item per conversation / session / event / file
  <run>/stats.json              counts that make good evidence (repeats, tools, rhythm)
  <run>/read-log.json           exactly what was read, for the report's privacy section

What is never read: tool output, command arguments, assistant replies longer than
a short preview, attachments, Office file bodies, and anything is_secret_path() flags.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (GENERATOR, die, is_secret_path, now_iso, read_json, redact,  # noqa: E402
                    set_masked_names, to_dt, write_json)

PROMPT_PREVIEW = 280      # chars of a first message kept in the digest
FOLLOWUP_PREVIEW = 160    # chars of later messages
MAX_FOLLOWUPS = 4
DOC_PREVIEW = 500

STOP = set("""a an the and or but if then else of to in on at for with from by as is are was were be been it this that
these those i you we me my our your he she they them his her its not no yes do does did done can could should would
will shall may might must just please also so very more most some any all each every than too into out up down over
about again here there when where why how what which who whom whose also bitte und oder aber der die das ein eine
einen einem einer ist sind war waren mit von zu im in am an auf für fur aus bei nach vor über ueber unter wie was wer
wo warum ich du wir ihr sie es mein meine dein unser euer nicht kein keine ja nein auch noch nur schon mal dann den
dem des hier dort heute morgen kannst könntest koennen can't don't let's i'm it's let make write give help new""".split())

APP_HINTS = {
    # name fragment (lower) -> canonical tool name; used for tool/app mentions in text and program names
    "gmail": "Gmail", "google calendar": "Google Calendar", "gcal": "Google Calendar", "google drive": "Google Drive",
    "google docs": "Google Docs", "google sheets": "Google Sheets", "sheets": "Google Sheets", "outlook": "Outlook",
    "notion": "Notion", "slack": "Slack", "teams": "Microsoft Teams", "zoom": "Zoom", "hubspot": "HubSpot",
    "pipedrive": "Pipedrive", "salesforce": "Salesforce", "linear": "Linear", "jira": "Jira", "asana": "Asana",
    "trello": "Trello", "clickup": "ClickUp", "github": "GitHub", "gitlab": "GitLab", "figma": "Figma",
    "canva": "Canva", "webflow": "Webflow", "wordpress": "WordPress", "shopify": "Shopify", "stripe": "Stripe",
    "lexoffice": "Lexoffice", "sevdesk": "sevDesk", "datev": "DATEV", "quickbooks": "QuickBooks", "xero": "Xero",
    "toggl": "Toggl Track", "clockify": "Clockify", "harvest": "Harvest", "calendly": "Calendly", "airtable": "Airtable",
    "dropbox": "Dropbox", "onedrive": "OneDrive", "excel": "Excel", "word": "Word", "powerpoint": "PowerPoint",
    "linkedin": "LinkedIn", "instagram": "Instagram", "mailchimp": "Mailchimp", "brevo": "Brevo", "typeform": "Typeform",
    "miro": "Miro", "loom": "Loom", "whatsapp": "WhatsApp", "telegram": "Telegram", "obsidian": "Obsidian",
    "vercel": "Vercel", "netlify": "Netlify", "supabase": "Supabase", "docusign": "DocuSign", "pandadoc": "PandaDoc",
}


# ------------------------------------------------------------------ helpers
class Run:
    def __init__(self, out: Path, since: datetime | None):
        self.out = out
        self.since = since
        self.digest_dir = out / "digest"
        self.digest_dir.mkdir(parents=True, exist_ok=True)   # connector files written by the agent stay
        self.log: list[dict] = []
        self.prompts: list[tuple[str, datetime | None, str]] = []   # (redacted text, time, source)
        self.tools = Counter()
        self.mcp = Counter()
        self.programs = Counter()
        self.projects = Counter()
        self.app_mentions = Counter()
        self.calendar: list[dict] = []
        self.doc_kinds = Counter()
        self._seen: set[str] = set()
        self.moments: list[dict] = []   # when the person wrote, how fast they answered; never the text

    def recent(self, dt: datetime | None) -> bool:
        return self.since is None or dt is None or dt >= self.since

    def writer(self, sid: str):
        return open(self.digest_dir / f"{sid}.jsonl", "w", encoding="utf-8")

    def add_moment(self, text: str, dt, src: str, reply_s=None, blocking=None) -> None:
        if not dt:
            return
        words = len(re.findall(r"\w+", text))
        decision = words <= 6 or bool(re.match(r"\s*(yes|ja|ok(ay)?|approve|approved|go|do it|merge|ship|publish|start|continue|weiter|passt)\b", text, re.I))
        self.moments.append({"t": int(dt.timestamp()), "src": src, "words": words, "decision": decision,
                             "reply_s": int(reply_s) if reply_s is not None and 0 < reply_s < 6 * 3600 else None,
                             "blocking": blocking})   # True: the agent had finished its turn and was waiting for this answer

    def add_prompt(self, text: str, dt, src: str) -> str:
        t = redact(text, PROMPT_PREVIEW)
        key = t.lower() + "|" + (dt.strftime("%Y-%m-%d") if dt else "")
        if t and key in self._seen:
            return t          # same prompt seen in another source (e.g. transcript + history)
        self._seen.add(key)
        if t:
            self.prompts.append((t, dt, src))
            low = " " + t.lower() + " "
            for frag, name in APP_HINTS.items():
                if re.search(r"(?<![a-z])" + re.escape(frag) + r"(?![a-z])", low):
                    self.app_mentions[name] += 1
        return t


def iter_jsonl(fh):
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


NOISE_PREFIXES = ("<command-", "<local-command", "<system-reminder", "<environment_context", "<user_instructions",
                  "caveat:", "[request interrupted", "<user-prompt-submit-hook", "# agents.md", "<permissions",
                  # messages an agent tool puts in the user's place: other sessions, task results, context restarts
                  "another claude session", "this session is being continued", "background (from the session",
                  "[system notification", "<task-notification", "</task-notification", "base directory for this skill",
                  "<cross-session-message", "<agent-message", "agent message from", "<artifact-content", "</workspace_roots",
                  "<workspace_roots", "[subagent", "task (from the session", "# files mentioned")


def clean_user_text(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", " ", t or "", flags=re.S)
    t = re.sub(r"^\[Image[^\]]*\]\s*$", " ", t, flags=re.M)            # pasted-image markers
    if re.match(r"\s*\[\d+\]\s", t):                                    # numbered tool logs from agent sub-threads
        return ""
    t = re.sub(r"<[a-z_\-]+>.*?</[a-z_\-]+>", " ", t, flags=re.S) if t.lstrip().startswith("<") else t
    t = t.strip()
    return "" if t.lower().startswith(NOISE_PREFIXES) else t


def blocks_text(content) -> tuple[str, list[str]]:
    """Return (user-visible text, tool names) from a message content field."""
    if isinstance(content, str):
        return content, []
    text, tools = [], []
    for b in content or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") in ("text", "input_text"):
            text.append(b.get("text", ""))
        elif b.get("type") == "tool_use":
            tools.append(b.get("name", "tool"))
        # tool_result, image, document: deliberately ignored
    return "\n".join(text), tools


def program_of(cmd: str) -> str | None:
    """First real program in a shell command line; arguments are dropped."""
    cmd = cmd.strip()
    if not cmd or cmd.startswith("#"):
        return None
    toks = re.split(r"\s+", cmd)
    i = 0
    while i < len(toks) and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", toks[i]) or toks[i] in ("sudo", "env", "time", "nohup", "exec", "command", "builtin")):
        i += 1
    if i >= len(toks):
        return None
    p = toks[i].split("/")[-1]
    p = re.sub(r"[^A-Za-z0-9_.+\-]", "", p)
    if not p or len(p) > 30 or re.fullmatch(r"[0-9.]+", p):
        return None
    if p in ("python", "python3", "node", "npx", "bun", "deno", "uv") and i + 1 < len(toks):
        nxt = toks[i + 1].split("/")[-1]
        if re.fullmatch(r"[A-Za-z0-9_\-]+\.(py|js|ts|mjs|sh)", nxt):
            return f"{p} {nxt}"   # script names are useful evidence ("python3 invoice_hours.py")
    return p


# ------------------------------------------------------------------ sources
def claude_code_transcripts(run: Run, paths: list[Path]) -> dict:
    files = []
    for root in paths:
        files += list(root.glob("*/*.jsonl")) if root.is_dir() else []
    n_items = 0
    with run.writer("claude-code-transcripts") as w:
        for f in files:
            if is_secret_path(f):
                continue
            users, tools, start, end, cwd, last_agent, waiting = [], Counter(), None, None, None, None, None
            with open(f, encoding="utf-8", errors="replace") as fh:
                for ev in iter_jsonl(fh):
                    dt = to_dt(ev.get("timestamp"))
                    cwd = cwd or ev.get("cwd")
                    msg = ev.get("message") or {}
                    origin = ev.get("origin")
                    not_human = ev.get("isSidechain") or (isinstance(origin, dict) and origin.get("kind") not in (None, "human"))
                    if ev.get("type") == "user" and not ev.get("isMeta") and not not_human:
                        text, _ = blocks_text(msg.get("content"))
                        text = clean_user_text(text)
                        if text:
                            users.append((text, dt, (dt - last_agent).total_seconds() if dt and last_agent else None, waiting))
                            waiting = False
                    elif ev.get("type") == "assistant":
                        _, tn = blocks_text(msg.get("content"))
                        tools.update(tn)
                        last_agent = dt or last_agent
                        sr = msg.get("stop_reason")
                        waiting = True if sr == "end_turn" else (False if sr else waiting)
                    if dt:
                        start = min(start, dt) if start else dt
                        end = max(end, dt) if end else dt
            if not users or not run.recent(start):
                continue
            project = Path(cwd).name if cwd else f.parent.name.split("-")[-1]
            run.projects[redact(project)] += 1
            for t in tools:
                run.tools[t] += tools[t]
                if t.startswith("mcp__"):
                    run.mcp[t.split("__")[1]] += tools[t]
            first = run.add_prompt(users[0][0], users[0][1], "claude-code")
            for t, dt, _, _ in users[1:]:
                run.add_prompt(t, dt, "claude-code")
            for t, dt, rep, wt in users:
                run.add_moment(t, dt, "claude-code", rep if wt else None, wt)
            w.write(json.dumps({"kind": "session", "source": "claude-code", "project": redact(project),
                                "start": start.isoformat() if start else None,
                                "minutes": round((end - start).total_seconds() / 60) if start and end else None,
                                "user_turns": len(users), "first_prompt": first,
                                "later_prompts": [redact(t, FOLLOWUP_PREVIEW) for t, _, _, _ in users[1:1 + MAX_FOLLOWUPS]],
                                "tools": dict(tools.most_common(8))}, ensure_ascii=False) + "\n")
            n_items += 1
    return {"files_read": len(files), "items": n_items}


def markdown_notes(run: Run, sid: str, files: list[Path], limit: int = 2000) -> dict:
    n = 0
    with run.writer(sid) as w:
        for f in files:
            if is_secret_path(f) or not f.is_file():
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            text = re.sub(r"^---.*?---", "", text, flags=re.S)   # drop frontmatter
            w.write(json.dumps({"kind": "note", "source": sid, "title": redact(f.stem),
                                "text": redact(text, limit)}, ensure_ascii=False) + "\n")
            n += 1
    return {"files_read": n, "items": n}


def prompt_history(run: Run, sid: str, files: list[Path], text_key: str, time_key: str) -> dict:
    n = 0
    with run.writer(sid) as w:
        for f in files:
            if is_secret_path(f) or not f.is_file():
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                for ev in iter_jsonl(fh):
                    dt = to_dt(ev.get(time_key))
                    text = clean_user_text(ev.get(text_key) or "")
                    if not text or not run.recent(dt):
                        continue
                    t = run.add_prompt(text, dt, sid)
                    w.write(json.dumps({"kind": "prompt", "source": sid, "at": dt.isoformat() if dt else None,
                                        "project": redact(Path(ev["project"]).name) if ev.get("project") else None,
                                        "text": t}, ensure_ascii=False) + "\n")
                    n += 1
    return {"files_read": len(files), "items": n}


def codex_sessions(run: Run, paths: list[Path]) -> dict:
    files = []
    for root in paths:
        files += list(root.rglob("*.jsonl")) if root.is_dir() else []
    n = 0
    with run.writer("codex-sessions") as w:
        for f in files:
            if is_secret_path(f):
                continue
            users, tools, progs, start, end, cwd, last_agent, waiting = [], Counter(), Counter(), None, None, None, None, None
            mark = len(run.moments)
            with open(f, encoding="utf-8", errors="replace") as fh:
                for ev in iter_jsonl(fh):
                    dt = to_dt(ev.get("timestamp"))
                    p = ev.get("payload") or ev
                    if ev.get("type") == "session_meta" or p.get("type") == "session_meta":
                        cwd = cwd or p.get("cwd")
                        if isinstance(p.get("source"), dict) and "subagent" in p["source"]:
                            users = []
                            break                                  # a sub-agent's thread: not the person's words
                    if p.get("type") == "message" and p.get("role") == "user":
                        text, _ = blocks_text(p.get("content"))
                        text = clean_user_text(text)
                        if text:
                            run.add_moment(text, dt, "codex", (dt - last_agent).total_seconds() if dt and last_agent and waiting else None, waiting)
                            users.append((text, dt))
                            waiting = False
                    elif p.get("type") == "message" and p.get("role") == "assistant":
                        last_agent = dt or last_agent
                        waiting = True
                    elif p.get("type") in ("function_call", "local_shell_call", "custom_tool_call"):
                        name = p.get("name") or p.get("type")
                        tools[name] += 1
                        if name.startswith("mcp__"):
                            run.mcp[name.split("__")[1]] += 1
                        args = p.get("arguments")
                        try:
                            args = json.loads(args) if isinstance(args, str) else (args or {})
                        except json.JSONDecodeError:
                            args = {}
                        cmd = args.get("command") if isinstance(args, dict) else None
                        if isinstance(cmd, list):
                            cmd = cmd[-1] if cmd[:1] in (["bash"], ["zsh"], ["sh"]) else " ".join(cmd)
                        if isinstance(cmd, str):
                            for part in re.split(r"&&|\|\||;|\|", cmd):
                                prog = program_of(part)
                                if prog:
                                    progs[prog] += 1
                    if dt:
                        start = min(start, dt) if start else dt
                        end = max(end, dt) if end else dt
            if not users or not run.recent(start):
                del run.moments[mark:]                      # sub-agent threads and old sessions leave no trace
                continue
            project = redact(Path(cwd).name) if cwd else "unknown"
            run.projects[project] += 1
            run.tools.update(tools)
            run.programs.update(progs)
            first = run.add_prompt(users[0][0], users[0][1], "codex")
            for t, dt in users[1:]:
                run.add_prompt(t, dt, "codex")
            w.write(json.dumps({"kind": "session", "source": "codex", "project": project,
                                "start": start.isoformat() if start else None,
                                "minutes": round((end - start).total_seconds() / 60) if start and end else None,
                                "user_turns": len(users), "first_prompt": first,
                                "later_prompts": [redact(t, FOLLOWUP_PREVIEW) for t, _ in users[1:1 + MAX_FOLLOWUPS]],
                                "programs": dict(progs.most_common(8))}, ensure_ascii=False) + "\n")
            n += 1
    return {"files_read": len(files), "items": n}


def _open_export(p: Path):
    """Yield (name, bytes) for the JSON files of a chat export (zip or folder)."""
    if p.is_file() and p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                base = Path(n).name.lower()
                if base.endswith(".json") and not is_secret_path(n):
                    yield base, z.read(n)
    elif p.is_dir():
        for f in p.glob("*.json"):
            if not is_secret_path(f):
                yield f.name.lower(), f.read_bytes()


def chatgpt_export(run: Run, paths: list[Path]) -> dict:
    n, files, gpts = 0, 0, Counter()
    with run.writer("chatgpt-export") as w:
        for p in paths:
            for name, data in _open_export(p):
                if not name.startswith("conversations"):
                    continue
                files += 1
                for conv in json.load(io.BytesIO(data)):
                    created = to_dt(conv.get("create_time"))
                    if not run.recent(created):
                        continue
                    msgs = []
                    for node in (conv.get("mapping") or {}).values():
                        m = (node or {}).get("message") or {}
                        if (m.get("author") or {}).get("role") != "user":
                            continue
                        parts = (m.get("content") or {}).get("parts") or []
                        text = " ".join(x for x in parts if isinstance(x, str))
                        if text.strip():
                            msgs.append((to_dt(m.get("create_time")) or created, text))
                    if not msgs:
                        continue
                    msgs.sort(key=lambda x: x[0] or created)
                    if conv.get("gizmo_id"):
                        gpts["custom GPT"] += 1
                    first = run.add_prompt(msgs[0][1], msgs[0][0], "chatgpt")
                    for dt, t in msgs[1:]:
                        run.add_prompt(t, dt, "chatgpt")
                    for dt, t in msgs:
                        run.add_moment(t, dt, "chatgpt")
                    w.write(json.dumps({"kind": "conversation", "source": "chatgpt",
                                        "title": redact(conv.get("title"), 90),
                                        "start": created.isoformat() if created else None,
                                        "user_turns": len(msgs), "first_prompt": first,
                                        "later_prompts": [redact(t, FOLLOWUP_PREVIEW) for _, t in msgs[1:1 + MAX_FOLLOWUPS]],
                                        "custom_gpt": bool(conv.get("gizmo_id"))}, ensure_ascii=False) + "\n")
                    n += 1
    return {"files_read": files, "items": n, "custom_gpt_conversations": gpts["custom GPT"]}


def claude_export(run: Run, paths: list[Path], memory_only: bool = False) -> dict:
    """At depth quick only memory and project instructions are read, not conversations."""
    n, files = 0, 0
    with run.writer("claude-export") as w:
        for p in paths:
            for name, data in _open_export(p):
                obj = json.load(io.BytesIO(data))
                if name.startswith("conversations") and not memory_only:
                    files += 1
                    for conv in obj:
                        created = to_dt(conv.get("created_at"))
                        if not run.recent(created):
                            continue
                        msgs = []
                        for m in conv.get("chat_messages") or []:
                            if m.get("sender") != "human":
                                continue
                            text = m.get("text") or blocks_text(m.get("content"))[0]
                            if text.strip():
                                msgs.append((to_dt(m.get("created_at")) or created, text))
                        if not msgs:
                            continue
                        first = run.add_prompt(msgs[0][1], msgs[0][0], "claude-ai")
                        for dt, t in msgs[1:]:
                            run.add_prompt(t, dt, "claude-ai")
                        for dt, t in msgs:
                            run.add_moment(t, dt, "claude-ai")
                        w.write(json.dumps({"kind": "conversation", "source": "claude-ai",
                                            "title": redact(conv.get("name"), 90),
                                            "start": created.isoformat() if created else None,
                                            "user_turns": len(msgs), "first_prompt": first,
                                            "later_prompts": [redact(t, FOLLOWUP_PREVIEW) for _, t in msgs[1:1 + MAX_FOLLOWUPS]]},
                                           ensure_ascii=False) + "\n")
                        n += 1
                elif name.startswith("projects"):
                    files += 1
                    for pr in obj:
                        w.write(json.dumps({"kind": "project", "source": "claude-ai", "title": redact(pr.get("name"), 90),
                                            "description": redact(pr.get("description"), 300),
                                            "doc_titles": [redact(d.get("filename"), 80) for d in (pr.get("docs") or [])][:10],
                                            "instructions": redact(pr.get("prompt_template"), 400)}, ensure_ascii=False) + "\n")
                        n += 1
                elif name.startswith("memories"):
                    files += 1
                    for mem in obj if isinstance(obj, list) else [obj]:
                        text = mem.get("conversations_memory") or ""
                        for k, v in (mem.get("project_memories") or {}).items():
                            text += f"\n{v}"
                        if text.strip():
                            w.write(json.dumps({"kind": "memory", "source": "claude-ai", "text": redact(text, 3000)},
                                               ensure_ascii=False) + "\n")
                            n += 1
    return {"files_read": files, "items": n}


def shell_history(run: Run, files: list[Path]) -> dict:
    n, hours = 0, Counter()
    for f in files:
        if is_secret_path(f) or not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            dt = None
            m = re.match(r"^: (\d+):\d+;(.*)$", line)          # zsh extended history
            if m:
                dt, line = to_dt(m.group(1)), m.group(2)
            elif line.startswith("- cmd: "):                    # fish
                line = line[7:]
            if not run.recent(dt):
                continue
            for part in re.split(r"&&|\|\||;|\|", line):
                prog = program_of(part)
                if prog:
                    run.programs[prog] += 1
                    n += 1
            if dt:
                hours[dt.strftime("%a %H")] += 1
    with run.writer("shell-history") as w:
        w.write(json.dumps({"kind": "programs", "source": "shell", "top": dict(run.programs.most_common(40))}) + "\n")
    return {"files_read": len(files), "items": n}


def _ics_events(text: str):
    text = re.sub(r"\r?\n[ \t]", "", text)                     # unfold lines
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.S):
        ev = defaultdict(list)
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            ev[k.split(";")[0].upper()].append((k, v))
        yield ev


def _ics_dt(raw: str):
    raw = raw.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            d = datetime.strptime(raw, fmt)
            return d.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def calendar_files(run: Run, files: list[Path]) -> dict:
    n = 0
    with run.writer("calendar-files") as w:
        for f in files:
            if is_secret_path(f) or not f.is_file():
                continue
            for ev in _ics_events(f.read_text(encoding="utf-8", errors="replace")):
                start = _ics_dt(ev["DTSTART"][0][1]) if ev.get("DTSTART") else None
                end = _ics_dt(ev["DTEND"][0][1]) if ev.get("DTEND") else None
                rrule = ev["RRULE"][0][1] if ev.get("RRULE") else ""
                if not rrule and not run.recent(start):
                    continue
                org = ev["ORGANIZER"][0][1].lower() if ev.get("ORGANIZER") else ""
                org_dom = org.split("@")[-1] if "@" in org else ""
                att = [v.lower() for _, v in ev.get("ATTENDEE", [])]
                ext = sum(1 for a in att if "@" in a and org_dom and not a.endswith("@" + org_dom))
                loc = (ev["LOCATION"][0][1] if ev.get("LOCATION") else "") + " " + (ev["DESCRIPTION"][0][1] if ev.get("DESCRIPTION") else "")
                video = next((v for k, v in [("zoom.us", "Zoom"), ("meet.google", "Google Meet"), ("teams.microsoft", "Microsoft Teams")] if k in loc), None)
                freq = re.search(r"FREQ=(\w+)", rrule)
                interval = re.search(r"INTERVAL=(\d+)", rrule)
                byday = re.search(r"BYDAY=([\w,]+)", rrule)
                item = {"kind": "event", "source": "calendar", "title": redact(ev["SUMMARY"][0][1], 80) if ev.get("SUMMARY") else "",
                        "start": start.isoformat() if start else None,
                        "minutes": round((end - start).total_seconds() / 60) if start and end else None,
                        "repeats": (freq.group(1).lower() if freq else None),
                        "interval": int(interval.group(1)) if interval else 1,
                        "days": byday.group(1) if byday else None,
                        "attendees": len(att), "external_attendees": ext, "video": video}
                run.calendar.append(item)
                w.write(json.dumps(item, ensure_ascii=False) + "\n")
                n += 1
    return {"files_read": len(files), "items": n}


DOC_KIND_HINTS = [
    ("template", r"template|vorlage|boilerplate"), ("proposal", r"proposal|angebot|offer|quote|pitch"),
    ("invoice", r"invoice|rechnung|billing|abrechnung"), ("contract", r"contract|vertrag|agreement|nda|agb"),
    ("meeting notes", r"meeting|notes|protokoll|minutes|call|notizen"), ("report", r"report|bericht|status|update|recap"),
    ("checklist", r"checklist|checkliste|todo|sop|process|prozess|playbook"), ("brand", r"brand|style|voice|tone|marke"),
    ("onboarding", r"onboarding|welcome|kickoff|kick-off"),
]


def documents(run: Run, roots: list[Path], max_files: int = 400) -> dict:
    n, read_bodies = 0, 0
    with run.writer("documents") as w:
        for r in roots:
            if not r.is_dir():
                continue
            from inventory import walk            # same pruning as the inventory: no hidden, secret, repo or app folders
            for f in sorted(walk(r, 5), key=lambda x: -x.stat().st_mtime if x.exists() else 0):   # newest first
                if n >= max_files:
                    break
                rel_parts = f.relative_to(r).parts
                if any(p.startswith(".") for p in rel_parts) or is_secret_path(f) or not f.is_file():
                    continue
                ext = f.suffix.lower()
                if ext not in {".md", ".txt", ".rtf", ".docx", ".doc", ".pdf", ".pages", ".xlsx", ".csv", ".pptx", ".key", ".numbers", ".odt"}:
                    continue
                st = f.stat()
                mt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                name = f.stem.lower()
                kinds = [k for k, rx in DOC_KIND_HINTS if re.search(rx, name + " " + " ".join(rel_parts[:-1]).lower())]
                run.doc_kinds.update(kinds or ["other"])
                item = {"kind": "file", "source": "documents", "folder": redact("/".join(rel_parts[:-1])[-60:]),
                        "name": redact(f.stem, 80), "type": ext.lstrip("."), "modified": mt.date().isoformat(),
                        "kb": round(st.st_size / 1024), "looks_like": kinds}
                if ext in (".md", ".txt") and st.st_size < 200_000:
                    item["preview"] = redact(f.read_text(encoding="utf-8", errors="replace"), DOC_PREVIEW)
                    read_bodies += 1
                elif ext == ".csv" and st.st_size < 5_000_000:
                    with open(f, encoding="utf-8", errors="replace") as fh:
                        item["columns"] = redact(fh.readline(), 200)   # header row only
                w.write(json.dumps(item, ensure_ascii=False) + "\n")
                n += 1
    return {"files_listed": n, "text_previews_read": read_bodies, "items": n}


def installed_apps(run: Run, src: dict) -> dict:
    apps = src.get("apps") or []
    with run.writer("installed-apps") as w:
        w.write(json.dumps({"kind": "apps", "source": "apps", "apps": apps}) + "\n")
    return {"items": len(apps)}


# ------------------------------------------------------------------ stats
def repeated_requests(prompts) -> list[dict]:
    """Group first-words patterns of prompts. Recurring asks are the strongest
    evidence of a workflow worth automating."""
    groups: dict[str, list] = defaultdict(list)
    for text, dt, src in prompts:
        # proper nouns (clients, places) vary between repeats of the same ask, so they are left out of the key
        toks = re.findall(r"[A-Za-zÄÖÜäöüß]+", text)
        words = [w.lower() for i, w in enumerate(toks) if (i == 0 or not w[0].isupper()) and w.lower() not in STOP and len(w) > 2 and w != "name"]
        if len(words) < 2:
            continue
        key = " ".join(sorted(set(words[:6]))[:4])
        groups[key].append((text, dt, src))
    out = []
    for key, items in groups.items():
        if len(items) >= 3:
            dts = sorted(d for _, d, _ in items if d)
            out.append({"pattern": key, "count": len(items), "sources": dict(Counter(s for _, _, s in items)),
                        "first": dts[0].date().isoformat() if dts else None, "last": dts[-1].date().isoformat() if dts else None,
                        "weekdays": dict(Counter(d.strftime("%a") for d in dts).most_common(3)),
                        "examples": [t[:140] for t, _, _ in items[:3]]})
    return sorted(out, key=lambda x: -x["count"])[:40]


def keyword_counts(prompts, top=60):
    uni, bi = Counter(), Counter()
    for text, _, _ in prompts:
        words = [w for w in re.findall(r"[a-zäöüß]+", text.lower()) if w not in STOP and len(w) > 2]
        uni.update(set(words))
        bi.update({f"{a} {b}" for a, b in zip(words, words[1:])})
    return {"words": dict(uni.most_common(top)), "phrases": dict((k, v) for k, v in bi.most_common(top) if v >= 3)}


def rhythm(prompts):
    by_day, by_hour = Counter(), Counter()
    for _, dt, _ in prompts:
        if dt:
            by_day[dt.strftime("%a")] += 1
            by_hour[dt.hour] += 1
    return {"by_weekday": dict(by_day), "by_hour_utc": dict(sorted(by_hour.items()))}


def recurring_meetings(events):
    rec = [e for e in events if e.get("repeats")]
    per_week = {"daily": 5, "weekly": 1, "monthly": 12 / 52, "yearly": 1 / 52}
    out = []
    for e in rec:
        days = len(e["days"].split(",")) if e.get("days") and e["repeats"] == "weekly" else 1
        hours = (e.get("minutes") or 0) / 60 * per_week.get(e["repeats"], 0) * days / max(e.get("interval") or 1, 1)
        out.append({"title": e["title"], "repeats": e["repeats"], "interval": e.get("interval"), "days": e.get("days"),
                    "minutes": e.get("minutes"), "hours_per_week": round(hours, 2), "attendees": e["attendees"],
                    "external_attendees": e["external_attendees"]})
    one_off = [e for e in events if not e.get("repeats")]
    weeks = 1
    dts = sorted(to_dt(e["start"]) for e in one_off if e.get("start"))
    if len(dts) > 1:
        weeks = max(1, (dts[-1] - dts[0]).days / 7)
    ext = [e for e in one_off if e.get("external_attendees")]
    return {"recurring": sorted(out, key=lambda x: -x["hours_per_week"]),
            "one_off_per_week": round(len(one_off) / weeks, 1),
            "external_meetings_per_week": round(len(ext) / weeks, 1),
            "meeting_hours_per_week": round(sum((e.get("minutes") or 0) for e in one_off) / 60 / weeks + sum(x["hours_per_week"] for x in out), 1)}


def data_span(run):
    """First and last dated item actually seen. Divide counts by these months, not by the window."""
    dts = [d for _, d, _ in run.prompts if d] + [to_dt(e["start"]) for e in run.calendar if e.get("start") and not e.get("repeats")]
    dts = [d for d in dts if d]
    if not dts:
        return None
    a, b = min(dts), max(dts)
    return {"first": a.date().isoformat(), "last": b.date().isoformat(), "months": round(max((b - a).days, 1) / 30.4, 1)}


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--consent", required=True)
    ap.add_argument("--home", default=None, help="home folder the inventory was made for (default: yours)")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    inv = read_json(a.inventory)
    consent = read_json(a.consent)
    allowed = {k for k, v in (consent.get("sources") or {}).items() if v is True}
    if not allowed:
        die("consent.json allows no sources; nothing was read")
    set_masked_names(consent.get("mask_names") or [])
    since_days = consent.get("since_days", 180)
    since = datetime.now(timezone.utc) - timedelta(days=since_days) if since_days else None
    home = Path(a.home).expanduser().resolve() if a.home else Path.home()
    run = Run(Path(a.out_dir).expanduser(), since)

    def paths_of(src):
        return [Path(str(p).replace("~", str(home), 1)) if str(p).startswith("~") else Path(p) for p in src["paths"]]

    for src in inv["sources"]:
        sid = src["id"]
        entry = {"id": sid, "label": src["label"], "consented": sid in allowed, "status": src["status"]}
        levels = ["quick", "standard", "deep"]
        if consent.get("depth") in levels and src.get("depth") in levels and levels.index(src["depth"]) > levels.index(consent["depth"]):
            entry["read"] = False
            entry["note"] = f"above the chosen depth ({consent['depth']})"
            run.log.append(entry)
            continue
        if sid not in allowed or src["status"] != "found":
            entry["read"] = False
            run.log.append(entry)
            continue
        if src.get("kind") == "connector":
            # connectors are read by the agent itself (see subskills/1-discover.md); count what it wrote
            f = run.digest_dir / f"{sid.replace(':', '-')}.jsonl"
            n = sum(1 for _ in open(f, encoding="utf-8")) if f.exists() else 0
            entry.update({"read": n > 0, "read_by": "agent", "items": n})
            run.log.append(entry)
            continue
        ps = paths_of(src)
        if sid == "claude-code-transcripts":
            res = claude_code_transcripts(run, ps)
        elif sid == "claude-code-memory":
            files = sorted((home / ".claude" / "projects").glob("*/memory/*.md"))
            files += [p for p in [home / ".claude" / "CLAUDE.md"] if p.exists()]
            res = markdown_notes(run, sid, files)
        elif sid == "claude-code-history":
            res = prompt_history(run, sid, ps, "display", "timestamp")
        elif sid == "codex-sessions":
            res = codex_sessions(run, ps)
        elif sid == "codex-history":
            res = prompt_history(run, sid, ps, "text", "ts")
        elif sid == "codex-memory":
            files = [f for p in ps for f in (sorted(p.glob("*.md")) if p.is_dir() else [p])]
            res = markdown_notes(run, sid, files)
        elif sid == "chatgpt-export":
            res = chatgpt_export(run, ps)
        elif sid == "claude-export":
            res = claude_export(run, ps, memory_only=consent.get("depth") == "quick")
        elif sid == "shell-history":
            res = shell_history(run, ps)
        elif sid == "calendar-files":
            res = calendar_files(run, ps)
        elif sid == "documents":
            res = documents(run, ps)
        elif sid == "installed-apps":
            res = installed_apps(run, src)
        elif sid in ("mac-activity", "git-activity", "screen-time"):
            res = {"note": "read by rhythm.py"}      # timing only; rhythm.py fills in the counts
        else:
            res = {"note": "no reader for this source"}
        entry.update({"read": True, **res})
        run.log.append(entry)

    stats = {
        "schema": "dayprint.stats/0.1", "generator": GENERATOR, "generated_at": now_iso(),
        "window_days": since_days, "data_span": data_span(run), "prompts_total": len(run.prompts),
        "prompts_by_source": dict(Counter(s for _, _, s in run.prompts)),
        "repeated_requests": repeated_requests(run.prompts),
        "keywords": keyword_counts(run.prompts), "rhythm": rhythm(run.prompts),
        "agent_tools": dict(run.tools.most_common(30)), "mcp_servers_used": dict(run.mcp.most_common(20)),
        "programs": dict(run.programs.most_common(30)), "projects": dict(run.projects.most_common(20)),
        "apps_mentioned": dict(run.app_mentions.most_common(30)), "document_kinds": dict(run.doc_kinds),
        "calendar": recurring_meetings(run.calendar) if run.calendar else None,
    }
    write_json(run.out / "stats.json", stats)
    with run.writer("activity-prompts") as w:                  # times only, for rhythm.py; no text
        for m in sorted(run.moments, key=lambda m: m["t"]):
            if since is None or m["t"] >= since.timestamp():
                w.write(json.dumps(m) + "\n")
    write_json(run.out / "read-log.json", {"schema": "dayprint.read-log/0.1", "generator": GENERATOR,
                                           "generated_at": now_iso(), "window_days": since_days, "depth": consent.get("depth"),
                                           "uploaded": False, "secret_files_opened": 0,
                                           "masked_names": len(consent.get("mask_names") or []), "sources": run.log})
    for e in run.log:
        print(f"{'read' if e.get('read') else 'skip':5} {e['id']:26} {e.get('items', '')}")
    print(f"prompts: {len(run.prompts)}  repeated patterns: {len(stats['repeated_requests'])}  -> {run.out}")


if __name__ == "__main__":
    main()
