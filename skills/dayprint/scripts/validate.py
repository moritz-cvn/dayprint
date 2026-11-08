#!/usr/bin/env python3
"""Check a findings file or a workspace setup file before anyone sees it.

  python3 validate.py setup    cavion-workspace.json
  python3 validate.py findings findings.json
  python3 validate.py report   dayprint-report.html

Three layers: the JSON Schema (a small built-in validator, no packages needed),
cross-references and Cavion limits, and a leak scan for personal data and secrets.
Exit code 0 = clean, 1 = problems found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_leaks  # noqa: E402

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool, "null": type(None)}


# ------------------------------------------------------------------ mini JSON Schema
def check(node, schema, root, path, errs):
    if "$ref" in schema:
        ref = schema["$ref"]
        target = root
        for part in ref.lstrip("#/").split("/"):
            target = target[part]
        check(node, target, root, path, errs)
        schema = {k: v for k, v in schema.items() if k != "$ref"}
    if "oneOf" in schema:
        ok = [s for s in schema["oneOf"] if not _errs(node, s, root)]
        if len(ok) != 1:
            best = min(schema["oneOf"], key=lambda s: len(_errs(node, s, root)))
            sub = _errs(node, best, root)
            errs.append(f"{path}: matches {len(ok)} of the allowed shapes" + (f" (closest: {sub[0]})" if sub else ""))
    if "const" in schema and node != schema["const"]:
        errs.append(f"{path}: must be {json.dumps(schema['const'])}")
    if "enum" in schema and node not in schema["enum"]:
        errs.append(f"{path}: {json.dumps(node)} is not one of {schema['enum']}")
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        ok = any(isinstance(node, TYPES[x]) and not (x in ("integer", "number") and isinstance(node, bool)) for x in ts)
        if not ok:
            errs.append(f"{path}: expected {t}")
            return
    if isinstance(node, str):
        if "minLength" in schema and len(node) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(node) > schema["maxLength"]:
            errs.append(f"{path}: {len(node)} chars, limit {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], node):
            errs.append(f"{path}: {node[:40]!r} does not match {schema['pattern']}")
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        if "minimum" in schema and node < schema["minimum"]:
            errs.append(f"{path}: below {schema['minimum']}")
        if "maximum" in schema and node > schema["maximum"]:
            errs.append(f"{path}: above {schema['maximum']}")
    if isinstance(node, list):
        if "minItems" in schema and len(node) < schema["minItems"]:
            errs.append(f"{path}: needs at least {schema['minItems']} items")
        if "maxItems" in schema and len(node) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in node}) != len(node):
            errs.append(f"{path}: duplicate items")
        if "items" in schema:
            for i, x in enumerate(node):
                check(x, schema["items"], root, f"{path}[{i}]", errs)
    if isinstance(node, dict):
        for r in schema.get("required", []):
            if r not in node:
                errs.append(f"{path}: missing {r}")
        props = schema.get("properties", {})
        for k, v in node.items():
            if k in props:
                check(v, props[k], root, f"{path}.{k}", errs)
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unknown field {k}")


def _errs(node, schema, root):
    e: list[str] = []
    check(node, schema, root, "", e)
    return e


# ------------------------------------------------------------------ semantics
MEMORY_BUDGET = {"agent_notes": 2200, "user_profile": 1375}
SECTIONS = ["members", "spaces", "agents", "connections", "knowledge", "memory_seeds", "skills",
            "scheduled_tasks", "checks", "event_automations", "manual_steps"]


def semantic_setup(d, errs, warns):
    keys = {}
    for sec in SECTIONS:
        for o in d.get(sec, []):
            k = o.get("key")
            if k in keys:
                errs.append(f"key {k!r} used in {keys[k]} and {sec}; keys must be unique across the file")
            keys[k] = sec
    for s in d.get("spaces", []):
        for p in s.get("projects", []):
            keys[p["key"]] = "projects"
    of = lambda sec: {o["key"] for o in d.get(sec, [])}  # noqa: E731
    members, spaces, agents, conns, know = of("members"), of("spaces"), of("agents"), of("connections"), of("knowledge")
    projects = {p["key"] for s in d.get("spaces", []) for p in s.get("projects", [])}
    owners = [m for m in d.get("members", []) if m["role"] == "owner"]
    if len(owners) != 1:
        errs.append(f"exactly one member must be owner (found {len(owners)})")

    def ref(val, pool, where):
        if val is not None and val not in pool:
            errs.append(f"{where}: unknown key {val!r}")

    for s in d.get("spaces", []):
        for m in s["members"]:
            ref(m, members, f"spaces.{s['key']}.members")
        if not s["members"]:
            errs.append(f"spaces.{s['key']}: needs at least its owner as member")
    managers = {}
    assistants = {}
    for a in d.get("agents", []):
        w = f"agents.{a['key']}"
        if a["kind"] == "personal_assistant":
            if not a.get("owner"):
                errs.append(f"{w}: personal_assistant needs owner")
            ref(a.get("owner"), members, w)
            if a.get("owner") in assistants:
                errs.append(f"{w}: second assistant for {a['owner']} (one per member)")
            assistants[a.get("owner")] = a["key"]
        else:
            if not a.get("space"):
                errs.append(f"{w}: {a['kind']} needs space")
            ref(a.get("space"), spaces, w)
            if a["kind"] == "space_manager":
                if a.get("space") in managers:
                    errs.append(f"{w}: second manager for Space {a['space']} (one per Space)")
                managers[a.get("space")] = a["key"]
        for c in a.get("apps", []):
            ref(c, conns, f"{w}.apps")
        for s in a.get("other_spaces", []):
            ref(s, spaces, f"{w}.other_spaces")
        if a["kind"] == "specialist" and any(t in a.get("tools", []) for t in ("create_specialists", "speak_in_space_chats", "scheduled_tasks", "learn_skills")):
            warns.append(f"{w}: specialists cannot get create_specialists / speak_in_space_chats / scheduled_tasks / learn_skills in a proposal; the applier will drop them")
    conn_by = {c["key"]: c for c in d.get("connections", [])}
    agent_by = {a["key"]: a for a in d.get("agents", [])}
    for c in d.get("connections", []):
        w = f"connections.{c['key']}"
        if c["scope"] == "personal":
            if not c.get("owner"):
                errs.append(f"{w}: personal connection needs owner")
            ref(c.get("owner"), members, w)
        else:
            if not c.get("space"):
                errs.append(f"{w}: space connection needs space")
            ref(c.get("space"), spaces, w)
        if c["type"] == "mcp" and not c.get("mcp_url"):
            warns.append(f"{w}: MCP server without address; the person will paste it in Apps › MCP")
        for a in d.get("agents", []):
            if c["key"] in a.get("apps", []) and c["scope"] == "personal" and a["kind"] != "personal_assistant":
                errs.append(f"agents.{a['key']}: personal connection {c['key']} cannot be assigned to a Space agent; use a Space app")
            if c["key"] in a.get("apps", []) and c["scope"] == "space" and a.get("space") != c.get("space") \
                    and a.get("space") not in c.get("also_in_spaces", []) and a["kind"] != "personal_assistant":
                errs.append(f"agents.{a['key']}: Space app {c['key']} is not in Space {a.get('space')}")
    for k in d.get("knowledge", []):
        w = f"knowledge.{k['key']}"
        if k["vault"] == "space":
            ref(k.get("space"), spaces, w)
            if not k.get("space"):
                errs.append(f"{w}: space vault needs space")
        if k["vault"] == "my":
            ref(k.get("owner"), members, w)
    for m in d.get("memory_seeds", []):
        w = f"memory_seeds.{m['key']}"
        ref(m["agent"], agents, w)
        if m["learning_space"] == "shared_space":
            ref(m.get("space"), spaces, w)
        total = sum(len(e) for e in m["entries"]) + 3 * (len(m["entries"]) - 1)
        if total > MEMORY_BUDGET[m["document"]]:
            errs.append(f"{w}: {total} chars, {m['document']} budget is {MEMORY_BUDGET[m['document']]}")
    for s in d.get("skills", []):
        w = f"skills.{s['key']}"
        for a in s["for_agents"]:
            ref(a, agents, w)
        if s["scope"] == "space":
            ref(s.get("space"), spaces, w)
        sk = next((f for f in s["files"] if f["path"] == "SKILL.md"), None)
        if not sk:
            errs.append(f"{w}: needs a SKILL.md file")
        elif not re.match(r"^---\s*\nname:\s*\S+.*\ndescription:", sk["content"], re.S):
            errs.append(f"{w}: SKILL.md must start with frontmatter name and description")
    for t in d.get("scheduled_tasks", []) + d.get("checks", []):
        sec = "scheduled_tasks" if "timing" in t else "checks"
        w = f"{sec}.{t['key']}"
        ref(t["agent"], agents, w)
        conv = t["conversation"]
        ref(conv.get("space"), spaces, w + ".conversation")
        ref(conv.get("project"), projects, w + ".conversation")
        ag = agent_by.get(t["agent"])
        if ag and ag["kind"] != "personal_assistant" and conv.get("space") != ag.get("space") and conv.get("space") not in ag.get("other_spaces", []):
            errs.append(f"{w}: agent {t['agent']} does not work in Space {conv.get('space')}")
        if ag and ag["kind"] == "personal_assistant" and conv["audience"] == "space_shared":
            errs.append(f"{w}: a personal assistant cannot own a shared Space chat task")
        if sec == "scheduled_tasks":
            for ta in t["apps"]:
                ref(ta["connection"], conns, w + ".apps")
                if ag and ta["connection"] not in ag.get("apps", []):
                    errs.append(f"{w}: app {ta['connection']} is not assigned to agent {t['agent']}")
            for kk in t.get("knowledge", []):
                ref(kk, know, w + ".knowledge")
            tm = t["timing"]
            if tm.get("kind") == "weekly":
                mins = [int(x[:2]) * 60 + int(x[3:]) for x in tm["times"]]
                if mins != sorted(mins) or any(b - a < 30 for a, b in zip(mins, mins[1:])):
                    errs.append(f"{w}: weekly times must be sorted and 30 minutes apart")
        else:
            ref(t["app"], conns, w)
            if ag and t["app"] not in ag.get("apps", []):
                errs.append(f"{w}: app {t['app']} is not assigned to agent {t['agent']}")
            c = conn_by.get(t["app"])
            if c and c["permissions"]["read"] == "off":
                errs.append(f"{w}: checks need Read allowed on {t['app']}")
    for e in d.get("event_automations", []):
        ref(e["fallback_check"], of("checks"), f"event_automations.{e['key']}")
        ref(e["trigger"]["app"], conns, f"event_automations.{e['key']}")
    for m in d.get("manual_steps", []):
        for u in m.get("unblocks", []):
            if u not in keys:
                errs.append(f"manual_steps.{m['key']}: unblocks unknown key {u!r}")
    if not any(a["kind"] == "personal_assistant" for a in d.get("agents", [])):
        warns.append("no personal assistant is configured; every member gets one with default instructions")


COPY_TELLS = re.compile(r"\u2014|\b(seamless(ly)?|effortless(ly)?|unlock|elevate|empower|supercharge|game-chang\w*|cutting-edge|revolutionary|transformative|leverage|robust|powerful|world-class|delve)\b", re.I)


def semantic_findings(d, errs, warns):
    text = json.dumps({k: d[k] for k in ("headline", "findings", "workflows", "quick_wins", "watch_outs")}, ensure_ascii=False)
    for m in sorted({m.group(0).lower() for m in COPY_TELLS.finditer(text)}):
        warns.append(f"copy: {'em dash' if m == chr(0x2014) else repr(m)} reads as machine-written; use a plain fact instead")
    fids = {f["id"] for f in d["findings"]}
    wids = {w["id"] for w in d["workflows"]}
    if len(fids) != len(d["findings"]) or len(wids) != len(d["workflows"]):
        errs.append("finding and workflow ids must be unique")
    for w in d["workflows"]:
        for f in w["findings"]:
            if f not in fids:
                errs.append(f"workflows.{w['id']}: unknown finding {f}")
        s = w["saving"]
        if s["share_low"] > s["share_high"] or s["hours_per_week_low"] > s["hours_per_week_high"]:
            errs.append(f"workflows.{w['id']}: low saving above high saving")
        base = w["per_month"] / 4.33 * w["minutes_each"] / 60
        for side in ("low", "high"):
            exp = base * s[f"share_{side}"]
            got = s[f"hours_per_week_{side}"]
            if abs(exp - got) > max(0.15, 0.2 * exp):
                errs.append(f"workflows.{w['id']}: hours_per_week_{side} {got} does not follow per_month x minutes x share = {exp:.2f}")
        if not w["findings"]:
            warns.append(f"workflows.{w['id']}: no finding backs this workflow")
    for q in d["quick_wins"]:
        if q["workflow"] not in wids:
            errs.append(f"quick_wins: unknown workflow {q['workflow']}")
    wm = d.get("working_model") or {}
    if wm and all(h["status"] == "unasked" for h in wm.get("hypotheses", [])):
        warns.append("working_model: nothing was inferred or checked; build it from day.json (step 3)")
    for w in d["workflows"]:
        fit = w.get("fit") or {}
        if fit.get("speed") == "slower" and fit.get("on_critical_path"):
            errs.append(f"workflows.{w['id']}: makes work on the critical path slower; reshape it or move it to dropped")
        if fit.get("speed") == "slower" and wm.get("tempo") == "fast":
            warns.append(f"workflows.{w['id']}: slower for a fast person; make sure the note says why it is still worth it")


def check_timing(setup: dict, day: dict, warns: list):
    """Scheduled times and days should sit inside the person's measured day."""
    start = (day.get("typical") or {}).get("start")
    wk = day.get("weekdays") or {}
    weekend_work = any(wk.get(d, 0) >= 2 for d in ("Sat", "Sun"))
    for t in setup.get("scheduled_tasks", []):
        tm = t["timing"]
        if tm.get("kind") != "weekly":
            continue
        if start and all(x < start for x in tm["times"]) and start > "05:00":
            warns.append(f"scheduled_tasks.{t['key']}: runs at {', '.join(tm['times'])}, before the usual start ({start}); is that on purpose?")
        if weekend_work and set(tm["weekdays"]) <= {1, 2, 3, 4, 5} and len(tm["weekdays"]) >= 3:
            warns.append(f"scheduled_tasks.{t['key']}: weekdays only, but they work on weekends")


