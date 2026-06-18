# Security And UX Audit

Date: 2026-06-18

## Executive summary

This audit found several real implementation-level issues, not just polish gaps.

The highest-risk security issue is the current PII encryption design: it reuses deterministic nonces with AES-GCM, which breaks the security assumptions of the cipher and can expose relationships between repeated plaintexts. The second cluster of security issues is around trust boundaries: auth endpoints still return bearer tokens in JSON even though the app already uses HttpOnly cookies, CSP is weakened by `unsafe-inline` and a production `localhost` frame allowance, and the external-link checker can fetch attacker-controlled URLs without private-address guards.

On the UX side, there are at least two user-visible broken flows today: account deactivation cannot succeed because the frontend omits a required `confirm` body field, and Office preview is hardcoded to `http://localhost:8088`, which will fail outside a local developer machine. There are also trust-eroding experience issues such as a fake registration date on the profile page and an inaccessible login modal.

## Critical

### SEC-01

- Severity: Critical
- Rule ID: FASTAPI-AUTH-003 / cryptographic misuse
- Location: `scustack-api/app/core/security.py:17-27`
- Evidence:

```py
def _derive_nonce(plaintext: str) -> bytes:
    return hashlib.sha256(('pii_nonce:' + plaintext).encode()).digest()[:12]

def encrypt_pii(plaintext: str) -> str:
    nonce = _derive_nonce(plaintext)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
```

- Impact: AES-GCM requires nonce uniqueness per key. Reusing a deterministic nonce for equal plaintexts breaks confidentiality guarantees and can enable plaintext relation leakage and integrity compromise.
- Fix: Stop using deterministic nonces with AES-GCM. Use random nonces for encryption and store a separate keyed lookup field for search/equality, such as `HMAC(secret, normalized_value)`.
- Mitigation: Until redesigned, treat encrypted PII columns as weaker than expected and avoid expanding their use to more fields.
- False positive notes: None. This is a cryptographic design issue in the code shown.

## High

### SEC-02

- Severity: High
- Rule ID: FASTAPI-SESS-002 / token exposure
- Location: `scustack-api/app/api/v1/auth.py:98-103`, `124-126`, `147-148`, `173-178`, `316-321`; `scustack-web/composables/useAuth.ts:16-35`, `158-179`
- Evidence:

```py
response = JSONResponse({
    'code': 0,
    'data': TokenResponse(**tokens).model_dump(),
    'message': 'ok',
})
_set_token_cookies(response, tokens['access_token'], tokens['refresh_token'])
```

```ts
return $fetch<{ code: number; data: { access_token: string; refresh_token: string; token_type: string } | null; message: string }>(
  `${base}/api/v1/auth/login`,
```

- Impact: The system already authenticates with HttpOnly cookies, but still exposes access and refresh tokens to browser JavaScript. Any future XSS, debug logging, browser extension, or accidental client persistence would gain the tokens unnecessarily.
- Fix: Remove token payloads from auth JSON responses and return only user/session metadata plus cookie side effects.
- Mitigation: Audit the frontend to confirm no tokens are being persisted or logged today.
- False positive notes: This is not theoretical; the API shape explicitly returns the secrets.

### SEC-03

- Severity: High
- Rule ID: JS-CSP-001 / VUE-HEADERS-001
- Location: `scustack-api/app/middleware/security.py:18-29`
- Evidence:

```py
"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
"frame-src 'self' http://localhost:*; "
```

- Impact: The current CSP meaningfully weakens XSS defense with `unsafe-inline`, and it also permits framing content from `localhost` in production responses. That creates an unnecessary trust bridge to developer-local services and makes the policy much less valuable as a containment layer.
- Fix: Remove `unsafe-inline` from `script-src`, remove the `localhost` frame allowance outside dev, and move any required exceptions behind environment-specific config.
- Mitigation: If strict CSP rollout is hard, start with a report-only policy in staging and inventory inline script/style usage.
- False positive notes: If edge infrastructure overwrites CSP later, verify the runtime header before changing priority.

### UX-01

- Severity: High
- Location: `scustack-web/composables/useAuth.ts:137-141`, `scustack-web/pages/user/privacy.vue:130-137`, `scustack-api/app/api/v1/users.py:213-228`
- Evidence:

```ts
async function deactivateAccount() {
  return $fetch(`${base}/api/v1/me/deactivate`, { method: 'POST', credentials: 'include' })
}
```

```py
async def deactivate_account(body: DeactivateRequest, ...):
    if not body.confirm:
        return {'code': 40000, 'data': None, 'message': 'confirm must be true'}
```

- Impact: The visible “注销账户” flow cannot complete successfully because the frontend never sends the required confirmation body. Users will click through a destructive confirmation UI and still fail silently.
- Fix: Send `{ confirm: true }` from the frontend and surface backend errors to the user.
- Mitigation: Add an integration test that exercises the exact account deactivation flow from UI to API.
- False positive notes: None; the request contract is mismatched in code.

### UX-02

- Severity: High
- Location: `scustack-web/components/preview/OfficePreview.vue:35-37`
- Evidence:

```ts
const onlyofficeUrl = 'http://localhost:8088'
return `${onlyofficeUrl}/doceditor?directUrl=${encodeURIComponent(props.url)}&mode=view&lang=zh`
```

- Impact: Office preview depends on a hardcoded localhost service, so it will fail for real users in staging/production and for any developer not running that exact local stack.
- Fix: Move the document preview base URL into runtime config and provide an explicit fallback state when the preview service is unavailable.
- Mitigation: Hide the preview action when no preview backend is configured.
- False positive notes: If a reverse proxy rewrites this in production, that behavior is not visible in the repo.

