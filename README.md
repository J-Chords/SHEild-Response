# SHEild Response

SHEild Response is a local academic prototype that demonstrates reporting, response and administration workflows for gender-based violence and femicide prevention. It is a Bachelor final-year project and is **not connected to police, hospitals, NGOs or any emergency dispatch service**.

## What the prototype includes

- Reporter registration, secure sign-in, profile, multi-section incident reporting, deterministic risk classification, anonymous responder-view option, filtered private case list, confirmation screen and timeline.
- Emergency SOS: a short dedicated form (category, brief description, location, immediate-danger toggle, anonymous preference) that, after a deliberate confirmation step, atomically creates a linked CRITICAL-priority incident, a `NEW` emergency alert and a timeline entry, with its own confirmation screen. Reachable from the landing page, the primary site navigation (incl. mobile menu) and the reporter dashboard; unauthenticated visitors are guided through sign-in/registration without losing their place.
- Responder case-management workspace: a data-driven dashboard (new-alert, critical, and caseload metrics; emergency queue; my cases; unassigned priority cases; recent activity), a filterable/searchable case queue and emergency queue, case claiming with race-safe conflict handling, an explicit allowed-status-transition model, internal notes (never reporter-visible), deliberate reporter-visible updates, typed response actions (contact attempt, safety check, referrals, follow-up), and referrals against the fictional support directory. Emergency alerts move through a dedicated Acknowledge → Start Response → Resolve lifecycle that updates the linked case without silently closing it.
- Administrator operations centre: nine live metric cards and six Chart.js charts (category, risk, status, a 6-month reports-over-time trend, report source, emergency alert status) computed directly from SQLite; filterable/searchable/paginated incident, user and activity lists; deliberate case assign/reassign with a full audit trail; a dedicated responder-management page showing per-responder workload; an activity log across every case's timeline; and editable support-service/emergency-contact directories that drive the public support page live.
- Hashed passwords, CSRF protection, role-based authorization, private reporter ownership checks and non-database public case references.
- Responsive, accessibility-conscious interface with persistent Quick Exit and graceful photography fallbacks. Runs entirely offline: no CDN, remote font or external script dependency anywhere in the application.
- Fictional seed data and clearly labelled prototype limitations.

## Technology

Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, SQLite, Jinja2, HTML, CSS, vanilla JavaScript and Chart.js v4.4.4 (vendored locally at `shield/static/vendor/chartjs/`, admin dashboard only — no CDN, no network access required to run the app).

## Local setup

From the repository root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open <http://127.0.0.1:5000>.

On macOS or Linux, activate the environment with `source .venv/bin/activate` and use the same install/run commands.

The SQLite database is created automatically at `instance/shield.db` on first run. Fictional demonstration records are checked and created by unique identifiers, so initialization is safe to run repeatedly without duplicate accounts or records.

To initialize or re-check the demo dataset explicitly:

```powershell
python -m flask --app app seed-demo
```

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Reporter | `demo@sheild.local` | `Demo123!` |
| Responder | `responder@sheild.local` | `Responder123!` |
| Administrator | `admin@sheild.local` | `Admin123!` |

These credentials are deliberately public for local assessment. Never reuse them in a deployed system.

## Running tests

```powershell
python -m pytest -q
```

## Configuration

- `SECRET_KEY`: session and CSRF signing secret. Change it outside local demonstration use.
- `DATABASE_URL`: optional SQLAlchemy URL; defaults to the instance SQLite database.
- `FLASK_DEBUG`: set to `1` only during local development.

## Important safety limitations

- SOS and report submissions stay inside the local SQLite database and do not alert any real service.
- Quick Exit replaces the current page with Google, but cannot clear browser history, network logs or monitoring software.
- Seed records and accounts are entirely fictional.
- Anonymous reporting in this prototype hides reporter identity from responder-facing case views, but preserves the internal account relationship so the reporter can track the case. Administrators and the database can still access that ownership relationship; this is not technical anonymity from the system operator. The emergency SOS form offers the same anonymous preference as a normal report, and it is honoured the same way.
- Risk classification is a deterministic rules-based priority aid, not AI and not a substitute for professional safeguarding judgement. Immediate danger, threats to life and weapon involvement add four points each; possible medical attention and dependant risk add two each. Scores map to low (0), medium (1–3), high (4–7) and critical (8+). Every emergency SOS case is classified CRITICAL by this same policy regardless of indicator score, because activating the SOS workflow is itself treated as the highest-priority signal.
- Real deployment would require verified jurisdiction-specific contacts, safeguarding governance, encryption/key management, retention policies, professional threat modelling, secure hosting, monitoring, audit review and specialist legal/ethical review.
- Claiming an already-claimed case redirects with a message rather than erroring, since two responders claiming the same case within moments of each other is an expected race in a shared queue, not a security violation; directly opening another responder's assigned case is still a hard 403. This is optimistic, not lock-based, concurrency control — acceptable for a single-machine academic prototype, not for a high-concurrency deployment.
- Admin incident, user and activity-log pagination uses simple SQLAlchemy `paginate()`; fine for prototype data volumes, not tuned for very large tables.

