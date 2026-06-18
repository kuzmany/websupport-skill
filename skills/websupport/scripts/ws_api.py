#!/usr/bin/env python3
"""Websupport REST API client (https://rest.websupport.sk).

Auth (verified against the live API): HTTP Basic where
  username = API key
  password = hex HMAC-SHA1 signature over the canonical string
             "METHOD path UNIX_TIMESTAMP"   (query string and BODY are NOT signed)
The same unix timestamp is sent in the date headers so the server can
recompute the signature. We send BOTH `Date` (extended ISO-8601 UTC, what the
official Python/PHP clients use and what the live server accepts) and `X-Date`
(compact ISO-8601 basic GMT, what the docs prose requires) — belt and braces.

Credentials come from env: WEBSUPPORT_API_KEY / WEBSUPPORT_API_SECRET.
See references/ for full endpoint docs.

Generic:
  ws_api.py whoami
  ws_api.py get  <path> [--query k=v ...]
  ws_api.py post <path> --data '<json>' [--query k=v ...]
  ws_api.py put  <path> --data '<json>'
  ws_api.py delete <path>
  ws_api.py raw <METHOD> <path> [--data '<json>'] [--query k=v ...]

Convenience (read-only / safe):
  ws_api.py prices [--market sk]          # GET /v1/order/<market>  (TLDs + prices)
  ws_api.py services                      # GET /v1/user/self/service (domains as services)
  ws_api.py zones                         # GET /v1/user/self/zone (DNS zones)
  ws_api.py dns <domain>                  # GET /v1/user/self/zone/<domain>/record
  ws_api.py profiles                      # GET /v1/user/self/domainProfile (registrant profiles)
  ws_api.py check <domain> [--market sk] [--profile ID]   # validate availability + price (no order)

Money-spending operations (create profile, order a domain, pay) are NOT given
dedicated subcommands on purpose — do them via `post`/`put` after explicit
confirmation. See references/domain-registration.md.
"""
import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import sys
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = os.environ.get("WEBSUPPORT_API_BASE", "https://rest.websupport.sk")


def _creds():
    key = os.environ.get("WEBSUPPORT_API_KEY")
    secret = os.environ.get("WEBSUPPORT_API_SECRET")
    if not key or not secret:
        sys.exit("ERROR: set WEBSUPPORT_API_KEY and WEBSUPPORT_API_SECRET "
                 "(export them in your shell, e.g. ~/.zshenv or ~/.bashrc, "
                 "then open a new shell).")
    return key, secret


def sign(method, path, ts, secret):
    """hex HMAC-SHA1 of 'METHOD path TS'. `path` is the BARE request path —
    the query string is deliberately EXCLUDED (signing it returns 401)."""
    canonical = "%s %s %s" % (method.upper(), path, ts)
    return hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"),
                    hashlib.sha1).hexdigest()


def call(method, path, data=None, query=None, accept_language=None, retries=3):
    """Signed request. Returns (status:int, parsed_body | text | None).

    Retries transient network/TLS errors (the API occasionally drops a
    connection or read-times-out under burst); the timestamp + signature are
    regenerated on each attempt so they never go stale. HTTP error responses
    (4xx/5xx) are returned, not retried.
    """
    key, secret = _creds()
    method = method.upper()

    # CRITICAL: the signature is computed over the path WITHOUT the query string.
    # (The docs prose shows query in the canonical example, but the official client
    # signs the bare path and only appends the query to the URL — verified live:
    # signing path+query returns 401 "Incorrect api key or signature".)
    qs = urlencode(query) if query else ""
    url_path = path + ("?" + qs if qs else "")
    body = json.dumps(data).encode("utf-8") if data is not None else None

    # Harden against a crafted `path` that redirects the request — and the
    # API-key Authorization header — to another host. Example: path="@evil.com/x"
    # makes API + path = "https://rest.websupport.sk@evil.com/x", whose real host
    # is evil.com. Require a leading "/" and verify the final URL stays on the
    # configured base host/scheme before anything is signed or sent.
    if not path.startswith("/"):
        sys.exit("ERROR: path must start with '/' (got %r)" % (path,))
    _want, _got = urlparse(API), urlparse(API + url_path)
    if (_got.scheme, _got.hostname) != (_want.scheme, _want.hostname):
        sys.exit("ERROR: refusing request to unexpected host %r" % (_got.hostname,))

    last_err = None
    for attempt in range(retries):
        ts = int(time.time())
        signature = sign(method, path, ts, secret)
        date_ext = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))   # 2026-06-17T12:00:00Z
        date_basic = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(ts))     # 20260617T120000Z
        basic = base64.b64encode(("%s:%s" % (key, signature)).encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Date": date_ext,
            "X-Date": date_basic,
            "Authorization": "Basic " + basic,
        }
        if accept_language:
            headers["Accept-Language"] = accept_language

        req = Request(API + url_path, data=body, headers=headers, method=method)
        try:
            resp = urlopen(req, timeout=30)
            status, raw = resp.getcode(), resp.read().decode("utf-8", "replace")
        except HTTPError as e:
            # A real HTTP response (4xx/5xx) — return it, don't retry.
            status, raw = e.code, e.read().decode("utf-8", "replace")
        except (OSError, http.client.HTTPException) as e:
            # Every transient transport failure is an OSError subclass
            # (URLError, ssl.SSLError, ConnectionError, and crucially a read
            # TimeoutError / socket.timeout) or an http.client.HTTPException.
            # Catching the base classes keeps a single dropped/timed-out
            # connection from escaping the retry loop as an uncaught traceback.
            last_err = e
            if attempt < retries - 1:
                time.sleep(0.6 * (attempt + 1))
                continue
            sys.exit("Network error after %d attempts: %s" % (retries, last_err))

        try:
            return status, (json.loads(raw) if raw else None)
        except ValueError:
            return status, raw


