#!/usr/bin/env python3
"""Build the synthetic test persona's home folder (deterministic).

Lena Hoffmann is fictional: founder of "Studio Nordlicht", a three-person brand and
web studio in Hamburg. All people, companies, e-mail addresses, phone numbers,
IBANs and keys below are invented. Decoy secret files contain the marker
DECOY-SECRET-DO-NOT-READ so a test can prove they were never opened.

  python3 make_persona.py            # writes ./home next to this file
"""
from __future__ import annotations

import json
import random
import shutil
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE / "home"
R = random.Random(42)
TZ = timezone(timedelta(hours=1))
START = datetime(2026, 8, 3, tzinfo=TZ)      # Monday
END = datetime(2026, 11, 6, tzinfo=TZ)
DECOY = "DECOY-SECRET-DO-NOT-READ"

CLIENTS = ["Kaffeebar Ost", "Fahrradwerk Altona", "Praxis Weber Physio", "Elbe Yoga Loft"]
CONTACT = {"Kaffeebar Ost": "anna.berg@kaffeebar-ost.de", "Fahrradwerk Altona": "tom@fahrradwerk-altona.de",
           "Praxis Weber Physio": "info@praxis-weber.de", "Elbe Yoga Loft": "hello@elbeyogaloft.de"}


def uid():
    return str(uuid.UUID(int=R.getrandbits(128)))


def days(step=1):
    d = START
    while d <= END:
        yield d
        d += timedelta(days=step)


def at(d, h, m=0):
    return d.replace(hour=h, minute=m) + timedelta(minutes=R.randint(0, 20))


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- chat content
def status_notes(client):
    done = R.sample(["finished the menu page", "new photos are in", "contact form tested", "SEO titles done",
                     "mobile nav fixed", "booking widget connected", "hero animation approved", "copy round 2 in"], 2)
    nxt = R.sample(["final review on Tuesday", "launch next Thursday", "waiting for logo files", "need opening hours",
                    "staging link to share", "domain transfer pending"], 2)
    return f"done: {', '.join(done)}. next: {', '.join(nxt)}. blocker: {R.choice(['none', 'client feedback late', 'photos missing'])}"


def gen_chatgpt():
    convs = []
    fridays = [d for d in days() if d.weekday() == 4]
    for d in fridays:                                   # weekly client status mails
        for c in R.sample(CLIENTS, 2):
            t = at(d, 15, 30)
            convs.append((t, f"Weekly update {c}", [
                f"Write the weekly status update email for {c} based on these notes: {status_notes(c)}. Friendly, short, German, sign as Lena.",
                "Make it a bit shorter and add the staging link placeholder.",
            ]))
    for i, d in enumerate(R.sample(list(days()), 7)):    # proposals
        c = R.choice(["Bäckerei Krume", "Hafen Physio", "Studio Ahoi Kids", "Weinbar Elbblick", "Nordwind Segelschule", "Lokal Gin", "Kanzlei Brandt"])
        convs.append((at(d, 10), f"Angebot {c}", [
            f"Turn these discovery call notes into a proposal (Angebot) using my usual structure: goals, scope, timeline, price, next steps. Notes: {c} wants a new website, 5 pages, booking, budget around 6-8k, launch before spring. Contact phone +49 40 5551234.",
            "Use our standard day rate of 850 EUR and split it into design and build.",
            "Translate the scope section to English for the co-founder.",
        ]))
    mondays = [d for d in days() if d.weekday() == 0]
    for d in R.sample(mondays, 9):                      # LinkedIn posts
        convs.append((at(d, 16), "LinkedIn post", [
            f"Draft a LinkedIn post about our latest launch for {R.choice(CLIENTS)}: what the problem was, what we built, one result. No hashtags spam, max 120 words.",
            "Give me two alternative hooks.",
        ]))
    for d in R.sample(list(days()), 12):                # lead replies
        convs.append((at(d, 9, 15), "Reply to inquiry", [
            f"Reply to this inquiry from the website contact form: '{R.choice(['We need a new website for our dental practice', 'Can you redesign our shop logo and packaging', 'Looking for someone to build a Webflow site for our yoga studio', 'Do you do SEO?'])}'. Offer two call slots next week and link my Calendly.",
        ]))
    for d in R.sample(list(days()), 10):                # call notes -> tasks
        c = R.choice(CLIENTS)
        convs.append((at(d, 12), f"Action items {c}", [
            f"Turn these call notes into action items for Notion with owner and due date: {c} call, Jonas does the new icons, Mira fixes the booking form, I send the invoice and ask for the photos. Next call in two weeks.",
        ]))
    misc = [("Lisbon trip", "Plan a 4 day trip to Lisbon in October for two, food and design shops."),
            ("CSS grid", "Explain CSS subgrid with an example for a card layout."),
            ("Pricing", "How should a small design studio price retainers vs. projects?"),
            ("Steuer", "Was ist bei der Umsatzsteuervoranmeldung für Freiberufler zu beachten?"),
            ("Recipe", "Quick vegetarian dinner with leeks and potatoes?"),
            ("Hiring", "Write a job post for a part-time junior designer in Hamburg."),
            ("Contract", "What should a website maintenance contract include?"),
            ("Font pairing", "Suggest three font pairings for a calm physiotherapy brand.")]
    for (title, p) in misc:
        convs.append((at(R.choice(list(days())), 20), title, [p]))
    out = []
    for t, title, msgs in sorted(convs, key=lambda x: x[0]):
        mapping, parent, ts = {}, None, t
        root = uid()
        mapping[root] = {"id": root, "message": None, "parent": None, "children": []}
        parent = root
        for m in msgs:
            for role, text in (("user", m), ("assistant", "Sure — here is a draft. [assistant reply omitted in this synthetic export]")):
                nid = uid()
                mapping[nid] = {"id": nid, "parent": parent, "children": [], "message": {
                    "id": nid, "author": {"role": role}, "create_time": ts.timestamp(),
                    "content": {"content_type": "text", "parts": [text]}}}
                mapping[parent]["children"].append(nid)
                parent = nid
                ts += timedelta(minutes=2)
        out.append({"title": title, "create_time": t.timestamp(), "update_time": ts.timestamp(),
                    "mapping": mapping, "current_node": parent, "gizmo_id": None, "id": uid()})
    return out


