# Websupport REST API — Authentication & request signing

Single host: **`https://rest.websupport.sk`**. Version = path prefix: `/v1/…` (full
feature set) or `/v2/…` (newer narrow slice: DNS, FTP, hosting assign). Same auth for both.

## The scheme

HTTP **Basic** auth where:
- **username = API key**
- **password = a per-request signature** (hex HMAC-SHA1) — the secret itself is NEVER sent.

```
signature = HMAC_SHA1(key=SECRET, msg="METHOD PATH UNIX_TS").hexdigest()
Authorization: Basic base64("APIKEY:signature")
```

Canonical string = three single-space-separated tokens:
```
{UPPERCASE_METHOD} {request path} {unix epoch seconds}
e.g.  GET /v1/user/self 1548240417
```

The same unix timestamp is sent in a date header so the server can recompute and
reject stale requests.

## Critical gotchas (verified against the live API)

1. **Query string is NOT signed.** Sign the bare path; append the query only to the
   URL. The docs *prose* shows `GET /v1/some/url?attributes=123&some=aaa 1548240417`
   (query included) but that is misleading — the official Python sample signs `path`
   and builds the URL as `api + path + query` separately. Live proof: signing
   `path?query` returns **`401 {"code":401,"message":"Incorrect api key or signature."}`**.
2. **Body is NOT signed.** POST/PUT JSON bodies don't enter the canonical string.
3. **Date header.** Docs prose says header `X-Date` in ISO8601 *basic* GMT
   (`YYYYMMDDTHHMMSSZ`). The official Python/PHP clients use a `Date` header in
   ISO8601 *extended* UTC (`2026-06-17T12:00:00Z`) and that is accepted live. The
   bundled client sends **both** headers (extended `Date` + basic `X-Date`) to satisfy
   every code path. The header only matters for the server's time-window check; the
   signature depends solely on the raw integer timestamp.
4. **`self`**: pass the literal `self` for the user id (`/v1/user/self/…`) — no lookup.
5. **v2 `{service}`** path param = the **numeric service id** (from `GET
   /v1/user/self/service`), NOT the domain name. Passing `domain.sk` → `404 Service
   model s id=… nebol nájdený`.

## Reference signing code (official, verbatim)

Python 3 (from rest.websupport.sk/docs/libraries):
```python
canonicalRequest = "%s %s %s" % (method, path, timestamp)          # path WITHOUT query
signature = hmac.new(bytes(secret,'UTF-8'), bytes(canonicalRequest,'UTF-8'), hashlib.sha1).hexdigest()
headers = {"Content-Type":"application/json","Accept":"application/json",
           "Date": datetime.fromtimestamp(timestamp, timezone.utc).isoformat()}
requests.get(api + path + query, headers=headers, auth=(apiKey, signature))   # query only on URL
```

PHP (community jdrab/websupport-client, faithful):
```php
$canonicalRequest = sprintf('%s %s %s', $method, $path, $time);
$signature = hash_hmac('sha1', $canonicalRequest, $secret);
curl_setopt($ch, CURLOPT_USERPWD, $apiKey.':'.$signature);   // Basic auth
// headers: 'Date: '.gmdate('Y-m-d\TH:i:s\Z',$time), 'Content-Type: application/json'
```

`scripts/ws_api.py` implements exactly this (path-only signature, dual date headers).

## Errors

- v1: `{"code": <int>, "message": "<text>"}`
- v2: `{"type":"/errors/…","status":<int>,"title":"<text>","key":"<text>"}`
- Status codes: 200/201/204 success; 400/401/403/404/500/501 errors.
- `Accept-Language: en_us|sk|cs_cz|hu` localizes error messages (`--lang` flag).
- Rate limits & a global pagination scheme are **not documented**; per-endpoint
  pagers exist (v1 `{items, pager}`, v2 `{data, totalPages, totalRecords, …}`).
</content>