def _emit(status, body):
    sys.stderr.write("HTTP %s\n" % status)
    if isinstance(body, (dict, list)):
        print(json.dumps(body, indent=2, ensure_ascii=False))
    elif body is not None:
        print(body)
    sys.exit(0 if 200 <= status < 300 else 1)


def _q(items):
    out = {}
    for it in items or []:
        if "=" in it:
            k, v = it.split("=", 1)
            out[k] = v
    return out


def main():
    p = argparse.ArgumentParser(description="Websupport REST API client")
    p.add_argument("--lang", help="Accept-Language for error messages: en_us|sk|cs_cz|hu")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="GET /v1/user/self")
    sub.add_parser("services", help="GET /v1/user/self/service")
    sub.add_parser("zones", help="GET /v1/user/self/zone")
    sub.add_parser("profiles", help="GET /v1/user/self/domainProfile")

    pr = sub.add_parser("prices", help="GET /v1/order/<market>")
    pr.add_argument("--market", default="sk")

    dn = sub.add_parser("dns", help="GET /v1/user/self/zone/<domain>/record")
    dn.add_argument("domain")

    ck = sub.add_parser("check", help="validate domain availability + price (no order)")
    ck.add_argument("domain")
    ck.add_argument("--market", default="sk")
    ck.add_argument("--profile", help="domainProfileId to validate against")

    g = sub.add_parser("get"); g.add_argument("path"); g.add_argument("--query", nargs="*")
    for name in ("post", "put"):
        sp = sub.add_parser(name)
        sp.add_argument("path"); sp.add_argument("--data", required=True)
        sp.add_argument("--query", nargs="*")
    d = sub.add_parser("delete"); d.add_argument("path")
    r = sub.add_parser("raw")
    r.add_argument("method"); r.add_argument("path")
    r.add_argument("--data"); r.add_argument("--query", nargs="*")

    a = p.parse_args()
    lang = a.lang

    if a.cmd == "whoami":
        _emit(*call("GET", "/v1/user/self", accept_language=lang))
    elif a.cmd == "services":
        _emit(*call("GET", "/v1/user/self/service", accept_language=lang))
    elif a.cmd == "zones":
        _emit(*call("GET", "/v1/user/self/zone", accept_language=lang))
    elif a.cmd == "profiles":
        _emit(*call("GET", "/v1/user/self/domainProfile", accept_language=lang))
    elif a.cmd == "prices":
        _emit(*call("GET", "/v1/order/%s" % a.market, accept_language=lang))
    elif a.cmd == "dns":
        _emit(*call("GET", "/v1/user/self/zone/%s/record" % a.domain, accept_language=lang))
    elif a.cmd == "check":
        body = {"domain": a.domain}
        if a.profile:
            body["domainProfileId"] = int(a.profile)
        _emit(*call("POST", "/v1/order/%s/validate/domain" % a.market, data=body,
                    accept_language=lang))
    elif a.cmd == "get":
        _emit(*call("GET", a.path, query=_q(a.query), accept_language=lang))
    elif a.cmd in ("post", "put"):
        _emit(*call(a.cmd.upper(), a.path, data=json.loads(a.data),
                    query=_q(a.query), accept_language=lang))
    elif a.cmd == "delete":
        _emit(*call("DELETE", a.path, accept_language=lang))
    elif a.cmd == "raw":
        _emit(*call(a.method, a.path, data=(json.loads(a.data) if a.data else None),
                    query=_q(a.query), accept_language=lang))


if __name__ == "__main__":
    main()