def gen_claude_ai():
    convs = []
    for d in R.sample(list(days()), 9):
        convs.append((at(d, 11), "Website copy in brand voice", [
            f"Rewrite this website copy for {R.choice(CLIENTS)} in our brand voice (warm, clear, no buzzwords): 'We are a leading provider of innovative solutions for your wellbeing.'",
            "Now a shorter version for the meta description.",
        ]))
    for d in R.sample(list(days()), 4):
        convs.append((at(d, 14), "Case study", [
            f"Write a case study for our portfolio about the {R.choice(CLIENTS)} website: challenge, approach, result. Use the facts from the project notes I paste.",
        ]))
    for d in R.sample(list(days()), 4):
        convs.append((at(d, 10), "Proposal draft", [
            "Draft a proposal from these call notes, same structure as always (goals, scope, timeline, price, next steps): new brand + website for a bakery, 3 locations, budget 10k.",
        ]))
    for d in R.sample(list(days()), 3):
        convs.append((at(d, 17), "Client follow-up", [
            "Write a polite reminder to a client whose invoice is 14 days overdue. Mention invoice number RE-2026-041, IBAN DE89 3704 0044 0532 0130 00.",
        ]))
    out = []
    for t, name, msgs in sorted(convs, key=lambda x: x[0]):
        cm, ts = [], t
        for m in msgs:
            cm.append({"uuid": uid(), "sender": "human", "text": m, "created_at": ts.isoformat()})
            cm.append({"uuid": uid(), "sender": "assistant", "text": "[assistant reply omitted]", "created_at": (ts + timedelta(minutes=1)).isoformat()})
            ts += timedelta(minutes=3)
        out.append({"uuid": uid(), "name": name, "created_at": t.isoformat(), "updated_at": ts.isoformat(), "chat_messages": cm})
    projects = [{"uuid": uid(), "name": "Studio Nordlicht – Brand voice", "description": "How we write for clients and for ourselves.",
                 "prompt_template": "Write warm, clear and concrete. Short sentences. No buzzwords. German for clients unless asked otherwise.",
                 "docs": [{"filename": "Brand voice.md", "content": "..."}, {"filename": "Case study template.md", "content": "..."}]},
                {"uuid": uid(), "name": "Proposals", "description": "Angebote for new website and brand projects.",
                 "prompt_template": "Structure: goals, scope, timeline, price, next steps. Day rate 850 EUR.",
                 "docs": [{"filename": "Angebot-Vorlage.md", "content": "..."}]}]
    memories = [{"conversations_memory": "Lena runs Studio Nordlicht, a three-person brand and web studio in Hamburg (Lena, designer Jonas, freelance developer Mira). Builds client sites in Webflow, designs in Figma, tracks time in Toggl, invoices with Lexoffice, plans in Notion, talks in Slack. Writes German to clients, English internally. Wants proposals faster and hates chasing invoices.",
                 "project_memories": {"Proposals": "Day rate 850 EUR; proposals usually 6-10k; always offer a maintenance retainer."}}]
    users = [{"uuid": uid(), "full_name": "Lena Hoffmann", "email_address": "lena@studio-nordlicht.de"}]
    return out, projects, memories, users


