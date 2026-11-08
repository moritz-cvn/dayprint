#!/usr/bin/env python3
"""Reconstruct how the person works: an average day, hour by hour, and their tempo.

  python3 rhythm.py --run <run> --consent <run>/consent.json [--home ~]

Reads only timestamps, never content, and only from consented sources:
  activity        digest/activity-prompts.jsonl from extract.py (when you wrote to an agent,
                  how fast you answered, whether it was a short decision)   [always, if present]
  mac-activity    `pmset -g log`: display on/off, sleep and wake (no special access)
  git-activity    commit times of your own commits in local repositories (author e-mail from
                  your git config, used to filter and never written out)
  screen-time     app focus time per app from macOS Screen Time (knowledgeC), app names only;
                  needs Full Disk Access for the terminal app, otherwise it is skipped

Writes <run>/day.json (dayprint.day/0.1): the typical start and end of a working day,
active hours per hour of the day and per weekday, deep-work blocks, the tempo (how often and how
fast you answer agents, how long agents wait for you), app time by category, and per-day rows.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics as st
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GENERATOR, is_secret_path, now_iso, read_json, write_json  # noqa: E402

DAY_CUT = 5          # a working day runs from 05:00 to 04:59, so late nights count to the day before
GAP_MIN = 45         # a gap longer than this ends a working stretch
APP_CATS = [
    (r"anthropic|claude", "AI assistants"), (r"openai|chatgpt|codex|cursor|perplexity|copilot", "AI assistants"),
    (r"terminal|iterm|warp|ghostty|vscode|visualstudio|xcode|jetbrains|sublime|zed\b|nova", "Code and terminal"),
    (r"chrome|safari|firefox|arc|brave|edge|opera|vivaldi", "Browser"),
    (r"slack|whatsapp|telegram|signal|ichat|messages|teams|discord|zoom|meet|facetime|webex", "Chat and calls"),
    (r"mail|outlook|spark|airmail|superhuman", "Mail"), (r"ical|calendar|fantastical|cron", "Calendar"),
    (r"notion|obsidian|bear|craft|notes|evernote|logseq|pages|word|docs", "Notes and documents"),
    (r"figma|paper|affinity|canva|sketch|photoshop|illustrator|pixelmator|blender|finalcut|davinci|capcut", "Design and media"),
    (r"excel|numbers|sheets|tradingview", "Numbers"), (r"spotify|music|tv\b|podcasts|steam|minecraft", "Leisure"),
    (r"finder|systempreferences|systemsettings|activitymonitor", "System"),
]


def local(ts: int) -> datetime:
    return datetime.fromtimestamp(ts)              # the machine's own time zone


def work_day(dt: datetime) -> str:
    return (dt - timedelta(hours=DAY_CUT)).date().isoformat()


def category(bundle: str) -> str:
    low = bundle.lower()
    for rx, name in APP_CATS:
        if re.search(rx, low):
            return name
    return "Other"


GENERIC_PARTS = {"com", "org", "net", "io", "co", "de", "app", "apps", "mac", "macos", "desktop", "helper", "agent"}


def _looks_like_id(part: str) -> bool:      # team ids and build hashes such as 2601167VJW8XE
    return len(part) >= 8 and bool(re.search(r"\d", part)) and bool(re.search(r"[a-z]", part, re.I)) and part.isalnum()


def app_name(bundle: str) -> str:
    """Readable app name from a bundle id: com.anthropic.claudefordesktop -> Claude, com.google.Chrome -> Chrome."""
    parts = [p for p in re.split(r"[.\-_]", bundle) if p and p.lower() not in GENERIC_PARTS and not _looks_like_id(p)]
    if not parts:
        return "Unidentified app"
    last = parts[-1] if len(parts[-1]) > 2 or len(parts) == 1 else f"{parts[-2]} {parts[-1]}"   # ai.example.to -> "Example to"
    name = re.sub(r"(fordesktop|formac|desktop|mac|app)$", "", last, flags=re.I) or last
    return name[0].upper() + name[1:] if name.islower() else name


def merge_spans(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


# ------------------------------------------------------------------ sources
def read_moments(run: Path, since: float) -> list[dict]:
    f = run / "digest" / "activity-prompts.jsonl"
    if not f.exists():
        return []
    return [m for m in (json.loads(x) for x in f.read_text().splitlines() if x.strip()) if m["t"] >= since]


def read_pmset(since: float) -> list[tuple[int, int]]:
    """Display-on intervals from the power log (the Mac was in front of someone)."""
    try:
        out = subprocess.run(["pmset", "-g", "log"], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    on, spans = None, []
    for line in out.splitlines():
        m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) [+-]\d{4} (\w+)\s+(.*)$", line)
        if not m:
            continue
        ts = int(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp())
        kind, rest = m.group(2), m.group(3)
        if (kind == "Notification" and "Display is turned on" in rest) or kind == "Wake":
            on = on or ts
        elif (kind == "Notification" and "Display is turned off" in rest) or kind == "Sleep":
            if on and ts - on > 60 and ts >= since:
                spans.append((max(on, int(since)), ts))
            on = None
    return spans


def find_repos(home: Path, roots=("Documents", "Desktop", "Developer", "code", "Code", "Projects", "projects", "src", "dev", "repos", "GitHub")) -> list[Path]:
    repos = []
    for r in roots:
        base = home / r
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            d = Path(dirpath)
            if len(d.parts) - len(base.parts) > 4:
                dirnames[:] = []
                continue
            if ".git" in dirnames or ".git" in filenames:
                repos.append(d)
                dirnames[:] = []
                continue
            dirnames[:] = [n for n in dirnames if not n.startswith(".") and n not in ("node_modules", "Library") and not is_secret_path(d / n)]
    return repos


def read_git(home: Path, since: float) -> tuple[list[int], int]:
    try:
        email = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True, timeout=10).stdout.strip()
    except OSError:
        return [], 0
    seen, times = set(), []
    repos = find_repos(home)
    for repo in repos:
        args = ["git", "-C", str(repo), "log", "--all", f"--since={int(since)}", "--format=%H %at"]
        if email:
            args.insert(5, f"--author={email}")
        try:
            out = subprocess.run(args, capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in out.splitlines():
            h, _, t = line.partition(" ")
            if h and h not in seen and t.isdigit():
                seen.add(h)
                times.append(int(t))
    return sorted(times), len(repos)


def read_screen_time(home: Path, since: float) -> tuple[list[tuple[str, int, int]], str]:
    db = home / "Library/Application Support/Knowledge/knowledgeC.db"
    if not db.exists():
        return [], "not found"
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
        q = ("SELECT ZOBJECT.ZVALUESTRING, ZOBJECT.ZSTARTDATE, ZOBJECT.ZENDDATE FROM ZOBJECT {join} "
             "WHERE ZOBJECT.ZSTREAMNAME = '/app/usage' AND ZOBJECT.ZSTARTDATE > ? {local}")
        try:   # this Mac only: Screen Time also stores usage synced from the person's phone and other Macs
            rows = con.execute(q.format(join="LEFT JOIN ZSOURCE ON ZOBJECT.ZSOURCE = ZSOURCE.Z_PK",
                                        local="AND ZSOURCE.ZDEVICEID IS NULL"), (since - 978307200,)).fetchall()
        except sqlite3.OperationalError:
            rows = con.execute(q.format(join="", local=""), (since - 978307200,)).fetchall()
        con.close()
    except sqlite3.Error as e:
        return [], "needs Full Disk Access" if "unable to open" in str(e) or "authorization" in str(e).lower() else f"unreadable ({type(e).__name__})"
    out = [(b, int(s + 978307200), int(e + 978307200)) for b, s, e in rows if b and s and e and e > s]
    return out, "read" if out else "empty (newer macOS keeps app usage elsewhere)"


# ------------------------------------------------------------------ model
def minutes_by_hour(spans):
    """{work_day: Counter(hour -> active minutes)} from (start, end) epoch spans."""
    days = defaultdict(Counter)
    for a, b in spans:
        t = a
        while t < b:
            dt = local(t)
            nxt = int((dt.replace(minute=0, second=0) + timedelta(hours=1)).timestamp())
            end = min(b, nxt)
            days[work_day(dt)][dt.hour] += (end - t) / 60
            t = end
    return days


def prompt_spans(moments):
    """Working stretches from prompt times: consecutive prompts less than GAP_MIN apart."""
    spans, start, last = [], None, None
    for m in moments:
        if last is None or m["t"] - last > GAP_MIN * 60:
            if start is not None:
                spans.append((start, last + 300))
            start = m["t"]
        last = m["t"]
    if start is not None:
        spans.append((start, last + 300))
    return spans


def hhmm(minutes_after_cut: float) -> str:
    m = int(round(minutes_after_cut)) + DAY_CUT * 60
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def build(moments, display, commits, screen, sources, n_repos):
    msg_days = minutes_by_hour(prompt_spans(moments))
    # Best signal first: app focus from Screen Time, then display on/off for days Screen Time does not cover.
    screen_spans = merge_spans([(s, e) for _, s, e in screen])
    screen_days = {work_day(local(a)) for a, _ in screen_spans}
    base = screen_spans + [sp for sp in display if work_day(local(sp[0])) not in screen_days]
    by_day = minutes_by_hour(base) if base else defaultdict(Counter)
    # A screen can stay on, and an app in focus, while nobody is there (agents running, video). Count that time
    # only in hours next to a sign of the person: a message, a commit or an app switch in that hour or the one beside it.
    human = defaultdict(set)
    for t in [m["t"] for m in moments] + list(commits) + [s for _, s, _ in screen]:
        dt = local(t)
        human[work_day(dt)].add(dt.hour)
    if base and human:
        for d in list(by_day):
            hs = human.get(d, set())
            for h in list(by_day[d]):
                if not ({h, (h - 1) % 24, (h + 1) % 24} & hs):
                    by_day[d][h] = 0
    for d, v in msg_days.items():              # days the power log does not cover fall back to message times
        if d not in by_day:
            by_day[d] = v
    active = base + [sp for sp in prompt_spans(moments) if work_day(local(sp[0])) not in {work_day(local(a)) for a, _ in base}]
    pr_day = defaultdict(Counter)
    for m in moments:
        dt = local(m["t"])
        pr_day[work_day(dt)][dt.hour] += 1
    cm_day = defaultdict(Counter)
    for t in commits:
        dt = local(t)
        cm_day[work_day(dt)][dt.hour] += 1
    days = sorted(set(by_day) | set(pr_day))
    if not days:
        return None
    # typical start and end (minutes after the 05:00 cut), from all activity
    firsts, lasts, actives = [], [], []
    for d in days:
        pts = [local(m["t"]) for m in moments if work_day(local(m["t"])) == d] + \
              [local(a) for a, b in active if work_day(local(a)) == d] + [local(b) for a, b in active if work_day(local(a)) == d]
        if not pts:
            continue
        base = datetime.fromisoformat(d) + timedelta(hours=DAY_CUT)
        firsts.append((min(pts) - base).total_seconds() / 60)
        lasts.append((max(pts) - base).total_seconds() / 60)
        actives.append(sum(by_day[d].values()) / 60)
    n = len(days)
    hours = []
    for h in list(range(DAY_CUT, 24)) + list(range(0, DAY_CUT)):
        hours.append({"hour": h,
                      "active_share": round(sum(1 for d in days if by_day[d][h] >= 10) / n, 2),
                      "active_minutes": round(sum(by_day[d][h] for d in days) / n, 1),
                      "prompts": round(sum(pr_day[d][h] for d in days) / n, 1),
                      "commits": round(sum(cm_day[d][h] for d in days) / n, 2)})
    weekday = defaultdict(list)
    for d in days:
        weekday[datetime.fromisoformat(d).strftime("%a")].append(sum(by_day[d].values()) / 60)
    # deep-work blocks: stretches of 60+ minutes with no more than one agent message per 20 minutes
    blocks = []
    for a, b in active:
        if b - a >= 3600:
            n_msgs = sum(1 for m in moments if a <= m["t"] <= b)
            if n_msgs <= (b - a) / 1200:
                blocks.append((a, b))
    # tempo
    replies = sorted(m["reply_s"] for m in moments if m.get("reply_s"))
    pdays = sorted({work_day(local(m["t"])) for m in moments})
    per_day = [sum(1 for m in moments if work_day(local(m["t"])) == d) for d in pdays]
    dec = sum(1 for m in moments if m["decision"])
    act_hours = sum(sum(by_day[d].values()) for d in pdays) / 60 or 1
    waits = [min(m["reply_s"], 1800) for m in moments if m.get("reply_s")]   # longer gaps are breaks, not waiting
    tempo = None
    if moments:
        tempo = {"messages_per_day": round(st.median(per_day), 0) if per_day else 0,
                 "messages_per_active_hour": round(len(moments) / act_hours, 1),
                 "decision_share": round(dec / len(moments), 2),
                 "decisions_per_day": round(dec / max(len(pdays), 1), 0),
                 "reply_median_s": int(st.median(replies)) if replies else None,
                 "reply_p25_s": int(replies[len(replies) // 4]) if replies else None,
                 "reply_p75_s": int(replies[3 * len(replies) // 4]) if replies else None,
                 "agents_wait_hours_per_day": round(sum(waits) / 3600 / max(len(pdays), 1), 1),
                 "answered_within_2_min": round(sum(1 for r in replies if r <= 120) / len(replies), 2) if replies else None,
                 # of the answers where we can tell: did an agent sit idle until this answer came?
                 "blocking_share": (lambda k: round(sum(1 for m in k if m["blocking"]) / len(k), 2) if k else None)(
                     [m for m in moments if m.get("blocking") is not None])}
    apps = None
    if screen:
        cat, per_app = Counter(), Counter()
        for b, s, e in screen:
            cat[category(b)] += (e - s) / 3600
            per_app[app_name(b)] += (e - s) / 3600
        sd = max(len({work_day(local(s)) for _, s, _ in screen}), 1)
        apps = {"hours_per_day_by_category": {k: round(v / sd, 1) for k, v in cat.most_common()},
                "top_apps_hours_per_day": {k: round(v / sd, 1) for k, v in per_app.most_common(10)}}
    rows = []
    for d in days[-21:]:
        pts = sorted(h for h, v in by_day[d].items() if v >= 5)
        rows.append({"day": d, "weekday": datetime.fromisoformat(d).strftime("%a"), "active_hours": round(sum(by_day[d].values()) / 60, 1),
                     "messages": sum(pr_day[d].values()), "commits": sum(cm_day[d].values())})
    return {
        "schema": "dayprint.day/0.1", "generator": GENERATOR, "generated_at": now_iso(),
        "sources": sources, "repos_scanned": n_repos, "days_observed": n,
        "typical": {"start": hhmm(st.median(firsts)) if firsts else None, "end": hhmm(st.median(lasts)) if lasts else None,
                    "active_hours": round(st.median(actives), 1) if actives else None,
                    "late_nights_share": round(sum(1 for x in lasts if x > (24 - DAY_CUT) * 60 - 0) / len(lasts), 2) if lasts else None},
        "hours": hours,
        "weekdays": {k: round(st.median(v), 1) for k, v in weekday.items()},
        "deep_blocks_per_day": round(len(blocks) / n, 1),
        "tempo": tempo, "apps": apps, "per_day": rows,
        "basis": "screen time" if screen else "display on/off" if display else "message times",
        "display_days": len({work_day(local(a)) for a, _ in display}),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--consent", required=True)
    ap.add_argument("--home", default=str(Path.home()))
    a = ap.parse_args()
    run, home = Path(a.run).expanduser(), Path(a.home).expanduser()
    consent = read_json(a.consent)
    allow = {k for k, v in (consent.get("sources") or {}).items() if v is True}
    days = consent.get("since_days") or 180
    since = (datetime.now() - timedelta(days=days)).timestamp()
    sources = {}
    moments = read_moments(run, since)
    sources["activity"] = {"read": bool(moments), "items": len(moments)}
    own_mac = sys.platform == "darwin" and home.resolve() == Path.home().resolve()   # the power log belongs to this Mac's own user
    display = read_pmset(since) if "mac-activity" in allow and own_mac else []
    sources["mac-activity"] = {"read": "mac-activity" in allow, "items": len(display)}
    commits, n_repos = read_git(home, since) if "git-activity" in allow else ([], 0)
    sources["git-activity"] = {"read": "git-activity" in allow, "items": len(commits)}
    screen, status = read_screen_time(home, since) if "screen-time" in allow else ([], "not consented")
    sources["screen-time"] = {"read": bool(screen), "items": len(screen), "status": status}
    day = build(moments, display, commits, screen, sources, n_repos)
    if not day:
        print("not enough activity to reconstruct a day")
        sys.exit(1)
    write_json(run / "day.json", day)
    log_path = run / "read-log.json"          # the timing sources are read here, not by extract.py: record what was read
    if log_path.exists():
        log = read_json(log_path)
        for e in log.get("sources", []):
            if e.get("id") in ("mac-activity", "git-activity", "screen-time") and e["id"] in sources:
                v = sources[e["id"]]
                e.pop("note", None)
                e.update(read=bool(v["items"]), items=v["items"])
                if not v["items"] and v.get("status"):
                    e["note"] = v["status"]
        write_json(log_path, log)
    t = day["typical"]
    print(f"{day['days_observed']} days · start {t['start']} · end {t['end']} · {t['active_hours']} active h · basis {day['basis']}")
    if day["tempo"]:
        print("tempo:", json.dumps(day["tempo"]))
    for k, v in sources.items():
        print(f"{k:13} {v}")


if __name__ == "__main__":
    main()
