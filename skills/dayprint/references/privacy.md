# Privacy and trust

The person is letting an AI read years of their work. Treat that like a guest in someone's home: look only where invited, touch nothing private, and leave a note of where you have been.

## First message (adapt to the person's language)

> I'll look at what your AI tools and this computer can see about your work, find what repeats, and show you how it could run on its own — in Cavion and in the tools you already use. It all stays on this computer: nothing is uploaded. I'll ask before reading each source, I never open passwords, keys or credential files, and names and contact details are removed before I analyse anything.

## Rules the scripts enforce

- `common.is_secret_path` blocks, by path component: `.ssh`, `.gnupg`, `.aws`, `.azure`, `.kube`, `.docker`, keychains, password managers, `gcloud`, `gh`, `.git`, `node_modules`, `secrets`; and by name: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.kdbx`, `id_rsa*`/`id_ed25519*`, anything containing `credential`, `secret`, `token` or `password`, `.netrc`, `.npmrc`, `.pypirc`, `.git-credentials`, `auth.json`, `.claude.json`, `config.toml`, `settings.json`, `mcp.json`, cookies and browser login data. Blocked files are not opened, listed, counted or summarised.
- Agent transcripts: only the person's own messages and tool names are read. Tool output (which can contain file contents and secrets) and long assistant replies are skipped.
- Terminal history: only program and script names. Arguments are dropped because they can contain tokens, hosts and paths.
- Office files and PDFs: names only. Text and Markdown files: the first 500 characters. CSV: the header row.
- `redact()` replaces, before anything is written: private keys, API keys and tokens (OpenAI, Anthropic, GitHub, Slack, AWS, Google, JWTs, `key=value` secrets, bearer tokens), URL paths and query strings (hosts stay), e-mail addresses, IBANs, long numbers (cards, accounts), phone numbers, IP addresses, long hex and base64 strings, and home-folder paths (`/Users/<name>` → `~`). Names from `consent.mask_names` become `[name]`.
- `validate.py` scans findings, the setup file and the report again and fails on anything that still looks like an address, key or home path.

## Full Disk Access

Only for a deep look, only for Screen Time, and only after the person agrees. The person switches it on themselves in System Settings, for Terminal only; `screen_time_access.py` opens that page and asks in a macOS dialog, and Skip always works. The skill never opens other protected data (Mail, Messages, Safari, Photos) even when Full Disk Access is on; the secret-path rules and the source list stay the same.

## Rules for you

- Read connectors (mail, calendar, docs, chat) yourself, metadata first, and only after consent. Do not read message bodies unless the person allowed bodies.
- Never open a raw file the scripts skipped, with any tool. If the person asks you to include something blocked, explain why it is blocked and offer a safe alternative (they paste a redacted excerpt).
- Write people as roles: "a client", "the designer", "the accountant". Organisations as kinds: "a café client". Use real names only for the person's own organisation, and only if they agree.
- Paraphrase evidence. Counts and dates are fine; quotes of private messages are not.
- Leave private life out of findings and the setup file. List what you left out in `not_used`, one generic line each ("Personal travel planning").
- Do not post, send, upload or share anything. The report is a local file; the person decides who sees it.

## When the person wants something excluded

Add it to `mask_names` (for names) or set the source to false and re-run `extract.py` — it rewrites the digest from scratch. For a single topic, remove the matching findings and say what you removed.

## Clean-up

The working files (`digest/`, `stats.json`) hold redacted snippets. Offer to delete them at the end; keep `read-log.json`, `findings.json`, `cavion-workspace.json`, `apply-plan.*` and the report.