# ---------------------------------------------------------------- agent transcripts
def claude_code_session(project_dir, cwd, start, prompts, tools):
    sid = uid()
    lines, t, parent = [], start, None
    for p in prompts:
        u = uid()
        lines.append({"type": "user", "uuid": u, "parentUuid": parent, "sessionId": sid, "cwd": cwd, "timestamp": t.isoformat(),
                      "message": {"role": "user", "content": p}})
        t += timedelta(minutes=R.randint(4, 15))
        content = [{"type": "text", "text": "On it."}] + [{"type": "tool_use", "id": uid(), "name": n, "input": {}} for n in R.sample(tools, min(3, len(tools)))]
        a = uid()
        lines.append({"type": "assistant", "uuid": a, "parentUuid": u, "sessionId": sid, "cwd": cwd, "timestamp": t.isoformat(),
                      "message": {"role": "assistant", "content": content}})
        # a tool result that must never reach the digest
        lines.append({"type": "user", "uuid": uid(), "parentUuid": a, "sessionId": sid, "cwd": cwd, "timestamp": t.isoformat(),
                      "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": f"OPENAI_API_KEY=sk-proj-{DECOY}abc123456789"}]}})
        parent = a
    write(project_dir / f"{sid}.jsonl", "\n".join(json.dumps(x) for x in lines) + "\n")
    return [(start, p, cwd) for p in prompts]


def gen_claude_code():
    base = HOME / ".claude" / "projects"
    hist = []
    qa = ["Run the launch QA checklist on this site: lighthouse scores, missing alt texts, broken links, meta titles and descriptions, favicon, 404 page.",
          "Fix the missing alt texts you found and write them in German.",
          "Make a short QA summary I can send to the client."]
    for proj, dates in [("kaffeebar-website", ["2026-08-19", "2026-09-02", "2026-09-30"]),
                        ("fahrradwerk-website", ["2026-09-16", "2026-10-21"]),
                        ("yoga-loft-website", ["2026-10-28"])]:
        cwd = f"/Users/lena/Sites/{proj}"
        d = base / ("-Users-lena-Sites-" + proj)
        for i, ds in enumerate(dates):
            st = datetime.fromisoformat(ds + "T10:00:00+01:00")
            prompts = qa if i == len(dates) - 1 else [f"Build the {R.choice(['hero section', 'menu page', 'contact page', 'team section'])} from the Figma export in ./design, responsive, keep our spacing scale.", "Now check it on mobile widths."]
            hist += claude_code_session(d, cwd, st, prompts, ["Bash", "Edit", "Read", "Write", "WebFetch", "mcp__figma__get_file"])
    cwd = "/Users/lena/Sites/studio-ops"
    d = base / "-Users-lena-Sites-studio-ops"
    for ds, prompts in [("2026-09-01", ["The Toggl export is in ~/Documents/Studio/Finance. Group hours by client and project and make one invoice line per project, ready to paste into Lexoffice.", "Also flag any entries without a project."]),
                        ("2026-10-01", ["Same as last month: turn the Toggl export into invoice lines per client. Then draft the invoice emails.", "Put the open action items from the client calls into Notion."]),
                        ("2026-11-02", ["Monthly invoicing again — Toggl export to Lexoffice lines, and list which clients still owe us from last month.", "Draft the reminder for the overdue ones."])]:
        hist += claude_code_session(d, cwd, datetime.fromisoformat(ds + "T09:00:00+01:00"), prompts, ["Bash", "Read", "Write", "mcp__notion__create_page", "mcp__gmail__create_draft"])
    write(d / "memory" / "invoicing.md", "---\nname: invoicing\n---\nInvoices go out on the first working day of the month. Hours come from the Toggl Track CSV export; one line per client project; day rate 850 EUR; Lexoffice for the invoice itself; reminders after 14 days. Contact for questions: lena@studio-nordlicht.de\n")
    write(d / "memory" / "launch-checklist.md", "---\nname: launch-checklist\n---\nEvery site launch: lighthouse > 90, alt texts German, 404 page, favicon, meta titles, cookie banner, redirects from old URLs, Search Console.\n")
    write(d / "memory" / "MEMORY.md", "- [Invoicing](invoicing.md)\n- [Launch checklist](launch-checklist.md)\n")
    write(HOME / ".claude" / "CLAUDE.md", "Lena prefers German for client-facing text, English for code comments. Keep answers short.\n")
    with open(HOME / ".claude" / "history.jsonl", "w") as f:
        for st, p, cwd in hist:
            f.write(json.dumps({"display": p, "timestamp": int(st.timestamp() * 1000), "project": cwd}) + "\n")
    write(HOME / ".claude" / ".credentials.json", json.dumps({"claudeAiOauth": {"accessToken": DECOY}}))
    write(HOME / ".claude" / "settings.json", json.dumps({"env": {"SOME_TOKEN": DECOY}}))


