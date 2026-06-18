# Websupport — register / buy a domain (.sk and others)

**.sk is supported.** Buying happens in v1 under "Ordering new services". `check`
(validate) is free; **order spends money/credit — confirm with the user first**
(exact domain, period, registrant profile).

Markets (`<market>` for `validate`/`prices`) = storefront country: `sk | cz | hu | at`.
Independent of the TLD — buy `.com`/`.eu` via the `sk` market.

## 5-step flow

```bash
P=~/.claude/skills/websupport/scripts/ws_api.py
```

### 1. (optional) See TLDs + prices
`GET /v1/order/<market>`
```bash
python3 "$P" prices --market sk
```
Returns `[{ "type":"domain", "prices":[{"tld":"sk","price":9.9,"priceWithVat":12.18}, …] }, …]`
plus `vps`/`credit` types.

### 2. (once) Registrant identity — a "domain profile"
List/create with `/v1/user/self/domainProfile`.
```bash
python3 "$P" profiles                                   # GET — reuse an existing id
python3 "$P" post /v1/user/self/domainProfile --data '{
  "firstName":"Meno","lastName":"Priezvisko",
  "orgName":"Firma, s.r.o.",
  "street":"Ulica 12","city":"Bratislava","zip":"851 07","country":"SK",
  "phone":"+421900123456","email":"ja@example.com",
  "identCompanyRegistration":"12345678"
}'
```
Returns `item.id` = the `domainProfileId` (used below as `12345` — substitute yours).
- **Individual**: firstName + lastName + full address + email + phone (+ ident field if SK-NIC requires).
- **Company .sk**: also `orgName` + `identCompanyRegistration` (IČO).
- Other ident fields: `identBirthday`, `identVat`, `identPassport`, `identIdentityCard`
  ("required for registration of some tlds"). Missing-required → returned in `errors`.
- Profile endpoints: `GET/POST /v1/user/self/domainProfile`, `GET/PUT/DELETE /v1/user/self/domainProfile/<id>`.

### 3. Validate availability (free, no order)
`POST /v1/order/<market>/validate/domain`
```bash
python3 "$P" check mojadomena.sk --profile 12345
# == post /v1/order/sk/validate/domain --data '{"domain":"mojadomena.sk","domainProfileId":12345}'
```
Available →
```json
{"status":"success","item":{"domain":"mojadomena.sk","price":9.9,"priceWithVat":12.18,
 "currency":"eur","period":1,"periodLength":"year","domainProfileId":12345},"errors":[]}
```
Taken → `{"status":"error", …, "errors":{"domain":["Domain is taken."]}}`.
Optional body fields: `dnsServers` (`;`-separated, e.g. `ns1.websupport.sk;ns2.websupport.sk`),
`domainProfileId`, `contactId`.

### 4. Order (SPENDS MONEY — confirm first)
`POST /v1/user/self/order`
```bash
python3 "$P" post /v1/user/self/order --data '{
  "services":[{"type":"domain","domain":"mojadomena.sk","domainProfileId":12345,"period":1}],
  "note":"optional note to helpdesk"
}'
```
Success (HTTP 201): `item.id` = **order id**; per-service `sknicHandle` for .sk, plus
final `price`/`priceWithVat`. A service object accepts:
`{"type":"domain","domain":"x.sk","dnsServers":"","domainProfileId":155,"contactId":"","period":1}`.

### 5. Pay — a SEPARATE, separately-confirmed action
Payment is distinct from ordering. Re-show the order response's `priceWithVat` and get
a fresh explicit OK before paying — especially `byCredit`, which silently spends account
credit with no payment-gateway interstitial. Never chain order→pay in one unattended step.

Get hosted payment links:
`GET /v1/user/self/order/<orderId>/pay`
```json
{"tbtatrapay":"https://admin.websupport.sk/…/tatrapay",
 "tbcardpay":"https://admin.websupport.sk/…/creditCard-0",
 "vubeplatby":"…","comfortpay":"…"}
```
(Links appear a few seconds after the order; may be delayed if the order needs review.)
Or settle programmatically:
- `PUT /v1/user/self/order/<orderId>/pay/byCredit` — from account credit (check `whoami` → `credit`)
- `PUT /v1/user/self/order/<orderId>/pay/byPaymentCard/<paymentCardId>` — stored card

## Not fully documented
- Exact SK-NIC mandatory-ident matrix per individual/company — rely on `errors` from validate/order.
- `byCredit` / `byPaymentCard` request bodies (paths documented, bodies not shown — try `{}`).
- Meaning of the `suggest` boolean in the validate response.