## Responder workflow and status models

**Case status** (`Incident.status`) follows an explicit allowed-transition map enforced by `shield/services/case_transitions.py` for responder-driven changes (admin is not bound by it in this phase):

```text
RECEIVED           -> UNDER_REVIEW, RESPONDER_ASSIGNED
UNDER_REVIEW        -> RESPONDER_ASSIGNED, IN_PROGRESS
RESPONDER_ASSIGNED  -> IN_PROGRESS
IN_PROGRESS         -> REFERRED, RESOLVED
REFERRED            -> IN_PROGRESS, RESOLVED
RESOLVED            -> CLOSED, IN_PROGRESS
CLOSED              -> (terminal for responders)
```

**Emergency alert status** (`EmergencyAlert.status`) is a separate, smaller lifecycle driven by three deliberate responder actions rather than a free status picker: **Acknowledge** (`NEW` → `ACKNOWLEDGED`, stamps `acknowledged_at`, assigns the responder and the linked case if unassigned), **Start Response** (→ `RESPONDING`, moves the linked incident to `IN_PROGRESS`), and **Resolve Emergency** (→ `RESOLVED`). Resolving the *alert* never automatically changes the linked *case's* status — the incident keeps whatever status the responder has given it (`IN_PROGRESS`, `REFERRED`, `RESOLVED`, …), and the UI copy says so explicitly, since "emergency alert resolved" and "entire case resolved" are different facts.

**Internal vs reporter-visible updates**: every `CaseUpdate` carries a `visibility` of `INTERNAL`, `REPORTER_VISIBLE` or `SYSTEM` (kept in sync with the pre-existing `visible_to_reporter` boolean). Reporter-facing routes only ever read entries where `visible_to_reporter` is true, so `INTERNAL` notes, response actions and referrals are structurally excluded from anything a reporter's browser receives — not merely hidden by CSS. Responders have four distinct, deliberate actions on a case: an internal note (staff-only), an update for the reporter (appears in their timeline), a typed response action (contact attempt, safety check, referral, medical/counselling/legal referral, follow-up — internal by default), and a referral against a real fictional `SupportService` record (internal by default, with its own optional "move to Referred" step). A responder who wants the reporter to know about a referral adds a separate reporter-visible update for that.

## Admin capabilities and account model

- **Analytics**: the dashboard's metrics and all six charts are computed live from SQLite on every request (`shield/admin/routes.py:_build_chart_data`) — nothing is hardcoded or estimated. Chart data is embedded as a page-local `<script type="application/json">` blob and rendered client-side by `shield/static/js/admin_dashboard.js`; there is no public analytics API endpoint.
- **Assignment vs reassignment**: assigning an unassigned case, reassigning an already-assigned case, and unassigning a case are each detected automatically from the previous vs new responder, and each creates its own distinctly labelled, permanent `CaseUpdate` entry (`ADMIN_ASSIGNMENT` / `ADMIN_REASSIGNMENT` / `ADMIN_UNASSIGNMENT`) — prior assignment history is never deleted or overwritten silently.
- **Account deactivation**: deactivating a user preserves every incident, assignment, update and audit relationship — accounts are never hard-deleted. A deactivated account's credentials still exist but `login()` now rejects them with a specific "This account has been deactivated" message rather than the generic invalid-credentials message. An admin can never deactivate their own account (a simple, unconditional rule — strictly safer than conditionally allowing it when other admins exist, since it removes any possibility of an accidental full admin lockout).
- **Responder management**: a dedicated page (`/admin/responders`) separate from the general user directory, showing each responder's total/active/critical/resolved assigned-case counts and a direct link into their filtered case queue, alongside the existing create-responder form (role is always hardcoded server-side to `RESPONDER`; it can't be elevated by a forged form field).
- **Support services & emergency contacts**: every entry is explicitly labelled "Fictional demo entry" in the admin UI (no schema change was needed — the existing fields and site-wide prototype messaging already make this clear). Toggling an entry's active status immediately changes what the public `/support` page and reporter dashboard show; inactive entries never reach reporters.
- **Activity log** (`/admin/activity`): every `CaseUpdate` across every case, filterable by case reference, update type, visibility (`INTERNAL` / `REPORTER_VISIBLE` / `SYSTEM`) and date. This is an authorised admin operational view and deliberately shows internal notes that reporters never see — but it never names a reporter on an anonymous case, even for that reporter's own timeline entries (see Responder workflow section below for how `visibility` works, and `update_author_label()` in `shield/models.py` for the anonymity guard).