def gen_codex():
    hist = []
    for ds, prompts, cmd in [
        ("2026-08-26", ["write a script that renames exported Figma assets to kebab-case and sorts them into icons/ and images/"], "python3 rename_assets.py ./export"),
        ("2026-09-29", ["update invoice_hours.py so it groups by client and project and outputs a CSV for Lexoffice"], "python3 invoice_hours.py toggl.csv"),
        ("2026-10-12", ["make a script that checks all client sites for broken links and sends me a summary, I want to run it every Monday"], "python3 check_links.py sites.txt"),
        ("2026-10-26", ["check_links.py should also check SSL expiry and page speed for each client site"], "python3 check_links.py sites.txt"),
    ]:
        st = datetime.fromisoformat(ds + "T14:00:00+01:00")
        sid = uid()
        p = HOME / ".codex" / "sessions" / ds[:4] / ds[5:7] / ds[8:10] / f"rollout-{ds}T14-00-00-{sid}.jsonl"
        lines = [{"timestamp": st.isoformat(), "type": "session_meta", "payload": {"id": sid, "cwd": "/Users/lena/Sites/studio-ops", "originator": "codex_cli"}},
                 {"timestamp": st.isoformat(), "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<environment_context>cwd=/Users/lena</environment_context>"}]}}]
        t = st
        for pr in prompts:
            t += timedelta(minutes=1)
            lines.append({"timestamp": t.isoformat(), "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": pr}]}})
            for c in ["ls", "cat invoice_hours.py", cmd, "git add -A && git commit -m wip"]:
                t += timedelta(minutes=2)
                lines.append({"timestamp": t.isoformat(), "type": "response_item", "payload": {"type": "function_call", "name": "shell", "arguments": json.dumps({"command": ["bash", "-lc", c]})}})
                lines.append({"timestamp": t.isoformat(), "type": "response_item", "payload": {"type": "function_call_output", "output": f"token={DECOY}"}})
            hist.append({"session_id": sid, "ts": int(st.timestamp()), "text": pr})
        write(p, "\n".join(json.dumps(x) for x in lines) + "\n")
    write(HOME / ".codex" / "history.jsonl", "\n".join(json.dumps(h) for h in hist) + "\n")
    write(HOME / ".codex" / "AGENTS.md", "Use Python 3.12 and the standard library where possible. Lena's scripts live in ~/Sites/studio-ops.\n")
    write(HOME / ".codex" / "auth.json", json.dumps({"OPENAI_API_KEY": DECOY}))
    write(HOME / ".codex" / "config.toml", f'[mcp_servers.notion]\nenv = {{ NOTION_TOKEN = "{DECOY}" }}\n')


