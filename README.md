<div align="center">

# websupport-skill

**Buy domains and run DNS on [Websupport](https://www.websupport.sk) (SK registrar) straight from your terminal — or just ask your AI to do it.**

Register `.sk` `.eu` `.cz` `.com`… · check availability + price · list your domains · manage DNS — all over the official REST API.

![License: MIT](https://img.shields.io/badge/License-MIT-FF5A36.svg)
![Python 3 stdlib only](https://img.shields.io/badge/python3-stdlib%20only-555.svg)
![No deps](https://img.shields.io/badge/dependencies-zero-2EA043.svg)
![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-8A63D2.svg)

</div>

---

## TL;DR

```bash
git clone https://github.com/kuzmany/websupport-skill && cd websupport-skill && ./install.sh
export WEBSUPPORT_API_KEY=...  WEBSUPPORT_API_SECRET=...

websupport whoami                 # who am I? (credit, billing)
websupport check mojadomena.sk    # is it free? what's the price?
websupport prices --market sk     # full TLD price list
```

No `pip install`. No SDK. Pure Python 3 standard library. One file does the work.

## Why this exists

Websupport has a perfectly good REST API — but the **request signing is a trap**.
You HMAC-SHA1 a canonical string, and the docs *show you the query string inside
that string*… except the live server rejects it. Sign `path?query` → `401
Incorrect api key or signature`. You sign the **bare path**, send the query only
on the URL, and ship a timestamp in two different date-header formats to keep
both the docs and the real server happy.

This repo gets all of that right (verified against the live API) and hands you a
dead-simple CLI on top. So you — or your AI coding assistant — can buy a domain
in one line instead of losing an afternoon to a 401.

## 🤖 The vibe-coder bit: let your AI do it

This ships as a **[Claude Code](https://claude.ai/code) skill**. After
`./install.sh`, the skill lands in `~/.claude/skills/websupport` and Claude picks
it up automatically. Then you just talk:

> *"check if `mycoolstartup.sk` is free and how much it costs"*
> *"list all the domains I own on Websupport"*
> *"add an A record pointing `www.mydomain.sk` to `1.2.3.4`"*
> *"register `mycoolstartup.sk` for a year"* → Claude checks, shows the price, and **asks before spending a cent**

Claude reads `SKILL.md`, runs the right `websupport` commands, and shows you the
JSON. Buying anything is gated behind an explicit confirmation — see
[Spending money](#-spending-money-read-this) below.

Works the same from **Cursor, Cline, or any agent** that can run shell commands —
or just type the commands yourself. It's only a CLI.

## Get your API keys

1. Log in to the Websupport admin: <https://admin.websupport.sk>
2. Open **Security → API access** and generate a key + secret.
3. Export them (your secret is the HMAC key — it's **never sent over the wire**,
   so keep it out of any committed file):

   ```bash
   # ~/.zshenv or ~/.bashrc — so non-interactive shells (and your AI's tools) see them
   export WEBSUPPORT_API_KEY="your-key"
   export WEBSUPPORT_API_SECRET="your-secret"
   ```

## Install

```bash
git clone https://github.com/kuzmany/websupport-skill
cd websupport-skill
./install.sh
```

`install.sh` symlinks:
- the **`websupport`** command (alias **`ws-api`**) into `~/bin`
- the **skill** into `~/.claude/skills/websupport`

Make sure `~/bin` is on your `PATH`. No installer? Just run the script directly:
`python3 skills/websupport/scripts/ws_api.py whoami`.

## Quick start (all free, nothing spends money)

```bash
websupport whoami                     # account: id, credit, billing profiles
websupport check mojadomena.sk        # availability + price, NO order placed
websupport prices --market sk         # live TLD price list
websupport services                   # your domains (each domain is a "service")
websupport zones                      # your DNS zones
websupport dns example.sk             # DNS records of a zone
websupport profiles                   # your registrant (domain) profiles
```

Output goes: **HTTP status → stderr**, **JSON body → stdout**, non-2xx exits `1`.
So you can pipe the JSON straight into `jq` and still see the status.

## 💸 Spending money (read this)

Registering a domain costs real money / account credit. The tool **deliberately
has no "buy" button** — there's no `order` or `pay` subcommand. You do those via
the generic `post`/`put` commands, on purpose, so it's always a conscious act.

The flow is **validate → profile → order → pay**, and **order** and **pay** are
two separate confirmations:

```bash
# 1. confirm it's free + see the exact price (free)
websupport check mojadomena.sk --profile 12345

# 2. place the order (SPENDS — only after you've confirmed domain/period/profile)
websupport post /v1/user/self/order \
  --data '{"services":[{"type":"domain","domain":"mojadomena.sk","domainProfileId":12345,"period":1}]}'

# 3. pay — a SECOND, separate confirmation. byCredit silently drains credit.
websupport get /v1/user/self/order/<ORDER_ID>/pay              # hosted payment links
websupport put /v1/user/self/order/<ORDER_ID>/pay/byCredit --data '{}'   # only when you mean it
```

`12345` is your `domainProfileId` (the registrant identity) — get or create one
with `websupport profiles`. Full payloads, SK-NIC / company `.sk` (IČO) details,
and the verbatim flow are in
[`skills/websupport/references/domain-registration.md`](skills/websupport/references/domain-registration.md).

> When Claude drives this, it will check + show you the price and **ask before
> ordering, then ask again before paying.** Never let an agent chain order→pay
> unattended.

## Manage DNS

```bash
# v1 (works, by domain name)
websupport get  /v1/user/self/zone/example.sk/record
websupport post /v1/user/self/zone/example.sk/record \
  --data '{"type":"A","name":"www","content":"1.2.3.4","ttl":3600}'

# v2 (current, by NUMERIC service id from `websupport services`)
websupport get  /v2/service/28468/dns/record
websupport post /v2/service/28468/dns/record \
  --data '{"type":"A","name":"www","content":"1.2.3.4","ttl":3600}'
```

## All commands

| Command | What it does |
|---|---|
| `whoami` | account info — id, credit, billing |
| `check <domain> [--market sk] [--profile ID]` | availability + price, **no order** |
| `prices [--market sk]` | TLD price list for a storefront market |
| `services` | your domains/products (domain = a "service") |
| `zones` | your DNS zones |
| `dns <domain>` | DNS records of a zone (v1) |
| `profiles` | your registrant (domain) profiles |
| `get / post / put / delete <path>` | any signed request to any endpoint |
| `raw <METHOD> <path>` | escape hatch for anything else |

`get`/`post`/`put`/`raw` accept `--query k=v …` (URL params) and `--data '<json>'`
(body). Add `--lang sk\|en_us\|cs_cz\|hu` for localized error messages.

## Good to know

- **`--market` is the storefront country** (`sk\|cz\|hu\|at`), independent of the
  TLD. Buy a `.com` through the `sk` market.
- **v2 `{service}` is the numeric service id** (e.g. `28468`), *not* the domain
  name. Pass a domain there → `404`. Get the id from `websupport services`.
- Use the literal **`self`** for the user id in `/v1/user/self/…` paths.
- v1 errors look like `{"code":N,"message":…}`; v2 like `{"status":N,"title":…}`.
- The client **retries** transient network drops / read-timeouts (the API can
  hiccup under burst) with a fresh signature each attempt.

## Layout

```
bin/websupport                          thin wrapper (also installed as ws-api)
skills/websupport/SKILL.md              the Claude Code skill (what the AI reads)
skills/websupport/scripts/ws_api.py     the whole client — stdlib only, ~200 lines
skills/websupport/references/           deep docs:
  auth.md                                 HMAC-SHA1 signing + the path/query/header traps
  domain-registration.md                  validate → profile → order → pay, verbatim
  endpoints.md                             v1/v2 endpoint map, DNS CRUD, pagination, errors
install.sh                              symlinks command + skill into place
```

## How auth works (the 60-second version)

```
signature = HMAC_SHA1(SECRET, "METHOD /bare/path UNIX_TS").hexdigest()
Authorization: Basic base64("APIKEY:signature")
Date: 2026-06-17T12:00:00Z          # extended ISO-8601 (what the live server accepts)
X-Date: 20260617T120000Z            # basic ISO-8601 (what the docs prose wants) — send both
```

- **Path only** in the signature — *not* the query string, *not* the body.
- Same `UNIX_TS` goes in the signature **and** the date header (server checks the window).
- Secret is the HMAC key; it never leaves your machine.

Full details + the official reference snippets:
[`skills/websupport/references/auth.md`](skills/websupport/references/auth.md).

## Requirements

- **Python 3** (standard library only — nothing to `pip install`).
- A Websupport account with API access (key + secret).

## Disclaimer

Unofficial. Not affiliated with or endorsed by Websupport. Use at your own risk —
**ordering domains spends real money.** Always confirm price and domain before
you order, and again before you pay.

## License

[MIT](LICENSE) © Zdeno Kuzmany
