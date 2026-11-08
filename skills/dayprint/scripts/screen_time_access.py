#!/usr/bin/env python3
"""Ask for Screen Time with macOS dialogs instead of a command to paste.

  python3 screen_time_access.py --run <run> --consent <run>/consent.json [--dry-run]

macOS has no prompt an app can raise for Full Disk Access; a person has to switch it on in System
Settings. This script makes that one click away:

  1. If this process can already read Screen Time, it runs rhythm.py here and stops.
  2. A macOS dialog says what is read (app names and minutes, never what is on screen) and offers
     "Open Settings" or "Skip".
  3. It opens System Settings at Privacy & Security › Full Disk Access, and a second dialog waits
     for "Continue" once Terminal is switched on.
  4. It runs rhythm.py in a new Terminal window (Terminal has the access now, the agent's own app
     does not need a restart) and waits for day.json.
  5. If Terminal was already open, macOS applies the switch only after Terminal restarts: one more
     dialog asks to quit Terminal and try again.

Prints one JSON line: {"status": "read" | "skipped" | "restart_needed" | "failed", ...}.
If the agent itself runs inside Terminal, switching Terminal on needs a restart of the agent:
the script says so ("restart_needed") and the run folder keeps everything done so far.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import host_app  # noqa: E402

KC = Path.home() / "Library/Application Support/Knowledge/knowledgeC.db"
PANE = "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
TITLE = "Dayprint"
WAIT_S = 180


def can_read() -> bool:
    try:
        open(KC, "rb").close()      # opening reads nothing; macOS refuses the open itself without access
        return True
    except OSError:
        return False


def asq(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dialog(text: str, buttons: list[str], dry: bool) -> str | None:
    """Show a native dialog; return the button clicked, or None when dismissed or timed out."""
    if dry:
        print(f"[dialog] {text}  {buttons}")
        return buttons[-1]
    script = (f"display dialog {asq(text)} with title {asq(TITLE)} buttons {{{', '.join(asq(b) for b in buttons)}}} "
              f"default button {asq(buttons[-1])} cancel button {asq(buttons[0])} with icon note giving up after 600")
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0 or "gave up:true" in r.stdout:
        return None
    return r.stdout.split("button returned:")[-1].split(",")[0].strip()


def run_in_terminal(cmd: str, dry: bool) -> None:
    if dry:
        print(f"[terminal] {cmd}")
        return
    subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script {asq(cmd)}',
                    "-e", 'tell application "Terminal" to activate'], capture_output=True, text=True)


def wait_for_day(day: Path, since: float) -> dict | None:
    end = time.time() + WAIT_S
    while time.time() < end:
        if day.exists() and day.stat().st_mtime > since:
            time.sleep(0.5)
            try:
                return json.loads(day.read_text())["sources"].get("screen-time") or {}
            except (ValueError, KeyError):
                pass
        time.sleep(1)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--consent", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the dialogs and the command instead of showing them")
    a = ap.parse_args()
    run, consent = Path(a.run).expanduser(), Path(a.consent).expanduser()
    rhythm = Path(__file__).resolve().parent / "rhythm.py"
    args = ["python3", str(rhythm), "--run", str(run), "--consent", str(consent)]
    out = lambda **k: print(json.dumps(k)) or sys.exit(0)  # noqa: E731

    if sys.platform != "darwin" or not KC.exists():
        out(status="skipped", why="no Screen Time on this computer")
    if can_read() and not a.dry_run:
        subprocess.run(args)
        out(status="read", where="here")

    host = host_app()
    if host == "Terminal":
        msg = ("To add the apps you use to your working day, turn on Full Disk Access for Terminal. "
               "Only Screen Time is read: app names and minutes, never what is on your screen.\n\n"
               "Terminal has to restart afterwards. Your progress is kept; say “continue” after the restart.")
        if dialog(msg, ["Skip", "Open Settings"], a.dry_run) != "Open Settings":
            out(status="skipped", why="declined")
        subprocess.run(["open", PANE]) if not a.dry_run else print(f"[open] {PANE}")
        out(status="restart_needed", app="Terminal")

    msg = ("To add the apps you use to your working day, turn on Full Disk Access for Terminal.\n\n"
           "Only Screen Time is read: app names and minutes, never what is on your screen. Nothing leaves this Mac.")
    if dialog(msg, ["Skip", "Open Settings"], a.dry_run) != "Open Settings":
        out(status="skipped", why="declined")
    subprocess.run(["open", PANE]) if not a.dry_run else print(f"[open] {PANE}")

    prompt = "Turn on Terminal in the list (add it with + if it is missing), then click Continue."
    for attempt in range(2):
        if dialog(prompt, ["Skip", "Continue"], a.dry_run) != "Continue":
            out(status="skipped", why="declined")
        started = time.time()
        run_in_terminal(" ".join(shlex.quote(x) for x in args) + "; exit", a.dry_run)
        if a.dry_run:
            out(status="read", where="Terminal", dry_run=True)
        st = wait_for_day(run / "day.json", started)
        if st and st.get("read"):
            out(status="read", where="Terminal", items=st.get("items"))
        prompt = ("Terminal could not read Screen Time yet. If Terminal was already open, quit it (⌘Q) "
                  "so macOS applies the switch, then click Continue.")
    out(status="failed", why="Screen Time still not readable from Terminal")


if __name__ == "__main__":
    main()