def gen_shell():
    lines = []
    for d in days():
        if d.weekday() >= 5:
            continue
        t = at(d, 9)
        cmds = ["cd ~/Sites/" + R.choice(["kaffeebar-website", "fahrradwerk-website", "studio-ops"]), "git pull", "npm run dev", "code .", "git status", "git commit -m 'update'", "git push"]
        if d.weekday() == 0:
            cmds.append("python3 check_links.py sites.txt")
        if d.day <= 3:
            cmds += ["python3 invoice_hours.py ~/Downloads/toggl.csv", "open -a 'Google Chrome' https://app.lexoffice.de/vouchers"]
        if R.random() < 0.15:
            cmds.append("ssh deploy@203.0.113.7")
        if R.random() < 0.1:
            cmds.append(f"export OPENAI_API_KEY=sk-test-{DECOY}9999")
        if R.random() < 0.2:
            cmds.append("brew upgrade")
        if R.random() < 0.3:
            cmds.append("ffmpeg -i hero.mov -vf scale=1600:-1 hero.mp4")
        for c in cmds:
            t += timedelta(minutes=R.randint(1, 40))
            lines.append(f": {int(t.timestamp())}:0;{c}")
    write(HOME / ".zsh_history", "\n".join(lines) + "\n")


def ics_dt(d):
    return d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def gen_calendar():
    ev = []
    def add(summary, start, minutes, rrule=None, attendees=(), loc=""):
        lines = ["BEGIN:VEVENT", f"UID:{uid()}", f"SUMMARY:{summary}", f"DTSTART:{ics_dt(start)}", f"DTEND:{ics_dt(start + timedelta(minutes=minutes))}",
                 "ORGANIZER;CN=Lena Hoffmann:mailto:lena@studio-nordlicht.de"]
        if rrule:
            lines.append(f"RRULE:{rrule}")
        for a in attendees:
            lines.append(f"ATTENDEE;CN=Guest:mailto:{a}")
        if loc:
            lines.append(f"LOCATION:{loc}")
        lines.append("END:VEVENT")
        ev.append("\r\n".join(lines))
    mon = START.replace(hour=9)
    add("Weekly planning", mon, 60, "FREQ=WEEKLY;BYDAY=MO")
    add("Team stand-up (Slack huddle)", mon.replace(minute=30), 15, "FREQ=WEEKLY;BYDAY=MO,WE,FR", ["jonas@studio-nordlicht.de", "mira.dev@example.com"])
    add("Kaffeebar Ost – weekly check-in", (START + timedelta(days=3)).replace(hour=14), 30, "FREQ=WEEKLY;BYDAY=TH", [CONTACT["Kaffeebar Ost"]], "https://zoom.us/j/123456789?pwd=abc")
    add("Invoicing + reminders", (START + timedelta(days=28)).replace(hour=10), 120, "FREQ=MONTHLY;BYDAY=1MO")
    add("Content time – LinkedIn", (START + timedelta(days=4)).replace(hour=16), 45, "FREQ=WEEKLY;BYDAY=FR")
    add("Client status mails", (START + timedelta(days=4)).replace(hour=15), 60, "FREQ=WEEKLY;BYDAY=FR")
    for d in days():
        if d.weekday() < 5 and R.random() < 0.35:
            who = R.choice(["Bäckerei Krume", "Hafen Physio", "Lokal Gin", "Weinbar Elbblick", "Kanzlei Brandt", "Nordwind Segelschule"])
            add(f"Discovery call – {who}", at(d, R.choice([10, 11, 14, 15])), 45, None, [f"kontakt@{who.lower().replace(' ', '-').replace('ä', 'ae')}.de"], "https://meet.google.com/abc-defg-hij")
        if d.weekday() < 5 and R.random() < 0.25:
            c = R.choice(CLIENTS)
            add(f"{c} – review call", at(d, 11), 45, None, [CONTACT[c], "jonas@studio-nordlicht.de"], "https://zoom.us/j/987654321")
    add("Zahnarzt", at(START + timedelta(days=17), 8), 60)
    cal = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Synthetic//Lena//EN\r\n" + "\r\n".join(ev) + "\r\nEND:VCALENDAR\r\n"
    write(HOME / "Downloads" / "lena-calendar-export.ics", cal)