## Offline readiness, accessibility and visual QA

- **Fully offline**: every script, stylesheet and font the app uses ships inside the repository. Chart.js is vendored at `shield/static/vendor/chartjs/chart.umd.min.js` (v4.4.4, MIT-licensed; licence text alongside it) instead of loaded from a CDN. There is no `<link>` to Google Fonts or any other remote host anywhere in the templates — the type stack (`Georgia`/serif and `Inter`/system-ui/sans-serif) falls back to the operating system's own fonts if `Inter` isn't installed, so nothing ever blocks on a network font request.
- **Accessibility practices in place**: a global `:focus-visible` outline plus a refined `.input:focus` state give every interactive element a visible keyboard focus ring; the mobile nav toggle and Quick Exit both expose accessible names (`aria-expanded`/`aria-controls` and a visually-hidden "Menu" label, or visible "Quick Exit" text); all decorative SVGs carry `aria-hidden="true"`; tables use proper `<thead>`/`<th>` structure; and every multi-form page (e.g. the responder case-detail screen, which stacks five separate forms) uses distinct WTForms `prefix` values so field ids and `<label for>` associations never collide — this is not just tidiness, it was a real, previously-shipped bug (see below).
- **No absolute privacy/security claims**: reviewed all reporter/anonymity copy for language like "100% secure" or "completely anonymous"; none was found — existing wording ("hides your identity from responder-facing views", "this prototype still stores account ownership internally") was already appropriately qualified from earlier phases.
- **Submit feedback**: every form's submit control disables itself and shows "Submitting…" immediately after a valid submit, to discourage accidental double-submission on a slow connection. This is pure client-side UX — it never calls `preventDefault()`, so a server-side validation error still reloads the page with the error shown and a fresh, enabled button (verified with an automated browser check, not just read from the code).
- **Real visual QA, not a code-only read**: Phase 6 used a headless browser (Playwright, installed temporarily for this pass and removed again afterward) to actually screenshot and inspect the rendered pages at 1366×768 (the target defence resolution) and 390×844 (mobile), and to check the browser console/network tab for errors. This found and fixed five genuine bugs that a code read alone had missed since earlier phases:
  1. Dark-on-dark, unreadable checklist text in the home page's "Practical options, without pressure" panel (a CSS rule-order bug).
  2. The header's "Emergency SOS" and "Create account" buttons rendered with a transparent background and near-invisible text on *every* page, including the mobile menu — a CSS specificity collision between the nav's link-reset rule and the `.button` system had made them functionally invisible since Phase 3.
  3. A "View queue" link on the responder dashboard could wrap and visually collide with the floating Quick Exit button.
  4. Duplicate HTML ids (`id="note"`, `id="csrf_token"`, `id="submit"` each appearing five times) on the responder case-detail page, which silently broke label-to-input association for every "Note" field on that page — fixed with WTForms `prefix=` per form.
  5. Admin/responder tables were shrinking to fit narrow mobile screens instead of scrolling, producing cramped, unreadable columns — fixed with a mobile-only `min-width` so they now scroll horizontally inside their existing container, with zero page-level horizontal overflow.
- **Dead code removed**: four Phase-1 reporter templates (`dashboard.html`, `new_report.html`, `reports.html`, `report_detail.html`) had been fully superseded by their `_phase2` counterparts since Phase 2 and were confirmed, via a repo-wide search, to be referenced by nothing — deleted.

## Project structure

```text
app.py
shield/
  admin/          administrator blueprint
  auth/           authentication blueprint
  main/           public pages blueprint
  reporter/       reporter workflow blueprint
  responder/      responder workflow blueprint
  static/         design system, JavaScript, vendored Chart.js and image slots (see static/images/README.md)
  templates/      inherited and role-specific Jinja templates
  models.py       SQLAlchemy data model
  forms.py        validated Flask-WTF forms
  seed.py         fictional demo dataset
tests/            application and authorization tests
instance/         local database (created at runtime, ignored by git)
```

See [IMAGE_ASSETS_NEEDED.md](IMAGE_ASSETS_NEEDED.md) for the final photography brief and [PROJECT_STATUS.md](PROJECT_STATUS.md) for implementation status.
