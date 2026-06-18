# Websupport REST API — endpoint map

Host `https://rest.websupport.sk`. `<id>` accepts the literal `self`.
v1 = full feature set; v2 = newer narrow slice (DNS / FTP / hosting-assign / auth-check).
For DNS records v2 is the current path (v1 record endpoints are marked deprecated but
still work). Everything else (ordering, listing, invoices, hosting, VPS) is v1-only.

## User / account (v1)
| Method+Path | Notes |
|---|---|
| `GET /v1/user/self` | account: `id`, `login`, `credit`, `billing[]` |
| `GET /v1/user` · `GET /v1/user/<id>` | list / one user |

## Services = your domains & products (v1)
| Method+Path | Notes |
|---|---|
| `GET /v1/user/self/service` | list; each item `{id, serviceName:"domain", name:"x.sk", expireTime, price, autoExtend}` → `{items, pager}` |
| `GET /v1/user/self/service/<serviceId>` | one service detail |
| `PUT /v1/user/self/service/<serviceId>` | update (e.g. `autoExtend`) |

The `service.id` is also the **v2 `{service}` id** for DNS.

## DNS zones + records
| Method+Path | Notes |
|---|---|
| `GET /v1/user/self/zone` | list zones `{items:[{id,name}], pager}` |
| `GET /v1/user/self/zone/<domain>` | zone detail |
| `GET /v1/user/self/zone/<domain>/record` | **v1** records `{items:[{type,id,name,content,ttl,note}]}` (deprecated, works) |
| `GET /v1/user/self/zone/<domain>/record/<id>` | one record (v1) |
| `POST /v1/user/self/zone/<domain>/record` | create (v1) |
| `PUT /v1/user/self/zone/<domain>/record/<id>` | update (v1) |
| `DELETE /v1/user/self/zone/<domain>/record/<id>` | delete (v1) |
| `GET /v2/service/<serviceId>/dns/record` | **v2** list; envelope `{data:[…],currentPage,rowsPerPage,totalPages,totalRecords,nextPageUrl}` |
| `POST /v2/service/<serviceId>/dns/record` | create (v2) |
| `PUT /v2/service/<serviceId>/dns/record/<recordId>` | update (v2) |
| `DELETE /v2/service/<serviceId>/dns/record/<recordId>` | delete (v2) |
| `GET /v2/service/<serviceId>/dns/zone` | zone detail (v2) |

v2 DNS list query params: `page`, `rowsPerPage`, `descending`, `sortBy`, and a
`filters` deepObject (`filters[name]`, `filters[type][]` ∈
A/AAAA/ANAME/CAA/CNAME/MX/SRV/TXT/CERT/LOC/SSHFP/TLSA/DS, `filters[content]`,
`filters[ttl]`, `filters[priority]`, `filters[port]`, `filters[weight]`, …).
There is **no** single-record GET in v2 — list and filter instead.

Record create/update body (typical): `{"type":"A","name":"www","content":"1.2.3.4","ttl":3600}`
(MX/SRV add `priority`/`port`/`weight`).

## Ordering / domains (v1) — see domain-registration.md
| Method+Path | Notes |
|---|---|
| `GET /v1/order/<market>` | TLD prices + VPS/credit (`market` = sk/cz/hu/at) |
| `POST /v1/order/<market>/validate/domain` | availability + price (free) |
| `POST /v1/user/self/order` | place order (domain/vps/credit) → `item.id` |
| `GET /v1/user/self/order/<orderId>/pay` | hosted payment URLs |
| `PUT /v1/user/self/order/<orderId>/pay/byCredit` | pay from credit |
| `PUT /v1/user/self/order/<orderId>/pay/byPaymentCard/<cardId>` | pay by stored card |
| `GET/POST /v1/user/self/domainProfile` · `GET/PUT/DELETE …/<id>` | registrant profiles |

## Other groups (v1, not yet exercised here)
Invoice management, Hosting management, VPS management — documented at
https://rest.websupport.sk/docs (groups: User, Service, Invoice, Ordering, DNS,
Hosting, VPS). v2 also has FTP account CRUD (`/v2/service/<id>/ftp/account…`),
hosting `assign-domain`, and `/v2/check` (auth check).

## Pagination & errors
- v1 pager: response `{items:[…], pager:{…}}`; query `page`, `pagesize` (per-endpoint).
- v2 pager: `{data:[…], currentPage, rowsPerPage, totalPages, totalRecords, nextPageUrl}`.
- v1 error: `{"code":N,"message":"…"}` · v2 error: `{"status":N,"title":"…","key":"…"}`.