def gen_documents():
    S = HOME / "Documents" / "Studio"
    write(S / "Templates" / "Angebot-Vorlage.md", "# Angebot – {Kunde}\n\n## Ziele\n\n## Leistungsumfang\n\n## Zeitplan\n\n## Preis\nTagessatz 850 EUR netto.\n\n## Nächste Schritte\n")
    write(S / "Templates" / "Weekly status email.md", "Hallo {Name},\n\nkurzes Update zu {Projekt}:\n- Erledigt:\n- Als Nächstes:\n- Wir brauchen von euch:\n\nViele Grüße\nLena\n")
    write(S / "Brand" / "Brand voice.md", "# Brand voice\nWarm, clear, concrete. Short sentences. No buzzwords (innovative, leading, solutions). German for clients.\n")
    write(S / "Processes" / "Website launch checklist.md", "# Launch checklist\n- Lighthouse > 90\n- Alt texts (German)\n- 404 page\n- Favicon\n- Meta titles/descriptions\n- Redirects\n- Cookie banner\n- Search Console\n")
    write(S / "Processes" / "Client onboarding.md", "# Client onboarding\n1. Kick-off call\n2. Shared Notion page\n3. Slack Connect channel\n4. Collect logo, photos, texts\n5. Toggl project\n")
    write(S / "Processes" / "Invoicing.md", "# Invoicing\nFirst working day. Toggl export → invoice_hours.py → Lexoffice. Bank: IBAN DE89 3704 0044 0532 0130 00. Reminders after 14 days. Questions: +49 40 5550199\n")
    for c in CLIENTS:
        for i in range(R.randint(2, 4)):
            d = START + timedelta(days=R.randint(0, 90))
            write(S / "Clients" / c / f"{d.date()} call notes.md", f"# {c} call\nAttendees: {CONTACT[c]}, Lena, Jonas\n- {status_notes(c)}\n- Action: send staging link\n- Action: invoice for phase {i + 1}\n")
    write(S / "Finance" / "Toggl export 2026-10.csv", "Client,Project,Description,Start date,Duration,User,Email\nKaffeebar Ost,Website,Menu page,2026-10-02,03:30:00,Jonas,jonas@studio-nordlicht.de\n")
    write(S / "Marketing" / "LinkedIn ideas.md", "- Launch story Kaffeebar Ost\n- Before/after Fahrradwerk\n- How we price websites\n")
    write(S / "ops" / ".env", f"LEXOFFICE_API_KEY={DECOY}\n")
    write(HOME / "Documents" / "Private" / "Lisbon trip.md", "Flights booked, hotel near Príncipe Real.\n")
    (HOME / "Downloads").mkdir(parents=True, exist_ok=True)
    (HOME / "Downloads" / "Rechnung_RE-2026-041_Kaffeebar.pdf").write_bytes(b"%PDF-1.4\n% synthetic\n")
    write(HOME / ".ssh" / "id_ed25519", DECOY)
    write(HOME / ".aws" / "credentials", f"[default]\naws_secret_access_key={DECOY}\n")
    for app in ["Figma", "Notion", "Slack", "Google Chrome", "Toggl Track", "Visual Studio Code", "Claude", "ChatGPT", "zoom.us", "Spotify", "Codex"]:
        (HOME / "Applications" / f"{app}.app").mkdir(parents=True, exist_ok=True)


def main():
    if HOME.exists():
        shutil.rmtree(HOME)
    gen_claude_code()
    gen_codex()
    gen_shell()
    gen_calendar()
    gen_documents()
    dl = HOME / "Downloads"
    with zipfile.ZipFile(dl / "chatgpt-export-2026-11-01.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("conversations.json", json.dumps(gen_chatgpt(), ensure_ascii=False))
        z.writestr("user.json", json.dumps({"id": "user-synthetic", "email": "lena@studio-nordlicht.de"}))
        z.writestr("chat.html", "<html><body>synthetic</body></html>")
    convs, projects, memories, users = gen_claude_ai()
    with zipfile.ZipFile(dl / "data-2026-11-01-claude.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("conversations.json", json.dumps(convs, ensure_ascii=False))
        z.writestr("projects.json", json.dumps(projects, ensure_ascii=False))
        z.writestr("memories.json", json.dumps(memories, ensure_ascii=False))
        z.writestr("users.json", json.dumps(users, ensure_ascii=False))
    import os, re as _re
    for f in (HOME / "Documents").rglob("*"):                 # realistic modification dates
        if f.is_file():
            m = _re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
            d = datetime.fromisoformat(m.group(1)) if m else START + timedelta(days=R.randint(0, 90))
            os.utime(f, (d.timestamp(), d.timestamp()))
    n = sum(1 for _ in HOME.rglob("*") if _.is_file())
    print(f"persona written: {HOME} ({n} files)")


if __name__ == "__main__":
    main()