## Medium

### SEC-04

- Severity: Medium
- Rule ID: FASTAPI-SSRF-001
- Location: `scustack-api/app/services/upload_service.py:138-170`, `scustack-api/app/tasks/link_check.py:41-51`, `77-94`
- Evidence:

```py
if parsed.scheme not in ('http', 'https'):
    return '仅支持 http/https 链接'
...
resp = await client.head(url)
```

- Impact: External links are only checked for scheme/domain blacklist and can still point to raw IPs, private hosts, or redirect chains. Once approved, the dead-link task will fetch them server-side, creating an SSRF surface against internal services or cloud metadata endpoints.
- Fix: Reject private, loopback, link-local, and metadata IP ranges; validate redirects; and consider allowlisting university/content hosts if the business model permits.
- Mitigation: Apply egress filtering at the network layer for Celery workers.
- False positive notes: Risk severity depends on deployment topology; it becomes much more serious inside a VPC or cloud network.

### SEC-05

- Severity: Medium
- Rule ID: FASTAPI-UPLOAD-001
- Location: `scustack-api/app/services/upload_service.py:63-67`, `87-95`, `204-294`; `scustack-api/app/tasks/material_tasks.py:5-35`, `38-76`; `scustack-api/app/api/v1/materials.py:76-84`
- Evidence:

```py
async def generate_upload_token(file_name: str, content_type: str, file_size: int) -> dict:
    validate_file_request(file_name, file_size)
```

```py
def security_scan(file_name: str, file_content: bytes) -> tuple[bool, list[str]]:
    ...
```

```py
from app.tasks.material_tasks import pre_screen_content
pre_screen_content.delay(str(m.id), m.title, m.description)
```

- Impact: The codebase contains file-content validation helpers and a virus-scan task, but the normal create-material path only schedules text keyword screening. That means the system largely trusts client-supplied metadata and presigned uploads before marking materials approved.
- Fix: Enforce server-side object verification after upload and before approval: verify actual object size/hash/type, run malware/content scanning, and gate publication on scan completion.
- Mitigation: At minimum, mark hosted uploads `pending` until asynchronous scan status becomes `clean`.
- False positive notes: Some validation may exist outside the repo in OSS callbacks, but nothing visible here enforces it.

### SEC-06

- Severity: Medium
- Rule ID: FASTAPI-CSRF-001
- Location: `scustack-web/composables/useAuth.ts:7-193`, `scustack-api/app/api/v1/auth.py:52-64`, `scustack-api/app/middleware/anti_proxy.py:34-58`
- Evidence:

```ts
credentials: 'include'
```

```py
response.set_cookie(... httponly=True, secure=SECURE, samesite='lax')
```

```py
if origin or referer:
    ...
if host and not _is_allowed_host(host):
    return JSONResponse(...)
```

- Impact: The app uses cookie-authenticated state-changing requests throughout, but protection currently relies on `SameSite` plus an Origin/Referer heuristic. Requests with neither header pass through, so the design is weaker than a true per-request CSRF token scheme for a public web app.
- Fix: Add a real CSRF token flow for state-changing cookie-auth requests and allow the corresponding header in CORS.
- Mitigation: Keep the current Origin/Referer checks as defense-in-depth even after adding tokens.
- False positive notes: This is not “no protection at all”; it is an incomplete protection model.

### UX-03

- Severity: Medium
- Location: `scustack-web/pages/user/profile.vue:21-23`, `234-236`
- Evidence:

```ts
<p class="text-xs text-slate-400 mt-0.5">
  注册于 {{ formatDate(auth.user.id) }}
</p>

function formatDate(_id: string) {
  return '2026年'
}
```

- Impact: The profile page displays fabricated account metadata, which weakens user trust and makes the account center feel unfinished even when the rest of the product is functional.
- Fix: Return `created_at` from the profile API and format the real date.
- Mitigation: Hide the field entirely until real data is available.
- False positive notes: None.

### UX-04

- Severity: Medium
- Location: `scustack-web/components/auth/LoginModal.vue:2-9`, `172-309`
- Evidence:

```vue
<Teleport to="body">
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="close">
```

- Impact: The login modal lacks `role="dialog"`, `aria-modal`, focus trapping, initial focus placement, and keyboard dismissal logic. Keyboard-only and screen-reader users are likely to lose context or interact with background UI while the modal is open.
- Fix: Add dialog semantics, trap focus inside the modal, restore focus on close, and support `Esc` consistently.
- Mitigation: At minimum, add `role="dialog"` and autofocus the first actionable field.
- False positive notes: Some keyboard behavior may come from global composables, but it is not visible in this component.

## Low

### UX-05

- Severity: Low
- Location: `scustack-web/pages/user/profile.vue:210-212`
- Evidence:

```ts
watch(() => auth.authChecked, (checked) => {
  if (checked && !auth.isLoggedIn) auth.openLogin()
})
```

- Impact: The page comment says it supports logged-in and logged-out states, but the watcher still forces the login modal for guests. That creates a confusing mixed mode where the page pretends to allow browsing while interrupting the user immediately.
- Fix: Either make the page truly guest-friendly or move auth enforcement to route middleware and remove the logged-out state.
- Mitigation: Delay the login prompt until the user tries a protected action.
- False positive notes: This may be intentional product behavior, but it conflicts with the current page structure and copy.
