#!/usr/bin/env python3
"""Turn cavion-workspace.json into an ordered apply plan.

  python3 plan.py cavion-workspace.json --out-dir <run>/

Writes apply-plan.json (for a future Cavion MCP) and apply-plan.md (for people).
Steps are grouped in batches of at most six, the size of one Cavion setup
proposal, so each batch is one Approve. Every batch also gets a message the
person can paste into their Cavion assistant today, before the MCP exists.

Idempotency: each step carries ledger_key = setup_id/section/key. An applier
records ledger_key -> Cavion id after success and skips steps it has already done.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GENERATOR, now_iso, read_json, write_json  # noqa: E402

BATCH = 6
DAYS = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def when(t):
    if t.get("human"):
        return t["human"]
    if t["kind"] == "once":
        return f"{t['date']} {t['time']}"
    if t["kind"] == "weekly":
        return f"{', '.join(DAYS[d] for d in t['weekdays'])} at {', '.join(t['times'])}"
    return f"every {t['minutes']} min in working hours"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("setup")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    d = read_json(a.setup)
    sid = d["setup_id"]
    live = lambda o: o.get("status", "proposed") != "skipped"  # noqa: E731
    spaces = {s["key"]: s for s in d["spaces"] if live(s)}
    agents = {x["key"]: x for x in d["agents"] if live(x)}
    conns = {c["key"]: c for c in d["connections"] if live(c)}
    person, auto = [], []

    index = {}
    for sec in ("spaces", "agents", "connections", "knowledge", "skills", "memory_seeds", "scheduled_tasks", "checks", "members", "manual_steps"):
        for o in d.get(sec, []):
            index[o["key"]] = o
    for sp in d["spaces"]:
        for p in sp.get("projects", []):
            index[p["key"]] = p

    def step(section, key, title, who, via_today, via_mcp, where, deps=(), proposal=None, group="personal"):
        s = {"ledger_key": f"{sid}/{section}/{key}", "section": section, "key": key, "title": title, "group": group,
             "who": who, "via_today": via_today, "via_mcp": via_mcp, "where": where, "depends_on": [x for x in deps if x]}
        if proposal:
            s["proposal_step"] = proposal
        if key in index:
            s["payload"] = {k: v for k, v in index[key].items() if k not in ("why", "evidence", "confidence", "status")}
        (person if who == "person" else auto).append(s)

    # people-only steps first: money, devices, sign-ins
    w = d["workspace"]
    if w["run_with"] != "undecided":
        step("workspace", "run-with", f"Run this workspace with {w['run_with'].replace('_', ' ')}", "person",
             "Manage › AI › Run this workspace with", "not allowed (funding is a person's choice)", "Manage › AI")
    for i, k in enumerate(w.get("keys", [])):
        step("workspace", f"key-{k['provider']}-{i}", f"Add an {k['provider'].title()} key"
             + (f" with a {k['monthly_budget_usd']:.0f} USD monthly budget" if k.get("monthly_budget_usd") else ""),
             "person", "Manage › AI › Keys", "not allowed (keys are never handled by agents)", "Manage › AI")
    if d["devices"]["mac_app"]["recommend"]:
        step("devices", "mac-app", "Install Cavion for Mac and approve it", "person",
             "Manage › Computers › download, then approve in the browser", "not allowed (computer approval)", "Manage › Computers")
    if d["devices"]["cloud_computer"]["recommend"]:
        step("devices", "cloud-computer", "Connect a cloud computer", "person",
             "Manage › Computers › Connect a cloud computer", "not allowed (costs money)", "Manage › Computers")
    for m in d["members"]:
        if m["invite"] == "later" and live(m):
            step("members", m["key"], f"Invite: {m['title']} ({m['role']})", "person",
                 "Manage › People › Invite (type name and e-mail)", "invite_member (planned; e-mail typed by a person)", "Manage › People")
    for c in conns.values():
        place = "My apps › Add app" if c["scope"] == "personal" else f"Space {spaces.get(c.get('space'), {}).get('name', '')} › Apps › Add app"
        if c["type"] == "mcp":
            place = place.replace("Add app", "MCP › Add MCP server")
        step("connections", c["key"], f"Connect {c.get('label') or c['app']}", "person",
             f"{place} (sign in yourself)", "start_app_connection returns the sign-in link; the person finishes it", place,
             group=c.get("space") if c["scope"] == "space" else "personal", proposal={"kind": "connect_app", "app": c["app"], "why": c["why"]} if c["type"] == "composio" else None)
    for m in d["manual_steps"]:
        step("manual_steps", m["key"], m["title"], "person", m["where"], "not automated", m["where"], m.get("unblocks", []))

    # agent-run steps, in dependency order
    for s in spaces.values():
        step("spaces", s["key"], f"Create Space {s['name']} ({'Open' if s['agent_access'] == 'open' else 'Members only'})", "card",
             "setup proposal step create_space (assistant), then Space › Settings for agent access", "create_space",
             "Spaces › +", group=s["key"], proposal={"kind": "create_space", "name": s["name"], "purpose": s["purpose"][:2000], "why": s["why"]})
        for p in s.get("projects", []):
            step("projects", p["key"], f"Project {p['name']} in {s['name']}", "direct", "CREATE_PROJECT (direct, with Undo)",
                 "create_project", f"Space {s['name']} › Overview › Projects", [s["key"]], group=s["key"])
        for m in s["members"][1:]:
            step("space_members", f"{s['key']}--{m}", f"Add {m} to {s['name']}", "card", "ADD_SPACE_MEMBER (Allow once)",
                 "set_space_member", f"Space {s['name']} › People", [s["key"], m], group=s["key"])
    for x in agents.values():
        deps = [x.get("space")] if x.get("space") else []
        deps += [c for c in x.get("apps", []) if c in conns]
        if x["kind"] == "specialist":
            step("agents", x["key"], f"Create specialist {x['name']}", "card", "setup proposal step create_specialist",
                 "create_specialist", "Space › Agents", deps, group=x["space"],
                 proposal={"kind": "create_specialist", "space": x["space"], "name": x["name"],
                           "instructions": x["instructions"][:4000], "why": x["why"]})
        else:
            what = "assistant" if x["kind"] == "personal_assistant" else f"{spaces.get(x.get('space'), {}).get('name', '')} manager"
            step("agents", x["key"], f"Set up the {what}: instructions, tools, apps", "card",
                 "CAVION_EDIT_AGENT and CAVION_SET_AGENT_TOOLS (Allow once)", "configure_agent",
                 "Home › Assistant setup" if x["kind"] == "personal_assistant" else "Space › Agents › manager › Settings", deps,
                 group=x.get("space") or "personal")
    for c in conns.values():
        p = c["permissions"]
        step("app_permissions", c["key"], f"{c.get('label') or c['app']}: Read {p['read']}, Create and change {p['create_change']}, Send {p['send_delete_share']}",
             "card", "CAVION_SET_APP_PERMISSION (Allow once)", "set_app_permission", "app › Manage", [c["key"]],
             group=c.get("space") if c["scope"] == "space" else "personal")
    for k in d["knowledge"]:
        if not live(k):
            continue
        vault = {"my": "My knowledge", "space": "Space knowledge", "company": "Company knowledge"}[k["vault"]]
        step("knowledge", k["key"], f"Knowledge: {k['folder'] + '/' if k['folder'] else ''}{k['title']} ({vault})", "card",
             "an admin asks the assistant to save it" if k["vault"] == "company" else "ask the agent to save it", "write_context", vault, [k.get("space")],
             group={"space": k.get("space"), "company": "company"}.get(k["vault"], "personal"))
    for s in d["skills"]:
        if live(s):
            step("skills", s["key"], f"Skill {s['name']}" + (" (saved as Knowledge until skill import exists)" if s["fallback"] == "knowledge" else ""),
                 "card", "save SKILL.md as a Knowledge doc and point the agent's instructions to it", "import_skill (planned)",
                 "Knowledge", s["for_agents"], group=s.get("space") if s["scope"] == "space" else ("company" if s["scope"] == "company" else "personal"))
    for m in d["memory_seeds"]:
        if live(m):
            step("memory", m["key"], f"Memory for {m['agent']}: {len(m['entries'])} {m['document'].replace('_', ' ')}", "direct",
                 "ask the agent to remember each line (memory tool)", "memory_add (planned)", "agent › Learned", [m["agent"]],
                 group=agents.get(m["agent"], {}).get("space") or "personal")
    for t in d["scheduled_tasks"]:
        if live(t):
            step("scheduled_tasks", t["key"], f"Task {t['title']} · {when(t['timing'])} (starts paused)", "card",
                 "setup proposal step schedule_task, made in the task's own chat; a person turns it on", "create_scheduled",
                 "Work › Scheduled", [t["agent"]] + [x["connection"] for x in t["apps"]], group=t["conversation"].get("space") or "personal",
                 proposal={"kind": "schedule_task", "title": t["title"], "instruction": t["instruction"][:2000],
                           "when": when(t["timing"])[:120], "why": t["why"]})
    for c in d["checks"]:
        if live(c):
            step("checks", c["key"], f"Check {c['title']} · every {c['every_minutes']} min (starts off)", "card",
                 "ask the agent in that chat to propose the check (CAVION_PROPOSE_CHECK); Cavion tests it once", "propose_check (planned)",
                 "the chat", [c["agent"], c["app"]], group=c["conversation"].get("space") or "personal")

    order = {"spaces": 0, "projects": 1, "space_members": 1, "agents": 2, "app_permissions": 3, "knowledge": 4, "skills": 4,
             "memory": 5, "scheduled_tasks": 6, "checks": 7}
    groups = ["personal", "company"] + list(spaces)
    connect_groups = {x["group"] for x in person if x["section"] == "connections"}
    batches, starts = [], {}
    for g in groups:   # one Space at a time; first create it, then (after the person connects its apps) configure it
        steps = sorted((x for x in auto if x["group"] == g), key=lambda x: order.get(x["section"], 9))
        if g in spaces and g in connect_groups:
            phases = [[x for x in steps if order.get(x["section"], 9) <= 1], [x for x in steps if order.get(x["section"], 9) > 1]]
        else:
            phases = [[], steps]
        for n, chunk in enumerate(phases):
            if not chunk:
                continue
            starts.setdefault((g, n), len(batches) + 1)
            k = -(-len(chunk) // BATCH)             # number of batches, then spread evenly
            size = -(-len(chunk) // k)
            for i in range(0, len(chunk), size):
                batches.append(chunk[i:i + size])
    for i, b in enumerate(batches, 1):
        for s in b:
            s["batch"] = i
    where_key = {x["key"]: x["batch"] for b in batches for x in b}
    for s in person:   # space apps can only be connected once their Space exists
        if s["section"] == "connections":
            s["before_batch"] = starts.get((s["group"], 1), starts.get((s["group"], 0), 1))
        else:
            s["before_batch"] = 1
    conn_batch = {s["key"]: s["before_batch"] for s in person if s["section"] == "connections"}
    for s in person:   # a manual step goes right before the first thing it unblocks
        if s["section"] == "manual_steps" and s["depends_on"]:
            cands = [conn_batch.get(k) or where_key.get(k) for k in s["depends_on"]]
            cands = [c for c in cands if c]
            s["before_batch"] = min(cands) if cands else 1
    def detail(st):
        o = st.get("payload") or {}
        sec = st["section"]
        if sec == "agents":
            return [f"Name: {o['name']}", f"Apps: {', '.join(index[c].get('label') or index[c]['app'] for c in o['apps']) or 'none'}", "Instructions:", o["instructions"]]
        if sec == "spaces":
            return [f"Purpose: {o['purpose']}", "Agents from other Spaces: " + ("Can work with this Space" if o["agent_access"] == "open" else "Members only")]
        if sec == "knowledge":
            return [o["content_md"]]
        if sec == "skills":
            return ["Save this as a Knowledge document named after the skill and follow it:", o["files"][0]["content"]]
        if sec == "memory":
            return [f"- {e}" for e in o["entries"]]
        if sec == "scheduled_tasks":
            ap = ", ".join(f"{index[x['connection']].get('label') or index[x['connection']]['app']} (read {x['read']})" for x in o["apps"]) or "none"
            return [f"When: {when(o['timing'])} ({o['timing']['timezone']})", f"Apps: {ap}", f"Instruction: {o['instruction']}"]
        if sec == "checks":
            return [f"App: {index[o['app']].get('label') or index[o['app']]['app']}, every {o['every_minutes']} minutes", f"Looks at: {o['reads']}", f"Instruction: {o['instruction']}"]
        return []

    prompts = []
    for i, b in enumerate(batches, 1):
        lines = [f"Please set this up (part {i} of {len(batches)} of my Dayprint file {sid}). Propose it as one setup where you can, and ask me before each change:", ""]
        for n, st in enumerate(b, 1):
            lines.append(f"{n}. {st['title']}")
            lines += ["   " + ln for x in detail(st) for ln in x.splitlines()]
        prompts.append("\n".join(lines))
    write_json(Path(a.out_dir) / "apply-plan.json", {
        "schema": "cavion.workspace-apply-plan/0.1", "generator": GENERATOR, "generated_at": now_iso(),
        "setup_id": sid, "revision": d["revision"], "apply_policy": d["apply_policy"],
        "person_steps": person, "batches": [{"batch": i, "steps": b} for i, b in enumerate(batches, 1)],
        "paste_prompts": prompts})
    md = [f"# Apply plan · {d['workspace']['name']}", "",
          f"Setup file `{Path(a.setup).name}` · revision {d['revision']} · nothing is deleted, automations start paused.", ""]
    for i, b in enumerate(batches, 1):
        mine = [s for s in person if s["before_batch"] == i]
        if mine:
            md += ["", "## You first" if i == 1 else f"## You, before batch {i}", ""] + [f"- [ ] {s['title']} — {s['where']}" for s in mine]
        md += ["", f"## Batch {i} · one Approve", ""] + [f"- [ ] {s['title']} — {s['via_today']}" for s in b]
    late = [s for s in person if s["before_batch"] > len(batches)]
    if late:
        md += ["", "## You, at the end", ""] + [f"- [ ] {s['title']} — {s['where']}" for s in late]
    md += ["", "## Paste into your Cavion assistant", ""]
    for p in prompts:
        md += ["```", p, "```", ""]
    (Path(a.out_dir) / "apply-plan.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(person)} steps for you, {len(auto)} agent steps in {len(batches)} batches -> {a.out_dir}")


if __name__ == "__main__":
    main()
