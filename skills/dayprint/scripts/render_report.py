#!/usr/bin/env python3
"""Render the onboarding report and the portable agent cards.

  python3 render_report.py --findings findings.json --setup cavion-workspace.json \
      --read-log read-log.json --plan apply-plan.json --out dayprint-report.html

Writes the report (one self-contained HTML file) and agent-cards.md next to it.
The look lives in assets/report/elements.html: one <template> per element, matching the
el/* layers of the Paper board OR02. This script only chooses elements and fills their slots,
so every report is built from the same elements with the person's own data.
Offline: Inter, the Cavion mark, Lucide glyphs and real product logos are embedded.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_json  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
GLYPHS = json.loads((ASSETS / "lucide-icons.json").read_text())["icons"]
LOGOS = json.loads((ASSETS / "logos" / "index.json").read_text())["icons"]
SOURCE = (ASSETS / "report" / "elements.html").read_text(encoding="utf-8")
TEMPLATES = dict(re.findall(r'<template id="el-([a-z-]+)">(.*?)</template>', SOURCE, flags=re.S))
CSS = re.search(r'<style id="report-css">.*?</style>', SOURCE, flags=re.S).group(0)

NUM = {"en": "zero one two three four five six seven eight nine ten eleven twelve".split(),
       "de": "null ein zwei drei vier fünf sechs sieben acht neun zehn elf zwölf".split()}
L = {
    "en": {"plan_for": "Workspace plan for {who}, {date}", "week": "Your repeated week", "agent_can": "An agent can draft it",
           "stays": "Stays with you", "days": {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday",
           "sat": "Saturday", "sun": "Sunday", "month": "1st of the month", "any": "Any day"},
           "jobs": "{n} jobs an agent can take, the biggest first", "job_one": "One job an agent can take",
           "jobs_note": "Each one shows how it runs in Cavion, how to set it up in tools you already have, and the instructions to give any agent.",
           "hours": "{h} hours a week", "in_cavion": "In Cavion", "own": "In tools you already have", "instr": "Instructions for any agent",
           "you": "You review and send", "you_short": "You approve",
           "ws_title": "The workspace that takes these jobs", "ws_note": "Everything starts paused. Sending, deleting and sharing always ask you first.",
           "assistant": "Your assistant", "only_you": "Only you see it.", "open": "Open", "members_only": "Members only",
           "manager": "manager", "specialist": "specialist", "every": "every", "min": "min", "checked": "new items, checked every {m} min",
           "start": "Start with these", "start_note": "Each takes under an hour to set up and pays back in its first week.",
           "setup": "Set it up", "in_cavion_text": "The whole workspace is in one file. Paste its {n} short setup messages into your Cavion assistant and approve each one. Once Cavion reads the file directly, it is one step.",
           "any_agent": "With any other agent", "any_text": "Every job above has its instructions, trigger, tools and the step you approve. They work in ChatGPT or Claude projects, custom GPTs, n8n and Zapier.",
           "hours_title": "Where the hours come from", "hours_note": "Times a month, minutes each time, and the part an agent takes over. The rest stays with you.",
           "job": "Job", "a_month": "a month", "minutes": "minutes", "part": "agent part", "a_week": "a week", "all_jobs": "All {n} jobs",
           "read": "What was read", "read_note": "{depth}, {span}. On this computer only.", "never": "Never opened",
           "secrets": "keys, passwords, .env", "left_out": "Left out", "private": "{n} private topics",
           "basis": "Based on {list}{span}. Read on this computer. Nothing was uploaded, and names and contact details were removed first.",
           "from_to": " from {a} to {b}", "and": "and", "sessions": "{n} Claude Code and Codex sessions", "cta": "Run this workspace in Cavion:",
           "made": "Made with Dayprint, an open-source skill by Cavion. Product names and logos are trademarks of their owners.",
           "depth": {"quick": "Quick look", "standard": "Standard look", "deep": "Deep look"}, "weekdays": "Weekdays",
           "how": "How you work", "how_note": "From the times your Mac was on, when you wrote to agents and when you committed. No content.",
           "how_note_msgs": "From the times you wrote to agents. No content.",
           "how_note_screen": "From Screen Time, when you wrote to agents and when you committed. App names only, no content.",
           "used": "Mac in use", "msgs": "Messages to agents", "told": "What you told us", "inferred": "What the data shows", "keep": "Must not get slower: {x}",
           "f_start": "is when your day usually starts. It ends around {end}{late}.", "f_late": ", after midnight on most days",
           "f_reply": "is how long you usually take to answer an agent. {share} in 10 answers come within two minutes.",
           "f_wait": "a day, in total, your agents wait for you.", "f_msgs": "messages a day to your agents; {dec} in ten are short decisions.",
           "f_apps": "a day in {cat}, your biggest app category.",
           "fit": {"faster": "Faster for you.", "same": "Same pace.", "slower": "Slower, on purpose."},
           "dropped": "Left out after the check",
           "months": "January February March April May June July August September October November December".split(),
           "src": {"chatgpt-export": "{n} ChatGPT chats", "claude-export": "{n} Claude chats", "calendar-files": "your calendar",
                   "documents": "your files", "shell-history": "your terminal history"},
           "src_rows": {"chatgpt-export": "ChatGPT chats", "claude-export": "Claude chats and projects", "claude-code-transcripts": "Claude Code sessions",
                        "claude-code-history": "Claude Code prompts", "codex-sessions": "Codex sessions", "codex-history": "Codex prompts",
                        "claude-code-memory": "Claude memory notes", "codex-memory": "Codex instructions", "calendar-files": "Calendar events",
                        "documents": "Files", "shell-history": "Terminal commands", "installed-apps": "Installed apps"}},
    "de": {"plan_for": "Workspace-Plan für {who}, {date}", "week": "Deine wiederkehrende Woche", "agent_can": "Kann ein Agent entwerfen",
           "stays": "Bleibt bei dir", "days": {"mon": "Montag", "tue": "Dienstag", "wed": "Mittwoch", "thu": "Donnerstag", "fri": "Freitag",
           "sat": "Samstag", "sun": "Sonntag", "month": "Am 1. des Monats", "any": "Jeder Tag"},
           "jobs": "{n} Aufgaben, die ein Agent übernehmen kann, die größte zuerst", "job_one": "Eine Aufgabe, die ein Agent übernehmen kann",
           "jobs_note": "Zu jeder: wie sie in Cavion läuft, wie du sie mit deinen Tools einrichtest, und die Anweisungen für jeden Agenten.",
           "hours": "{h} Stunden pro Woche", "in_cavion": "In Cavion", "own": "Mit deinen Tools", "instr": "Anweisungen für jeden Agenten",
           "you": "Du prüfst und sendest", "you_short": "Du gibst frei",
           "ws_title": "Der Workspace für diese Aufgaben", "ws_note": "Alles startet pausiert. Senden, Löschen und Teilen fragen immer vorher.",
           "assistant": "Dein Assistent", "only_you": "Nur du siehst ihn.", "open": "Offen", "members_only": "Nur Mitglieder",
           "manager": "Manager", "specialist": "Spezialist", "every": "alle", "min": "Min.", "checked": "Neues, alle {m} Min. geprüft",
           "start": "Fang hiermit an", "start_note": "Jedes ist in unter einer Stunde eingerichtet und zahlt sich in der ersten Woche aus.",
           "setup": "Einrichten", "in_cavion_text": "Der ganze Workspace steckt in einer Datei. Füge ihre {n} kurzen Einrichtungsnachrichten in deinen Cavion-Assistenten ein und bestätige jede. Sobald Cavion die Datei direkt liest, ist es ein Schritt.",
           "any_agent": "Mit jedem anderen Agenten", "any_text": "Jede Aufgabe oben hat Anweisungen, Auslöser, Tools und den Schritt, den du freigibst. Das funktioniert in ChatGPT- und Claude-Projekten, Custom GPTs, n8n und Zapier.",
           "hours_title": "Woher die Stunden kommen", "hours_note": "Häufigkeit im Monat, Minuten pro Mal und der Teil, den ein Agent übernimmt. Der Rest bleibt bei dir.",
           "job": "Aufgabe", "a_month": "pro Monat", "minutes": "Minuten", "part": "Agent-Anteil", "a_week": "pro Woche", "all_jobs": "Alle {n} Aufgaben",
           "read": "Was gelesen wurde", "read_note": "{depth}, {span}. Nur auf diesem Computer.", "never": "Nie geöffnet",
           "secrets": "Schlüssel, Passwörter, .env", "left_out": "Weggelassen", "private": "{n} private Themen",
           "basis": "Grundlage: {list}{span}. Auf diesem Computer gelesen. Nichts wurde hochgeladen, Namen und Kontaktdaten wurden vorher entfernt.",
           "from_to": " von {a} bis {b}", "and": "und", "sessions": "{n} Claude-Code- und Codex-Sitzungen", "cta": "Diesen Workspace in Cavion nutzen:",
           "made": "Erstellt mit dem Open-Source-Skill Dayprint. Produktnamen und Logos sind Marken ihrer Inhaber.",
           "depth": {"quick": "Kurzer Blick", "standard": "Normaler Blick", "deep": "Tiefer Blick"}, "weekdays": "Werktags",
           "how": "Wie du arbeitest", "how_note": "Aus den Zeiten, in denen dein Mac an war, du Agenten geschrieben und committet hast. Ohne Inhalte.",
           "how_note_msgs": "Aus den Zeiten, in denen du Agenten geschrieben hast. Ohne Inhalte.",
           "how_note_screen": "Aus Bildschirmzeit, den Zeiten, in denen du Agenten geschrieben und committet hast. Nur App-Namen, ohne Inhalte.",
           "used": "Mac in Benutzung", "msgs": "Nachrichten an Agenten", "told": "Was du uns gesagt hast", "inferred": "Was die Daten zeigen", "keep": "Darf nicht langsamer werden: {x}",
           "f_start": "beginnt dein Tag meist. Er endet gegen {end}{late}.", "f_late": ", an den meisten Tagen nach Mitternacht",
           "f_reply": "brauchst du meist, um einem Agenten zu antworten. {share} von 10 Antworten kommen innerhalb von zwei Minuten.",
           "f_wait": "am Tag warten deine Agenten insgesamt auf dich.", "f_msgs": "Nachrichten am Tag an deine Agenten; {dec} von zehn sind kurze Entscheidungen.",
           "f_apps": "am Tag in {cat}, deiner größten App-Kategorie.",
           "fit": {"faster": "Schneller für dich.", "same": "Gleiches Tempo.", "slower": "Bewusst langsamer."},
           "dropped": "Nach der Prüfung weggelassen",
           "months": "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split(),
           "src": {"chatgpt-export": "{n} ChatGPT-Chats", "claude-export": "{n} Claude-Chats", "calendar-files": "dein Kalender",
                   "documents": "deine Dateien", "shell-history": "dein Terminal-Verlauf"},
           "src_rows": {"chatgpt-export": "ChatGPT-Chats", "claude-export": "Claude-Chats und Projekte", "claude-code-transcripts": "Claude-Code-Sitzungen",
                        "claude-code-history": "Claude-Code-Prompts", "codex-sessions": "Codex-Sitzungen", "codex-history": "Codex-Prompts",
                        "claude-code-memory": "Claude-Gedächtnisnotizen", "codex-memory": "Codex-Anweisungen", "calendar-files": "Kalendertermine",
                        "documents": "Dateien", "shell-history": "Terminal-Befehle", "installed-apps": "Installierte Apps"}},
}
SPACE_COLOURS = {"red": "#E5484D", "orange": "#F76B15", "yellow": "#E9B500", "green": "#30A46C", "teal": "#12A594",
                 "blue": "#3B8EEA", "indigo": "#3E63DD", "purple": "#8E4EC6", "pink": "#D6409F", "brown": "#A07553"}
DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun", "month", "any"]
SHORT_DAYS = {"en": ["", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"],
              "de": ["", "Montags", "Dienstags", "Mittwochs", "Donnerstags", "Freitags", "Samstags", "Sonntags"]}


def el(_element: str, **slots) -> str:
    """Fill one element: {{x}} gets escaped text, {{{x}}} gets HTML."""
    out = TEMPLATES[_element]
    out = re.sub(r"\{\{\{(\w+)\}\}\}", lambda m: str(slots.get(m.group(1), "")), out)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: html.escape(str(slots.get(m.group(1), ""))), out)


def glyph(name, size=18):
    return f'<svg class="ic" style="width:{size}px;height:{size}px" viewBox="0 0 24 24" aria-hidden="true">{GLYPHS[name]}</svg>'


_logo_cache: dict[str, str] = {}


def logo(key, size=16):
    """A real product logo as an <img> with an embedded SVG (no id clashes, no network)."""
    if not key or key not in LOGOS:
        return ""
    if key not in _logo_cache:
        _logo_cache[key] = base64.b64encode((ASSETS / "logos" / f"{key}.svg").read_bytes()).decode()
    return (f'<img class="logo" src="data:image/svg+xml;base64,{_logo_cache[key]}" alt="{html.escape(LOGOS[key]["name"])}" '
            f'style="width:{size}px;height:{size}px">')


def find_logo(text):
    """The logo whose product name appears in a tool name ('Task board (Notion)' -> notion)."""
    low = (text or "").lower()
    best = None
    for key, meta in LOGOS.items():
        for name in {meta["name"].lower(), key.replace("-", " ")}:
            if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low):
                if best is None or len(name) > len(LOGOS[best]["name"]):
                    best = key
    return best


def num(v, lang):
    return (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", "," if lang == "de" else ".")


def count(n, lang):                       # 10125 -> 10,125 (10.125 in German)
    return f"{int(n or 0):,}".replace(",", "." if lang == "de" else ",")


def hours(lo, hi, lang, dash=False):
    if round(lo, 1) == round(hi, 1):
        return num(lo, lang)
    return f"{num(lo, lang)}–{num(hi, lang)}" if dash else f"{num(lo, lang)}{' bis ' if lang == 'de' else ' to '}{num(hi, lang)}"


def sentences(steps):
    return " ".join(s.strip() if s.strip().endswith((".", "!", "?")) else s.strip() + "." for s in steps)


def when(t, lang, T):
    if t.get("human"):
        return t["human"]
    if t["kind"] == "once":
        return f"{t['date']}, {t['time']}"
    if t["kind"] == "weekly":
        d = T["weekdays"] if t["weekdays"] == [1, 2, 3, 4, 5] else ", ".join(SHORT_DAYS[lang][x] for x in t["weekdays"])
        return f"{d} {', '.join(t['times'])}"
    return f"{T['every']} {t['minutes']} {T['min']}"


def join_list(items, T):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" {T['and']} " + items[-1]


def how_section(day, f, lang, T):
    hrs = day.get("hours") or []
    mx_m = max([h["prompts"] for h in hrs] + [0.1])
    mx_a = max([h["active_minutes"] for h in hrs] + [1])
    strip = "".join(el("hr", a=int(h["active_minutes"] / mx_a * 100), m=int(h["prompts"] / mx_m * 92),
                       label=f"{h['hour']:02d}" if h["hour"] in (5, 8, 11, 14, 17, 20, 23, 2) else "") for h in hrs)
    facts = []
    t, tp = day.get("typical") or {}, day.get("tempo") or {}
    if t.get("start"):
        late = T["f_late"] if (t.get("late_nights_share") or 0) >= 0.5 else ""
        facts.append(el("fact", n=t["start"], text=T["f_start"].format(end=t.get("end"), late=late)))
    if tp.get("reply_median_s"):
        r_ = tp["reply_median_s"]
        n = f"{r_} s" if r_ < 120 else f"{round(r_ / 60)} min"
        facts.append(el("fact", n=n, text=T["f_reply"].format(share=round((tp.get("answered_within_2_min") or 0) * 10))))
    if tp.get("agents_wait_hours_per_day"):
        facts.append(el("fact", n=f"{num(tp['agents_wait_hours_per_day'], lang)} h", text=T["f_wait"]))
    elif tp.get("messages_per_day"):
        facts.append(el("fact", n=f"{int(tp['messages_per_day'])}", text=T["f_msgs"].format(dec=round(tp["decision_share"] * 10))))
    apps = (day.get("apps") or {}).get("hours_per_day_by_category") or {}
    if apps:
        cat, h = next(iter(apps.items()))
        facts.append(el("fact", n=f"{num(h, lang)} h", text=T["f_apps"].format(cat=cat)))
    wm = f.get("working_model") or {}
    rows = []
    asked = any(h["status"] in ("confirmed", "corrected") for h in wm.get("hypotheses", []))
    for h in wm.get("hypotheses", []):
        if h["status"] in ("confirmed", "corrected") or (not asked and h["status"] == "inferred"):
            rows.append(el("told-row", icon=glyph("check", 16), text=h.get("answer") if h["status"] == "corrected" and h.get("answer") else h["text"]))
    for x in wm.get("must_not_slow", [])[:2]:
        rows.append(el("told-row", cls="keep", icon=glyph("lock", 16), text=T["keep"].format(x=x)))
    told = el("told", title=T["told"] if asked else T["inferred"], rows="".join(rows)) if rows else ""
    basis = day.get("basis")
    note = T["how_note_screen"] if basis == "screen time" else T["how_note"] if basis == "display on/off" else T["how_note_msgs"]
    return el("side-sec", title=T["how"], note=note,
              body=el("how", used_label=T["used"] if basis in ("display on/off", "screen time") else T["msgs"], msg_label=T["msgs"],
                      hours=strip, facts="".join(facts), told=told))


def render(f, s, log, plan, stats=None, day=None) -> str:
    lang = f.get("language", "en")[:2]
    lang = lang if lang in L else "en"
    T = L[lang]
    flows = sorted(f["workflows"], key=lambda w: -w["saving"]["hours_per_week_high"])
    lo = sum(w["saving"]["hours_per_week_low"] for w in flows)
    hi = sum(w["saving"]["hours_per_week_high"] for w in flows)
    live = lambda o: o.get("status") != "skipped"  # noqa: E731
    agents = {a["key"]: a for a in s["agents"] if live(a)}
    conns = {c["key"]: c for c in s["connections"] if live(c)}
    read = {x["id"]: x for x in log["sources"] if x.get("read")}
    sp = (stats or {}).get("data_span")
    a_month = T["months"][int(sp["first"][5:7]) - 1] if sp else ""
    b_month = T["months"][int(sp["last"][5:7]) - 1] if sp else ""
    mark_svg = (ASSETS / "cavion-mark.svg").read_text()
    mark = mark_svg.replace("<svg ", '<svg class="mark" aria-label="Cavion" role="img" ', 1)
    mark_white = mark_svg.replace("<svg ", '<svg style="width:18px;height:16px" aria-hidden="true" ', 1).replace('fill="#090909"', 'fill="#FFFFFF"')
    body = []

    who = f["person"].get("short") or f["person"]["organisation"]
    today = date.today()
    body.append(el("header", mark=mark, meta=T["plan_for"].format(who=who, date=f"{today.day} {T['months'][today.month - 1]} {today.year}")))

    # hero: one sentence with the hours inside it
    head = html.escape(f["headline"])
    head = re.sub(r"(\d+(?:[.,]\d+)?\s*(?:to|bis|–|-)\s*\d+(?:[.,]\d+)?\s*(?:hours|Stunden|h)\b)", r"<em>\1</em>", head, count=1)
    counts = [T["src"][k].format(n=read[k]["items"]) for k in ("chatgpt-export", "claude-export") if k in read and read[k].get("items")]
    sess = sum(read[k]["items"] for k in ("claude-code-transcripts", "codex-sessions") if k in read)
    if sess:
        counts.append(T["sessions"].format(n=sess))
    counts += [T["src"][k] for k in ("calendar-files", "documents", "shell-history") if k in read]
    if not counts:
        counts = [T["src_rows"].get(k, v["label"]) for k, v in read.items()][:3]
    basis = T["basis"].format(list=join_list(counts, T) if counts else "—", span=T["from_to"].format(a=a_month, b=b_month) if sp else "")
    body.append(el("hero", headline=head, basis=basis))

    # the repeated week
    week = f.get("week") or []
    if week:
        cols = []
        for d in DAY_ORDER:
            slots = [x for x in week if x["day"] == d]
            if not slots and d not in ("mon", "tue", "wed", "thu", "fri"):
                continue
            inner = "".join(el("slot", cls="" if x["agent"] else "still", h=int(min(140, max(52, 34 + x["minutes"] * 0.65))),
                               title=x["title"], minutes=f"{x['minutes']} {T['min']}", logo=logo(x.get("logo"), 14)) for x in slots)
            cols.append(el("day", cls="month" if d == "month" else "", name=T["days"][d], slots=inner))
        body.append(el("week", title=T["week"], agent_label=T["agent_can"], still_label=T["stays"], days="".join(cols)))
    if day and day.get("hours"):
        body.append(how_section(day, f, lang, T))

    # the jobs
    n = len(flows)
    word = NUM[lang][n] if n < len(NUM[lang]) else str(n)
    body.append(el("section-head", title=T["jobs"].format(n=word[:1].upper() + word[1:]) if n > 1 else T["job_one"], note=T["jobs_note"]))
    fid = {x["id"]: x for x in f["findings"]}
    for w in flows:
        c = w.get("agent_card") or {}
        trig = c.get("trigger", {})
        t_icon = logo(trig.get("logo"), 20) or {"schedule": glyph("calendar-clock"), "new_item": glyph("inbox"),
                                                 "on_request": glyph("hand")}.get(trig.get("type"), glyph("zap"))
        cav_agent = next((agents[k] for k in w["with_cavion"]["setup_keys"] if k in agents), None)
        agent_label = (cav_agent["name"] + (" " + T["manager"] if cav_agent["kind"] == "space_manager" else "")
                       if cav_agent and cav_agent["kind"] != "personal_assistant" else T["assistant"] if cav_agent else c.get("name") or w["title"])
        nodes = [el("node", icon=t_icon, label=trig.get("when") or w["trigger"]),
                 el("node", cls="agent", icon=mark_white, label=agent_label)]
        tools = c.get("tools", [])
        out_key = next((find_logo(t["name"]) for t in tools if t["access"] in ("draft", "write") and find_logo(t["name"])), None)
        tool_logos = [k for k in dict.fromkeys(find_logo(t["name"]) for t in tools if t["access"] == "read") if k and k != out_key][:2]
        if tool_logos:
            names = [t["name"].split(" (")[0] for t in tools if find_logo(t["name"]) in tool_logos]
            nodes.append(el("node", icon="".join(logo(k, 16 if len(tool_logos) > 1 else 20) for k in tool_logos), label=", ".join(names[:2])))
        elif c.get("knowledge") or tools:
            names = c.get("knowledge") or [t["name"] for t in tools]
            label = names[0] if len(", ".join(names[:2])) > 30 else ", ".join(names[:2])
            nodes.append(el("node", icon=glyph("book-open"), label=label))
        nodes.append(el("node", icon=logo(out_key, 20) or glyph("file-text"), label=c.get("output") or ""))
        sends = any(x in (c.get("approval", "") + " " + w["with_cavion"]["steps"][-1]).lower() for x in ("send", "sende", "post"))
        nodes.append(el("node", cls="you", icon=glyph("user-round"), label=T["you"] if sends else T["you_short"]))
        ev = next((fid[k]["evidence"][0]["observation"] for k in w["findings"] if k in fid), "")
        body.append(el("workflow", title=w["title"],
                       saving=T["hours"].format(h=hours(w["saving"]["hours_per_week_low"], w["saving"]["hours_per_week_high"], lang)),
                       evidence=ev[:1].upper() + ev[1:], flow=el("flow", nodes=el("link").join(nodes)),
                       fit=el("fit", icon=glyph("gauge", 16), label=T["fit"][w["fit"]["speed"]], note=w["fit"]["note"]) if w.get("fit") else "",
                       cavion_label=T["in_cavion"], cavion=sentences(w["with_cavion"]["steps"]),
                       own_label=T["own"], own=sentences(w["own_tools"]["steps"]),
                       instructions=el("instructions", label=T["instr"], text=c["instructions"]) if c.get("instructions") else ""))

    if f.get("dropped"):
        body.append(el("side-sec", title=T["dropped"], note="", body='<div class="rule-list">' +
                       "".join(el("dropped-row", title=x["title"], why=x["why"]) for x in f["dropped"]) + "</div>"))

    # the workspace band
    def app_tiles(keys, small=False):
        out = []
        for k in keys:
            c = conns.get(k)
            if not c:
                continue
            key = c["app"] if c["app"] in LOGOS else find_logo(c.get("label") or c["app"])
            lg = logo(key, 15)
            out.append(f'<div class="app{" s" if small else ""}">{lg}</div>' if lg
                       else f'<span class="app-name">{html.escape((c.get("label") or c["app"]).split(" (")[0])}</span>')
        return "".join(dict.fromkeys(out))
    assistant = ""
    for a in [a for a in agents.values() if a["kind"] == "personal_assistant"][:1]:
        assistant = el("assistant", icon=glyph("user-round"), name=T["assistant"], why=f"{a['why'].rstrip('.')}. {T['only_you']}", apps=app_tiles(a["apps"]))
    spaces = []
    for spc in [x for x in s["spaces"] if live(x)]:
        ags = sorted([a for a in agents.values() if a.get("space") == spc["key"]], key=lambda a: a["kind"] != "space_manager")
        rows = "".join(el("space-agent", name=a["name"] if a["kind"] != "space_manager" else f"{a['name']} {T['manager']}",
                          role="" if a["kind"] == "space_manager" else T["specialist"]) for a in ags)
        spaces.append(el("space", colour=SPACE_COLOURS.get(spc.get("colour", "blue"), "#3B8EEA"), name=spc["name"],
                         access=T["open"] if spc["agent_access"] == "open" else T["members_only"],
                         purpose=spc["purpose"].split(". ")[0].rstrip(".") + ".", agents=rows,
                         apps=app_tiles(list(dict.fromkeys(c for a in ags for c in a["apps"])), True)))
    aname = lambda k: (lambda a: (a["name"] + (" " + T["manager"] if a["kind"] == "space_manager" else "")) if a["kind"] != "personal_assistant" else T["assistant"])(agents[k]) if k in agents else ""  # noqa: E731
    tt = [el("tt-row", when=when(t["timing"], lang, T), what=t["title"], agent=aname(t["agent"])) for t in s["scheduled_tasks"] if live(t)]
    tt += [el("tt-row", when=T["checked"].format(m=c["every_minutes"])[:1].upper() + T["checked"].format(m=c["every_minutes"])[1:], what=c["title"], agent=aname(c["agent"])) for c in s["checks"] if live(c)]
    body.append(el("workspace", title=T["ws_title"], note=T["ws_note"], assistant=assistant, spaces="".join(spaces), rows="".join(tt)))

    # start, set up, hours, read
    if f["quick_wins"]:
        body.append(el("side-sec", cls="first", title=T["start"], note=T["start_note"],
                       body='<div class="rule-list">' + "".join(el("next-row", title=q["title"], how=q["how"]) for q in f["quick_wins"][:5]) + "</div>"))
    n_batches = len(plan["batches"]) if plan else 0
    body.append(el("side-sec", title=T["setup"], note="", body=el("two", a_title=T["in_cavion"], a_text=T["in_cavion_text"].format(n=n_batches),
                   a_file="cavion-workspace.json", b_title=T["any_agent"], b_text=T["any_text"], b_file="agent-cards.md")))
    rows = "".join(el("ledger-row", job=w["title"], per_month=num(w["per_month"], lang), minutes=f"{w['minutes_each']:g}",
                      part=f"{w['saving']['share_low']:.0%}–{w['saving']['share_high']:.0%}",
                      week=hours(w["saving"]["hours_per_week_low"], w["saving"]["hours_per_week_high"], lang, dash=True) + " h") for w in flows)
    body.append(el("side-sec", title=T["hours_title"], note=T["hours_note"], body=el("ledger", job=T["job"], per_month=T["a_month"],
                   minutes=T["minutes"], part=T["part"], week=T["a_week"], rows=rows, total_label=T["all_jobs"].format(n=n),
                   total=hours(lo, hi, lang, dash=True) + " h")))
    order = list(T["src_rows"])
    rows_read = [el("read-row", label=T["src_rows"].get(k, v["label"]), value=count(v.get("items", v.get("files_read", 0)), lang))
                 for k, v in sorted(read.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99) if k != "installed-apps"]
    rows_read.append(el("read-row", label=T["never"], value=T["secrets"]))
    if f.get("not_used"):
        rows_read.append(el("read-row", label=T["left_out"], value=T["private"].format(n=len(f["not_used"]))))
    half = (len(rows_read) + 1) // 2
    depth = T["depth"][log.get("depth") or "standard"]
    note = T["read_note"].format(depth=depth, span=f"{a_month}–{b_month}" if sp else "").replace(", .", ".")
    body.append(el("side-sec", title=T["read"], note=note, body=el("read", left="".join(rows_read[:half]), right="".join(rows_read[half:]))))
    body.append(el("footer", mark=mark.replace('class="mark"', 'class="mark" style="height:14px"'), cta=T["cta"], made=T["made"]))

    font = base64.b64encode((ASSETS / "fonts" / "InterVariable.woff2").read_bytes()).decode()
    return el("page", lang=lang, title=f"Workspace plan · {who}", css=CSS.replace("{{{font}}}", font), body="".join(body))


def agent_cards_md(f) -> str:
    out = ["# Agent cards", "", "One agent per job found in your work. Each works in any agent tool: ChatGPT or Claude projects, custom GPTs, n8n, Zapier, or Cavion.", ""]
    for w in sorted(f["workflows"], key=lambda w: -w["saving"]["hours_per_week_high"]):
        c = w.get("agent_card")
        if not c:
            continue
        out += [f"## {c['name']}", "", c["role"], "", f"- **Starts:** {c['trigger']['type'].replace('_', ' ')}, {c['trigger']['when']}"]
        if c.get("inputs"):
            out.append(f"- **Reads:** {', '.join(c['inputs'])}")
        if c.get("tools"):
            out.append(f"- **Tools:** {', '.join(t['name'] + ' (' + t['access'] + ')' for t in c['tools'])}")
        if c.get("knowledge"):
            out.append(f"- **Needs:** {', '.join(c['knowledge'])}")
        out += [f"- **Delivers:** {c['output']}", f"- **You approve:** {c['approval']}",
                f"- **Saves:** {hours(w['saving']['hours_per_week_low'], w['saving']['hours_per_week_high'], 'en')} hours a week", "",
                "```text", c["instructions"], "```", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--read-log", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--stats", help="stats.json for the data period (default: next to the read log)")
    ap.add_argument("--day", help="day.json from rhythm.py (default: next to the read log)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    stats_path = Path(a.stats) if a.stats else Path(a.read_log).with_name("stats.json")
    f = read_json(a.findings)
    day_path = Path(a.day) if a.day else Path(a.read_log).with_name("day.json")
    doc = render(f, read_json(a.setup), read_json(a.read_log), read_json(a.plan) if a.plan else None,
                 read_json(stats_path) if stats_path.exists() else None, read_json(day_path) if day_path.exists() else None)
    out = Path(a.out)
    out.write_text(doc, encoding="utf-8")
    (out.parent / "agent-cards.md").write_text(agent_cards_md(f), encoding="utf-8")
    print(f"report written: {out} ({len(doc) // 1024} KB) + agent-cards.md")


if __name__ == "__main__":
    main()