def cross(findings: dict, setup: dict, errs: list):
    keys = {o["key"] for sec in SECTIONS for o in setup.get(sec, [])}
    keys |= {p["key"] for s in setup.get("spaces", []) for p in s.get("projects", [])}
    for w in findings["workflows"]:
        for k in w["with_cavion"]["setup_keys"]:
            if k not in keys:
                errs.append(f"findings workflows.{w['id']}: setup key {k!r} not in the setup file")
    ids = {f["id"] for f in findings["findings"]} | {w["id"] for w in findings["workflows"]}
    for sec in SECTIONS:
        for o in setup.get(sec, []):
            for e in o.get("evidence", []):
                if e not in ids:
                    errs.append(f"setup {sec}.{o['key']}: evidence {e} not in findings")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("setup", "findings", "report"):
        print(__doc__)
        sys.exit(2)
    kind, path = sys.argv[1], Path(sys.argv[2])
    text = path.read_text(encoding="utf-8")
    errs, warns = [], []
    if kind != "report":
        data = json.loads(text)
        schema = json.loads((SCHEMAS / ("cavion.workspace-setup-0.1.schema.json" if kind == "setup" else "dayprint.findings-0.1.schema.json")).read_text())
        check(data, schema, schema, "$", errs)
        if not errs:
            (semantic_setup if kind == "setup" else semantic_findings)(data, errs, warns)
        other = sys.argv[3] if len(sys.argv) > 3 else None
        if other and not errs:
            o = json.loads(Path(other).read_text())
            cross(data, o, errs) if kind == "findings" else cross(o, data, errs)
        day_path = Path(sys.argv[4]) if len(sys.argv) > 4 else path.with_name("day.json")
        if kind == "setup" and day_path.exists() and not errs:
            check_timing(data, json.loads(day_path.read_text()), warns)
    if kind == "report":
        text = re.sub(r"<style>.*?</style>|<svg.*?</svg>|data:[a-z/+-]+;base64,[A-Za-z0-9+/=]+", " ", text, flags=re.S)
    for leak, frag in find_leaks(text):
        errs.append(f"possible {leak} left in the file: {frag}")
    for w in warns:
        print(f"note: {w}")
    for e in errs:
        print(f"problem: {e}")
    print(f"{path.name}: {'ok' if not errs else str(len(errs)) + ' problem(s)'}")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
