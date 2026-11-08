#!/usr/bin/env python3
"""Step 1 of discover: list the data sources on this computer WITHOUT reading them.

Only file-system metadata is used (names, counts, sizes, dates). Zip exports are
recognised by their file list, never by their contents. Secret-looking paths are
skipped entirely and are not even counted.

  python3 inventory.py --out ~/dayprint/2026-11-07/inventory.json
  python3 inventory.py --home examples/persona-lena/home --out /tmp/inv.json
"""
from __future__ import annotations

import argparse
import os
import sys
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GENERATOR, is_secret_path, now_iso, tilde, write_json  # noqa: E402

EXPORT_SEARCH_DIRS = ["Downloads", "Desktop", "Documents"]

# Depth levels the person chooses from. Each source belongs to the lowest level that includes it.
#   quick    = what the AI tools already remember about you (memory, instructions, projects)
#   standard = + chat history from ChatGPT, Claude and Codex, and the calendar
#   deep     = + documents, terminal history, installed apps and every connected app
DEPTHS = ["quick", "standard", "deep"]
SOURCE_DEPTH = {
    "claude-code-memory": "quick", "codex-memory": "quick",
    "claude-code-transcripts": "standard", "claude-code-history": "standard", "codex-sessions": "standard",
    "codex-history": "standard", "chatgpt-export": "standard", "claude-export": "quick", "calendar-files": "standard",
    "documents": "deep", "shell-history": "deep", "installed-apps": "deep",
    # timestamps only, used by rhythm.py to rebuild an average working day
    "mac-activity": "standard", "git-activity": "standard", "screen-time": "deep",
}
DOC_DIRS = ["Documents", "Desktop", "Downloads", "Notes", "Obsidian", "iCloud Drive"]
DOC_EXT = {".md", ".txt", ".rtf", ".docx", ".doc", ".pdf", ".pages", ".xlsx", ".xls", ".csv",
           ".numbers", ".pptx", ".key", ".odt", ".ods"}


def walk(root: Path, max_depth: int, follow_hidden: bool = False):
    """Yield files under root, skipping secret and hidden paths."""
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        depth = len(d.parts) - root_depth
        if ".git" in dirnames or ".git" in filenames:      # a code repository: code, not the person's documents
            dirnames[:] = []
            continue
        dirnames[:] = [n for n in dirnames
                       if not is_secret_path(d / n)
                       and (follow_hidden or not n.startswith("."))
                       and not n.endswith((".app", ".photoslibrary", ".musiclibrary"))
                       and depth < max_depth]
        for n in filenames:
            p = d / n
            if n.startswith(".") and not follow_hidden:
                continue
            if is_secret_path(p):
                continue
            yield p


def summarise(files: list[Path], home: Path) -> dict:
    if not files:
        return {"files": 0, "bytes": 0}
    stats = []
    for f in files:
        try:
            stats.append(f.stat())
        except OSError:
            pass
    mtimes = [s.st_mtime for s in stats]
    fmt = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat()  # noqa: E731
    return {
        "files": len(stats),
        "bytes": sum(s.st_size for s in stats),
        "files_changed_from": fmt(min(mtimes)) if mtimes else None,   # file dates, not content dates
        "files_changed_to": fmt(max(mtimes)) if mtimes else None,
    }


def host_app() -> str:
    """The app macOS asks Full Disk Access for: the one at the top of this process tree."""
    try:
        import subprocess
        pid, seen = os.getppid(), []
        for _ in range(12):
            out = subprocess.run(["ps", "-o", "ppid=,comm=", "-p", str(pid)], capture_output=True, text=True, timeout=5).stdout.strip()
            if not out:
                break
            ppid, comm = out.split(None, 1)
            seen.append(comm)
            pid = int(ppid)
            if pid <= 1:
                break
        apps = [re.search(r"/([^/]+)\.app/", c).group(1) for c in seen if ".app/" in c]
        return apps[-1] if apps else "Terminal"
    except Exception:
        return "Terminal"


def source(sid, label, kind, files, home, paths, note, extra=None):
    s = {"id": sid, "label": label, "kind": kind,
         "status": "found" if files else "not_found",
         "paths": [tilde(p, home) for p in paths], **summarise(files, home),
         "privacy_note": note}
    if extra:
        s.update(extra)
    return s


def classify_zip(p: Path) -> str | None:
    try:
        with zipfile.ZipFile(p) as z:
            names = {Path(n).name.lower() for n in z.namelist()}
    except (zipfile.BadZipFile, OSError):
        return None
    if not any(n.startswith("conversations") and n.endswith(".json") for n in names):
        return None
    if "chat.html" in names or "message_feedback.json" in names or "user.json" in names:
        return "chatgpt"
    if "users.json" in names or "projects.json" in names or "memories.json" in names:
        return "claude"
    return "unknown-chat"


