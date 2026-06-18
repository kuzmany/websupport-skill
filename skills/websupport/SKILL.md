---
name: websupport
description: >
  Manage Websupport (rest.websupport.sk) via its REST API: register/buy domains
  (.sk, .eu, .cz, .com…), check domain availability and price, list owned
  domains/services, and manage DNS records and registrant (domain) profiles.
  Use when the user asks to "buy/register a domain", "check if domain is free",
  "kúpiť doménu", "zaregistrovať doménu .sk", "skontrolovať dostupnosť domény",
  "Websupport API", "manage Websupport DNS", "add DNS record on Websupport",
  "spravovať DNS na Websupporte", "pridať DNS záznam", "list my domains",
  "domain price", or anything touching rest.websupport.sk.
version: 1.0.0
---

# Websupport REST API

Buy domains and manage DNS / hosting on **Websupport** (Slovak registrar, SK-NIC
accredited) through `https://rest.websupport.sk`. **.sk registration via API works.**

All calls go through `scripts/ws_api.py` — a self-contained Python 3 client (stdlib
only, no deps) that handles the tricky HMAC-SHA1 request signing for you.

## Credentials

Read from env vars (export them in your shell profile, e.g. `~/.zshenv` or
`~/.bashrc`, so non-interactive tool shells inherit them):

- `WEBSUPPORT_API_KEY`
- `WEBSUPPORT_API_SECRET`

If a call returns `ERROR: set WEBSUPPORT_API_KEY…`, open a new shell or
`source` your profile first. **Never** hardcode the secret into files or
commands — it is the HMAC key and is never transmitted. Generate/rotate keys at
https://admin.websupport.sk/en/auth/apiKey .

## Quick start

```bash
P=~/.claude/skills/websupport/scripts/ws_api.py   # the client bundled with the skill
python3 "$P" whoami                       # auth smoke test → your user (id, credit, billing)
python3 "$P" check mojadomena.sk          # is it free? + price (no order placed)
python3 "$P" prices --market sk           # live TLD price list
python3 "$P" services                     # your domains (as "services")
python3 "$P" zones                        # your DNS zones
python3 "$P" dns example.sk               # DNS records of a zone (v1)
python3 "$P" profiles                     # your registrant (domain) profiles
```

> Snippets use the explicit `python3 "$P"` form. `$P` assumes a global install
> (`~/.claude/skills/websupport`, e.g. `npx skills add https://github.com/kuzmany/websupport-skill --skill websupport -g`);
> point it at the cloned `scripts/ws_api.py` if you installed into a project.

## Commands

| Command | HTTP call | Purpose |
|---|---|---|
| `whoami` | `GET /v1/user/self` | account info, `id`, `credit`, billing profiles |
| `check <domain> [--market sk] [--profile ID]` | `POST /v1/order/<market>/validate/domain` | availability + price, **no order** |
| `prices [--market sk]` | `GET /v1/order/<market>` | TLD price list + VPS/templates for a market |
| `services` | `GET /v1/user/self/service` | owned domains/products (domain = a "service") |
| `zones` | `GET /v1/user/self/zone` | DNS zones |
| `dns <domain>` | `GET /v1/user/self/zone/<domain>/record` | DNS records (v1) |
| `profiles` | `GET /v1/user/self/domainProfile` | registrant identity profiles |
| `get/post/put/delete <path>` | generic signed request | any endpoint not wrapped above |
| `raw <METHOD> <path>` | generic | escape hatch |

`get`/`post`/`put`/`raw` take `--query k=v …` (added to URL) and `--data '<json>'` (body).
Add `--lang sk|en_us|cs_cz|hu` for localized error messages.

Output: HTTP status to **stderr**, JSON body to **stdout**, non-2xx → exit 1.

## Buying a domain (validate → profile → order → pay)

`check` is free and safe. **Ordering spends money / credit** — never run an order
without explicit user confirmation of the exact domain, period, and registrant profile.
Full verbatim payloads and the 5-step flow are in `references/domain-registration.md`.

Treat **order** and **pay** as two separate, separately-confirmed actions.

Step A — check, then (after user confirms domain/period/profile) place the order:
```bash
P=~/.claude/skills/websupport/scripts/ws_api.py
python3 "$P" check mojadomena.sk --profile 12345     # confirm free + price (no spend)
python3 "$P" post /v1/user/self/order --data '{"services":[{"type":"domain","domain":"mojadomena.sk","domainProfileId":12345,"period":1}]}'
```
The order returns HTTP 201 with `item.id` (order id) and the final `priceWithVat`.
(`--profile` does not change availability/price — it surfaces registrant-specific
validation errors up front; the binding registrant check happens at order time.)

Step B — pay (a SECOND confirmation). Re-show the order's `priceWithVat` and get a
fresh OK before paying. `byCredit` silently drains account credit (no gateway prompt):
```bash
python3 "$P" get /v1/user/self/order/<ORDER_ID>/pay        # read-only: hosted payment links to hand the user
python3 "$P" put /v1/user/self/order/<ORDER_ID>/pay/byCredit --data '{}'   # ONLY after explicit pay confirmation
```
For .sk the order response returns the SK-NIC `sknicHandle`. Registrant data is
supplied via a **domain profile** (`domainProfileId`); company .sk needs `orgName` +
`identCompanyRegistration` (IČO). See `references/domain-registration.md`.

## DNS records

- v1 (works, marked deprecated): `GET/POST /v1/user/self/zone/<domain>/record`,
  `PUT/DELETE /v1/user/self/zone/<domain>/record/<recordId>`
- v2 (current, **uses the numeric service id**, NOT the domain name):
  `GET/POST /v2/service/<serviceId>/dns/record`,
  `PUT/DELETE /v2/service/<serviceId>/dns/record/<recordId>`.
  Get `<serviceId>` from `services`. v2 returns a `{data, totalPages, …}` envelope.

See `references/endpoints.md` for the full v1/v2 map, pagination, and error formats.

## Gotchas (verified live)

- **Signature covers the path only — NOT the query string.** Signing `path?query`
  returns `401 Incorrect api key or signature`. The client appends the query to the
  URL but signs the bare path. Body is **not** signed either.
- Pass `self` for the user id in any `/v1/user/<id>/…` path — no id lookup needed.
- v2 `{service}` is the **numeric service id** (e.g. `28468`), not `domain.sk`.
- `prices` / `validate` `--market` is the storefront country (`sk|cz|hu|at`),
  independent of the TLD — buy `.com` via the `sk` market.
- v1 errors → `{"code":N,"message":…}`; v2 errors → `{"status":N,"title":…,"key":…}`.

## References

- `references/auth.md` — exact signing algorithm + the path/query/header gotchas
- `references/domain-registration.md` — validate → profile → order → pay, verbatim payloads
- `references/endpoints.md` — v1/v2 endpoint map, DNS CRUD, pagination, errors

When in doubt, trust the live API over these notes: `whoami`, `prices`, and `check`
are free probes. Official docs: https://rest.websupport.sk/docs (v1) and
https://rest.websupport.sk/v2/docs (v2).
