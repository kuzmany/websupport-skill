<div align="center">

# websupport-skill

**Buy domains & manage DNS on [Websupport](https://www.websupport.sk) — just by asking Claude.**

`.sk` `.eu` `.cz` `.com`… check a price, register a domain, edit DNS records — a Claude Code skill.

![License: MIT](https://img.shields.io/badge/License-MIT-FF5A36.svg)
![Zero dependencies](https://img.shields.io/badge/dependencies-zero-2EA043.svg)

</div>

---

## 1. Install (one line)

```bash
npx skills add https://github.com/kuzmany/websupport-skill --skill websupport
```

The [`skills`](https://www.skills.sh) CLI pulls the skill straight from GitHub
into Claude Code (`.claude/skills/`). Claude Code is auto-detected — add
`-a claude-code` to force it, or **`-g`** to install globally (available in
**every** project):

```bash
npx skills add https://github.com/kuzmany/websupport-skill --skill websupport -g
```

### …or just ask your agent to install it

Paste this into Claude Code (or any agent that can run shell commands):

> Install the Websupport skill for me: run
> `npx skills add https://github.com/kuzmany/websupport-skill --skill websupport`
> then tell me when it's ready.

## 2. Add your API keys (once)

The skill calls Websupport's API, so it needs your key + secret.
Generate them here → **<https://admin.websupport.sk/en/auth/apiKey>**

Then drop them in your shell profile (`~/.zshenv` or `~/.bashrc`):

```bash
export WEBSUPPORT_API_KEY="your-key"
export WEBSUPPORT_API_SECRET="your-secret"
```

Open a new terminal. **That's it — it's ready.**

## 3. Just ask Claude

> "check if `mycoolstartup.sk` is free and how much it costs"
> "list my Websupport domains"
> "add an A record: `www.mydomain.sk` → `1.2.3.4`"
> "register `mycoolstartup.sk` for a year"

Claude runs the right calls and shows you the result. **Buying a domain spends
real money** — Claude confirms the domain + price before it orders, and asks
again before it pays. Nothing is bought without your OK.

## What it can do

- ✅ Check domain availability + price (`.sk` `.eu` `.cz` `.com`…)
- ✅ Register / buy domains
- ✅ List your domains, DNS zones, and registrant profiles
- ✅ Read / add / update / delete DNS records

Pure Python 3 standard library — **nothing to `pip install`.** Your secret never
leaves your machine: it signs each request locally (HMAC-SHA1) and is never sent.

## Disclaimer

Unofficial. Not affiliated with or endorsed by Websupport. Ordering domains
spends real money — always confirm the domain and price first.

## License

[MIT](LICENSE) © Zdeno Kuzmany
