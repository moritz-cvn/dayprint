"""Shared helpers for the dayprint scripts.

Standard library only, so the scripts run offline on any machine with Python 3.9+.
Everything here is about two promises the skill makes to the user:
  1. secret files are never opened (see is_secret_path), and
  2. nothing personal or secret leaves a script un-redacted (see redact).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
GENERATOR = f"dayprint/{VERSION}"

# ---------------------------------------------------------------- secret paths
# Files and folders that are never opened, listed or summarised. Matching is on
# path components (case-insensitive), so it also protects copies inside exports.
SECRET_DIRS = {
    ".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker", ".password-store",
    "keychains", "1password", ".1password", "bitwarden", ".terraform.d",
    "gcloud", "gh", ".vault-token", "cookies", "login data", "web data",
    ".git", "node_modules", "secrets",
}
SECRET_NAME_PATTERNS = [
    r"^\.env($|\.)", r"\.env$", r"\.pem$", r"\.key$", r"\.p12$", r"\.pfx$",
    r"\.keychain(-db)?$", r"\.kdbx$", r"^id_(rsa|dsa|ecdsa|ed25519)",
    r"credential", r"secret", r"token", r"password", r"passwd", r"^\.netrc$",
    r"^\.npmrc$", r"^\.pypirc$", r"^\.git-credentials$", r"^auth\.json$",
    r"^\.claude\.json$", r"^config\.toml$", r"^settings(\.local)?\.json$",
    r"^\.mcp\.json$", r"^mcp\.json$", r"^cookies", r"^login data", r"\.sqlite-wal$",
]
_SECRET_NAME_RE = re.compile("|".join(SECRET_NAME_PATTERNS), re.IGNORECASE)


def is_secret_path(path: str | os.PathLike) -> bool:
    """True when a path looks like it may hold credentials or keys.

    Deliberately over-cautious: a skipped harmless file costs little, a read
    secret breaks the user's trust.
    """
    parts = [p.lower() for p in Path(path).parts]
    if any(p in SECRET_DIRS for p in parts):
        return True
    return bool(_SECRET_NAME_RE.search(parts[-1] if parts else ""))


# ------------------------------------------------------------------ redaction
_RULES: list[tuple[re.Pattern, str]] = [
    # private keys and tokens first, so later rules do not split them
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[secret]"),
    (re.compile(r"\b(sk|rk|pk)-(ant-|proj-|live-|test-)?[A-Za-z0-9_\-]{12,}"), "[secret]"),
    (re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"), "[secret]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[secret]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[secret]"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"), "[secret]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), "[secret]"),
    (re.compile(r"(?i)\b(api[_-]?key|access[_-]?key|secret|token|password|passwd|pwd|authorization)\b\s*[:=]\s*[\"']?[^\s\"',;]{4,}"), r"\1 [secret]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{10,}"), "Bearer [secret]"),
    # URLs: keep scheme + host, drop paths and query strings (they carry ids and tokens)
    (re.compile(r"\b(https?://)([A-Za-z0-9.\-]+)(:[0-9]+)?[^\s)\]>\"']*"), r"\1\2"),
    # personal data
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[email]"),
    (re.compile(r"\b[A-Z]{2}[0-9]{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,3})?\b"), "[iban]"),
    (re.compile(r"\b(?:\d[ \-]?){13,19}\b"), "[number]"),
    (re.compile(r"\b[A-Z]{1,5}[-/]\d{2,4}[-/]\d{1,6}\b"), "[number]"),   # invoice, order and ticket numbers
    (re.compile(r"(?<![\w.])\+?\(?\d{2,4}\)?[ \-/]?\d{2,5}[ \-/]?\d{3,8}(?!\w|[.,]\d)"), "[phone]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[ip]"),
    # long opaque strings (hashes, ids, base64 blobs)
    (re.compile(r"\b[A-Fa-f0-9]{32,}\b"), "[id]"),
    (re.compile(r"\b[A-Za-z0-9+/_\-]{40,}={0,2}"), "[id]"),
    # home folders reveal user names
    (re.compile(r"(/Users|/home)/[^/\s]+"), "~"),
    (re.compile(r"C:\\Users\\[^\\\s]+", re.I), "~"),
]

_mask_names: list[re.Pattern] = []


def set_masked_names(names: list[str]) -> None:
    """Extra words (people, clients) to replace with [name] everywhere."""
    global _mask_names
    _mask_names = [re.compile(r"\b" + re.escape(n) + r"\b", re.I) for n in names if len(n.strip()) >= 2]


def redact(text: str | None, limit: int | None = None) -> str:
    if not text:
        return ""
    out = str(text)
    for rx, repl in _RULES:
        out = rx.sub(repl, out)
    for rx in _mask_names:
        out = rx.sub("[name]", out)
    out = re.sub(r"\s+", " ", out).strip()
    if limit and len(out) > limit:
        out = out[: limit - 1].rstrip() + "…"
    return out


LEAK_PATTERNS = {name: rx for name, rx in [
    ("private key", re.compile(r"PRIVATE KEY-----")),
    ("api key", re.compile(r"\b(sk|rk)-(ant-|proj-|live-|test-)?[A-Za-z0-9_\-]{12,}")),
    ("github token", re.compile(r"\b(ghp|gho|ghs)_[A-Za-z0-9]{20,}|github_pat_")),
    ("slack token", re.compile(r"\bxox[abprs]-")),
    ("aws key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.")),
    ("email address", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("iban", re.compile(r"\b[A-Z]{2}[0-9]{2}(?:[ ]?[A-Z0-9]{4}){3,7}\b")),
    ("home path", re.compile(r"/Users/[^/\s~\"]+/|/home/[^/\s~\"]+/")),
]}


def find_leaks(text: str, allow: set[str] | None = None) -> list[tuple[str, str]]:
    """Return (kind, excerpt) for anything that still looks personal or secret."""
    allow = allow or set()
    hits = []
    for kind, rx in LEAK_PATTERNS.items():
        for m in rx.finditer(text):
            frag = m.group(0)
            if frag in allow:
                continue
            hits.append((kind, frag[:12] + "…"))
    return hits


# ------------------------------------------------------------------ io helpers
def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def tilde(path: str | os.PathLike, home: Path) -> str:
    p = str(path)
    h = str(home)
    return "~" + p[len(h):] if p.startswith(h) else redact(p)


def read_json(path: str | os.PathLike):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | os.PathLike, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def to_dt(value) -> datetime | None:
    """Parse epoch seconds/ms or ISO strings into aware datetimes."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and re.fullmatch(r"\d+(\.\d+)?", value)):
            v = float(value)
            if v > 1e12:
                v /= 1000.0
            return datetime.fromtimestamp(v, tz=timezone.utc)
        s = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)