def classify_dir(p: Path) -> str | None:
    names = {n.lower() for n in os.listdir(p)} if p.is_dir() else set()
    if not any(n.startswith("conversations") and n.endswith(".json") for n in names):
        return None
    if "chat.html" in names or "user.json" in names:
        return "chatgpt"
    if "users.json" in names or "projects.json" in names:
        return "claude"
    return "unknown-chat"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", default=str(Path.home()), help="home folder to inventory (default: yours)")
    ap.add_argument("--extra", action="append", default=[], help="extra folder or export zip the user pointed to")
    ap.add_argument("--apps-dir", action="append", default=None, help="application folders (default /Applications and ~/Applications)")
    ap.add_argument("--depth", choices=DEPTHS, default="standard", help="which sources to preselect: quick, standard or deep")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    home = Path(a.home).expanduser().resolve()
    srcs = []

    # Claude Code ---------------------------------------------------------
    cproj = home / ".claude" / "projects"
    transcripts = [p for p in cproj.glob("*/*.jsonl")] if cproj.exists() else []
    srcs.append(source("claude-code-transcripts", "Claude Code chats", "agent-history", transcripts, home, [cproj],
                       "Your prompts and which tools ran. Tool output and file contents are skipped.",
                       {"projects": len({p.parent.name for p in transcripts})}))
    mem = [p for p in cproj.glob("*/memory/*.md")] if cproj.exists() else []
    mem += [p for p in [home / ".claude" / "CLAUDE.md"] if p.exists()]
    srcs.append(source("claude-code-memory", "Claude Code memory and instructions", "agent-memory", mem, home,
                       [cproj / "*/memory", home / ".claude/CLAUDE.md"], "Short notes Claude keeps about your work."))
    hist = [p for p in [home / ".claude" / "history.jsonl"] if p.exists()]
    srcs.append(source("claude-code-history", "Claude Code prompt history", "agent-history", hist, home,
                       [home / ".claude/history.jsonl"], "Prompts you typed, with dates."))

    # Codex ---------------------------------------------------------------
    cx = home / ".codex"
    sess = list((cx / "sessions").rglob("*.jsonl")) + list((cx / "archived_sessions").rglob("*.jsonl")) if cx.exists() else []
    srcs.append(source("codex-sessions", "Codex sessions", "agent-history", sess, home,
                       [cx / "sessions", cx / "archived_sessions"],
                       "Your prompts and which commands ran. Command output is skipped."))
    cxh = [p for p in [cx / "history.jsonl"] if p.exists()]
    srcs.append(source("codex-history", "Codex prompt history", "agent-history", cxh, home, [cx / "history.jsonl"],
                       "Prompts you typed, with dates."))
    cxm = [p for p in [cx / "AGENTS.md"] if p.exists()] + (list((cx / "memories").glob("*.md")) if (cx / "memories").exists() else [])
    srcs.append(source("codex-memory", "Codex instructions and memories", "agent-memory", cxm, home,
                       [cx / "AGENTS.md", cx / "memories"], "Standing instructions you gave Codex."))

    # Chat exports (ChatGPT, Claude.ai) -----------------------------------
    found = {"chatgpt": [], "claude": [], "unknown-chat": []}
    roots = [home / d for d in EXPORT_SEARCH_DIRS] + [Path(x).expanduser() for x in a.extra]
    for r in roots:
        if r.is_file() and r.suffix.lower() == ".zip":
            k = classify_zip(r)
            if k:
                found[k].append(r)
            continue
        if not r.is_dir():
            continue
        for p in walk(r, 3):
            if p.suffix.lower() == ".zip" and p.stat().st_size < 4_000_000_000:
                k = classify_zip(p)
                if k:
                    found[k].append(p)
            elif p.name.lower().startswith("conversations") and p.suffix == ".json":
                k = classify_dir(p.parent)
                if k and p.parent not in found[k]:
                    found[k].append(p.parent)
    srcs.append(source("chatgpt-export", "ChatGPT export", "chat-export", found["chatgpt"], home, found["chatgpt"],
                       "Conversation titles and your messages. Read inside the zip, nothing is unpacked."))
    srcs.append(source("claude-export", "Claude.ai export", "chat-export", found["claude"], home, found["claude"],
                       "Conversation titles, your messages, project names and memory."))

    # Shell history -------------------------------------------------------
    sh = [p for p in [home / ".zsh_history", home / ".bash_history", home / ".local/share/fish/fish_history"] if p.exists()]
    srcs.append(source("shell-history", "Terminal history", "activity", sh, home, sh,
                       "Program names only (git, python, npm). Arguments are never read, they can hold secrets."))

    # Calendars -----------------------------------------------------------
    ics = []
    for r in [home / d for d in EXPORT_SEARCH_DIRS] + [Path(x).expanduser() for x in a.extra]:
        if r.is_file() and r.suffix.lower() == ".ics":
            ics.append(r)
        elif r.is_dir():
            ics += [p for p in walk(r, 3) if p.suffix.lower() == ".ics"]
    srcs.append(source("calendar-files", "Calendar exports (.ics)", "calendar", ics, home, ics,
                       "Event titles, times and how often they repeat. Attendees become counts."))

    # Documents -----------------------------------------------------------
    docs, by_ext, top = [], {}, {}
    for d in DOC_DIRS:
        r = home / d
        if not r.is_dir():
            continue
        for p in walk(r, 5):
            ext = p.suffix.lower()
            if ext in DOC_EXT:
                docs.append(p)
                by_ext[ext] = by_ext.get(ext, 0) + 1
                rel = p.relative_to(home).parts
                key = "/".join(rel[:2]) if len(rel) > 2 else rel[0]
                top[key] = top.get(key, 0) + 1
    srcs.append(source("documents", "Documents and notes", "files", docs, home, [home / d for d in DOC_DIRS if (home / d).exists()],
                       "File names and the first lines of text and Markdown files. Office files: names only.",
                       {"by_extension": dict(sorted(by_ext.items(), key=lambda x: -x[1])),
                        "busiest_folders": dict(sorted(top.items(), key=lambda x: -x[1])[:8])}))

    # Apps ----------------------------------------------------------------
    app_dirs = [Path(x).expanduser() for x in a.apps_dir] if a.apps_dir else [Path("/Applications"), home / "Applications"]
    apps = []
    for r in app_dirs:
        if r.is_dir():
            apps += [r / n for n in os.listdir(r) if n.endswith(".app")]
    srcs.append(source("installed-apps", "Installed apps", "apps", apps, home, app_dirs,
                       "App names only.", {"apps": sorted({p.stem for p in apps})}))

    # Working-day sources: timestamps only (rhythm.py reads them)
    import subprocess
    import sys as _sys
    if _sys.platform == "darwin" and home == Path.home().resolve():      # the power log belongs to this Mac's own user
        try:
            pm = subprocess.run(["pmset", "-g", "log"], capture_output=True, text=True, timeout=60).stdout
            n_ev = len(re.findall(r"Display is turned (?:on|off)| Sleep | Wake ", pm))
            first = re.search(r"^(\d{4}-\d\d-\d\d)", pm, flags=re.M)
        except (OSError, subprocess.TimeoutExpired):
            n_ev, first = 0, None
        s_ = source("mac-activity", "When your Mac is in use", "activity", [], home, [], "Times the display turned on and off, sleep and wake. Nothing else.",
                    {"events": n_ev, "files_changed_from": first.group(1) if first else None})
        s_["status"], s_["files"] = ("found" if n_ev else "not_found"), n_ev
        srcs.append(s_)
    from rhythm import find_repos
    repos = find_repos(home)
    s_ = source("git-activity", "Your commit times", "activity", [], home, [], "Times of your own commits in local repositories. No code, no messages.",
                {"repositories": len(repos)})
    s_["status"], s_["files"] = ("found" if repos else "not_found"), len(repos)
    srcs.append(s_)
    kc = home / "Library/Application Support/Knowledge/knowledgeC.db"
    s_ = source("screen-time", "Screen Time (app focus)", "activity", [kc] if kc.exists() else [], home, [kc],
                "How long each app was in front, by app name. Needs Full Disk Access for the app running the agent.")
    if kc.exists():
        try:                                   # opening reads nothing; macOS refuses the open itself without Full Disk Access
            open(kc, "rb").close()
            s_["access"] = "granted"
        except PermissionError:
            s_["access"] = "needs_full_disk_access"
            s_["host_app"] = host_app()
    srcs.append(s_)

    # Connectors the agent itself can reach are added by the agent (see subskills/1-discover.md)
    for s in srcs:
        s["depth"] = SOURCE_DEPTH[s["id"]]
        s["preselected"] = s["status"] == "found" and DEPTHS.index(s["depth"]) <= DEPTHS.index(a.depth)
    write_json(a.out, {"schema": "dayprint.inventory/0.1", "generator": GENERATOR,
                       "generated_at": now_iso(), "home": "~", "depth": a.depth, "sources": srcs})
    for s in srcs:
        mark = ("yes" if s["preselected"] else "found") if s["status"] == "found" else "-"
        print(f"{mark:6} {s['id']:26} {s.get('files', 0):6} files  {s['depth']:8} {s['label']}")


if __name__ == "__main__":
    main()
