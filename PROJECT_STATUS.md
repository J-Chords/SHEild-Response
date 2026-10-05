# SHEild Response project status

Last updated: 5 October 2026

**Phase 1 status: complete and verified.**  
**Phase 2 status: complete and verified.**  
**Phase 3 status: complete and verified.**  
**Phase 4 status: complete and verified.**  
**Phase 5 status: complete and verified.**  
**Phase 6 status: complete and verified.**  
**Phase 7 status: complete and verified.**

## Implemented

- Clean Flask application factory with five blueprints: public, authentication, reporter, responder and administrator.
- SQLite/SQLAlchemy models for users, incidents, emergency alerts, case updates, support services and emergency contacts.
- Automatic local database creation and repeat-safe fictional seed data, with an explicit `seed-demo` CLI command.
- Werkzeug password hashing, Flask-Login sessions, CSRF protection, role decorators and ownership checks.
- Public case references in `SHR-YYYY-NNNN` format and separate `SOS-YYYY-NNNN` references.
- Reporter registration, login, forgot-password UI placeholder, profile, dashboard, report submission, anonymous responder-view preference, report history, timeline and emergency SOS submission.
- Responder dashboard, claimable queue, status/risk filters, case claiming, response actions, internal/reporter-visible notes and SOS progress queue.
- Admin dashboard analytics, incident search/assignment, user access management, responder-account creation, and add/edit/visibility management for support services and emergency contacts.
- Shared responsive design system, semantic status badges, keyboard focus states, reduced-motion handling, mobile layouts and error pages.
- Persistent Quick Exit link and `Shift+Escape` keyboard shortcut.
- Photography-ready panels with attractive built-in fallbacks and a final asset brief.
- Automated tests for public pages, authentication, role isolation, report creation and responder access.
- Reporter dashboard metrics, recent cases, latest reporter-visible updates and support-directory shortcut backed by live account-scoped data.
- Multi-section incident form with five safety indicators, safe contact preference and anonymous responder-view option.
- Dedicated deterministic risk-assessment service with documented scoring and explanations.
- Professional report confirmation, filtered My Reports view, assignment-safe case detail and vertical case timeline.
- Direct-object authorization tests preventing reporters from reading another reporter's case or confirmation page.
- Emergency SOS workflow: a short dedicated form (emergency category, brief description, general location, immediate-danger toggle, anonymous preference, explicit consent) atomically creates a linked CRITICAL-risk incident (public `SHR-YYYY-NNNN` reference), a `NEW` emergency alert and a case-timeline entry in a single transaction, with a deliberate "Cancel" vs "Send Emergency Request" confirmation step and a dedicated confirmation page (case reference, submission timestamp, Risk: CRITICAL, Emergency status: NEW, and View Case / Support Resources / Return to Dashboard actions).
- SOS cases respect the reporter's own anonymous preference exactly like normal reports — anonymity is never forced on or off by the emergency pathway.
- Unauthenticated visitors who press the public landing page's "Send Emergency Request" button are routed through a dedicated emergency-access page (clear prototype explanation, Login/Create account), and their intent to reach the SOS form is preserved end-to-end via a safe `next` redirect through both login and registration.
- "Emergency SOS" is now a prominent, danger-styled action in the primary site navigation (available on every page, including the mobile hamburger menu) for signed-in reporters and signed-out visitors alike, in addition to the landing-page emergency strip and the reporter dashboard navigation.
- Responder and administrator alert views (queue, detail and dashboards) show each emergency alert's linked case reference, emergency category and CRITICAL risk indicator, without exposing reporter identity when the case is anonymous.
- New administrator "Emergency alerts" page and dashboard sections (a "New SOS alerts" count of alerts awaiting first response, plus a recent-alerts table) give admins the same SOS visibility responders already had.
- "Emergency SOS" badges and flags mark SOS-originated cases across reporter, responder and admin case views and tables.
- Fixed the unassigned responder case queue, which previously sorted risk level alphabetically (so CRITICAL cases sorted last); it now sorts by true severity, so emergency-originated cases surface first.
- Added a colocated `shield/static/images/README.md` cataloguing every public-facing image slot (filename, ideal subject, orientation, recommended dimensions and where it appears), alongside the existing CSS-driven graceful fallbacks so missing photography never breaks layout.
- Responder workspace rebuilt into a full case-management system. Dashboard shows six live metrics (new emergency alerts, critical active cases, my assigned/in-progress/referred/resolved) above four panels in priority order: Emergency Queue, My Assigned Cases, Unassigned Priority Cases, Recent Activity.
- Emergency queue and case queue both gained real filters (status, assignment, risk, category, source, date where applicable) and reference search, with anonymity preserved throughout.
- Emergency alert lifecycle: dedicated **Acknowledge** / **Start Response** / **Resolve Emergency** actions (not a generic status dropdown). Acknowledging assigns the responder and the linked case, stamps `acknowledged_at`, and logs a timeline entry; starting response moves the alert to `RESPONDING` and the linked incident to `IN_PROGRESS`; resolving the alert only resolves the *alert* — it deliberately does not close the incident, and the UI copy says so explicitly.
- Case status changes are now governed by an explicit allowed-transition helper (`shield/services/case_transitions.py`), enforced both by restricting the status dropdown's options and by a server-side check — a responder cannot jump a case to an arbitrary status. Admin is intentionally not bound by this helper in Phase 4.
- Four new deliberate responder actions on the case-detail page, each its own small form in a collapsible disclosure: **internal note** (never shown to the reporter), **update for reporter** (appears in their timeline), **response action** (a typed operational log: contact attempt, safety check, referral, medical/counselling/legal referral, follow-up scheduled, other), and **referral** (selects a real fictional `SupportService` record, optionally moves the case to `REFERRED`).
- `CaseUpdate` gained an explicit `visibility` classification (`INTERNAL` / `REPORTER_VISIBLE` / `SYSTEM`) alongside the existing `visible_to_reporter` boolean (kept in sync, so existing reporter-facing filtering continues to work unchanged), plus an optional link to the referred `SupportService`.
- Claiming a case that was claimed by someone else a moment earlier now redirects with a clear "already claimed" message instead of a bare 403, while direct deep-links into another responder's case remain a hard 403.
- Fixed the Nigeria-specific "112" emergency-number reference on the SOS page per explicit instruction; replaced with neutral wording and a neutral icon.
- Admin dashboard rebuilt into a real operational analytics view: nine live metrics (total reports, active/critical-active cases, new SOS alerts, in-progress/referred/resolved, registered reporters, active responders) and six Chart.js charts (incidents by category, by risk level, cases by status, reports over time — last 6 months, zero-filled, report source, emergency alert status), all computed from SQLite with the chart data embedded as a page-local JSON blob (no public analytics API).
- Admin incident, alert, user and new activity lists share one consistent filter-bar pattern (search + selects + a "Clear filters" link) and simple `paginate()`-based pagination; incidents gained source/anonymous columns and responder/assignment/category/source filters; alerts gained responder and date filters.
- Admin can now deliberately **assign** or **reassign** a case to a responder from the case-detail page; the system distinguishes first assignment, reassignment and unassignment, records a matching audit-trail `CaseUpdate` for each, and never silently overwrites or deletes prior assignment history.
- New dedicated **Responder management** page (workload: total/active/critical/resolved assigned cases per responder, with activate/deactivate and a link into their filtered case queue) and a new **Activity log** page (every `CaseUpdate` across the system, filterable by case reference, update type, visibility and date) — both new, authorised-admin-only operational views.
- Admin case detail now also shows safety indicators, the linked emergency alert (if the case originated from SOS) and the complete timeline (internal notes, referrals, responder actions) — while a caught-and-fixed privacy bug means the audit trail never names a reporter on an anonymous case, even for the reporter's own "report received" entry (see Known issues).
- Login now gives a specific "This account has been deactivated" message instead of a generic "not recognised" error, satisfying the explicit friendly-message requirement without weakening the existing self-deactivation guard (an admin can never deactivate their own account, a simpler and strictly safer rule than conditionally allowing it when other admins exist).
- Support-service and emergency-contact management pages now carry an explicit "Fictional demo entry" label and a stronger prototype-responsibility notice, satisfying the demo-labelling requirement without adding a schema `is_demo` flag the existing architecture didn't need.
- **Chart.js is now vendored locally** (`shield/static/vendor/chartjs/chart.umd.min.js`, v4.4.4, MIT-licensed, with a copy of the licence alongside it) instead of loaded from a CDN. The admin dashboard, and the whole application, now loads with zero network requests to any remote host — verified with real internet disconnected from the page's perspective (no CDN/font/script requests of any kind leave the browser).
- A real visual QA pass (not just a code read) found and fixed five genuine, previously-shipped bugs: (1) dark-on-dark unreadable text in the home page's "Practical options" panel, caused by a CSS rule order/specificity bug; (2) the header's "Emergency SOS" and "Create account" nav buttons were rendering with transparent backgrounds and near-invisible text — a CSS specificity collision made them functionally invisible on every page, including the hamburger menu, since Phase 3; (3) a "View queue" link on the responder dashboard could wrap and visually collide with the floating Quick Exit button; (4) the responder case-detail page stacks five WTForms sharing field names like "note", which rendered five duplicate `id="note"`/`id="csrf_token"` attributes — invalid HTML that silently broke every `<label for="note">` association on that page; fixed with per-form WTForms prefixes. (5) Admin/responder/operational tables were shrinking to fit narrow mobile screens instead of scrolling, producing cramped, hard-to-read columns; fixed with a mobile-only `min-width` so they now scroll horizontally inside their existing container as intended.
- Error pages (403/404/500) now offer a context-appropriate "Return to dashboard" action alongside "Return home" when the visitor is signed in.
- Deleted four genuinely dead Phase-1 reporter templates (superseded by the `_phase2` versions since Phase 2, confirmed unreferenced by any route, include or test before removal).
- Added lightweight submit-button feedback (disables the button and shows "Submitting…" after a valid submit) across every form site-wide, with a `:disabled` button style; this cannot interfere with server-side validation retries since it never calls `preventDefault()` and the disabled state does not survive a real page reload.
- Confirmed, rather than assumed: no absolute privacy/security claims ("100% secure", "completely anonymous", etc.) exist anywhere in the copy; existing wording was already appropriately qualified from earlier phases.

## Phase 7 additions

- Added repeat-safe `seed-final-demo` CLI workflow with 15 canonical defence cases, four linked SOS alerts, a second fictional responder, six active fictional services, four non-dialable fictional contacts, selected rich timelines and intentional six-month/category/risk/status/workload distributions.
- Added `DEFENCE_DEMO_GUIDE.md` and `SCREENSHOT_CHECKLIST.md` for a concise presentation and reproducible 1366 × 768 report captures.
- Audited legacy `@shield.demo` accounts before cleanup: relationship-bearing accounts were deactivated; only the dependency-free legacy responder was removed. A verified pre-Phase-7 database backup is retained in `instance/backups/`.
- Removed the uniquely identified obsolete unlinked baseline alert (`SOS-…-0001`) during final seeding; all four active defence alerts are now linked to CRITICAL SOS incidents. Normal baseline seeding still creates its original alert for isolated tests until the final-demo marker exists.

## Currently working on

- No software phase is currently open. The completed application is ready for final photography and report screenshots.

## Remaining / recommended future work

- Replace fallback panels with licensed photographs described in `IMAGE_ASSETS_NEEDED.md`.
- Connect password recovery and verified email change flows to a privacy-reviewed email provider.
- Add invitation-based responder onboarding instead of sharing temporary passwords manually.
- Add pagination for large datasets and CSV/PDF exports with an explicit privacy review.
- Add database migrations with Flask-Migrate before changing production-like schemas.
- Conduct specialist accessibility, safeguarding, security and data-protection reviews before any real-world pilot.
- Before any real-world deployment, replace fictional demo contacts with independently verified, jurisdiction-specific services.
- Add final licensed photography (see "Image files still required" below) — the only remaining item from the Phase 6 brief, deliberately left to the project owner since it requires real, rights-cleared images.
- Consider a small visual pass on "View cases → / Disable" stacking on the responder-management table, and on the admin incidents filter bar's density at very narrow widths — both cosmetic, non-blocking.

## Image files still required

None of these exist yet; every reference below already has a working CSS gradient-and-icon fallback, so the site looks complete without them, but final photography would meaningfully improve the defence screenshots. See `shield/static/images/README.md` for the full brief (subject, orientation, dimensions, placement) on each:

- `hero-women-support.jpg` — home page hero panel
- `community-support.jpg` — home page "Support beyond reporting" split section
- `professional-woman.jpg` — reserved for a future about/responder panel
- `safe-family.jpg` — reserved for a future family-safety/referral feature
- `support-team.jpg` — reserved for a future about/responder-training section

## Known issues and limitations

- This is a local academic demonstration, not a live emergency system.
- Quick Exit cannot erase browser history or evade device/network monitoring.
- SQLite and the automatic seed/database setup are intended for a single-machine demonstration.
- The current sequence generator is suitable for a local prototype; a deployed multi-worker system would need transactional reference allocation.
- No email, SMS, geolocation, map, police, hospital, NGO or emergency-dispatch integration exists.
- Pagination uses simple offset-based `paginate()` on incidents, users and the activity log; fine for prototype data volumes, not tuned for very large tables.
- Three relationship-bearing legacy `@shield.demo` accounts remain inactive to preserve historical foreign-key relationships. The dependency-free `zainab@shield.demo` account was intentionally removed by the final-demo cleanup routine after a database backup was verified.

## Verification

- Automated suite: 75 tests passing on Python 3.14.6 (63 from Phases 1–5 plus 12 new Phase 6 tests covering: response-action recording, no-duplicate-ids regression guard on the case-detail page, Chart.js served locally with zero CDN references anywhere in the codebase, every public/reporter/responder/admin page loading cleanly, expected navigation destinations present, Quick Exit present on every sensitive page, branded error pages with context-appropriate actions, and anonymous-identity protection across admin case detail *and* the new activity log).
- Phase 5 (42 from Phases 1–4 plus 21 Phase 5 tests) covering: admin dashboard load and metric/analytics correctness against live database values, reporter/responder lockout from every admin route, incident search/filtering, deliberate assignment and reassignment with distinct audit-trail entries for each, user listing with no authentication internals leaked, responder creation with hashed passwords and duplicate-email rejection, deactivate/login-denied/reactivate, admin self-deactivation guard, support-service and emergency-contact create/edit/toggle with reporter-directory visibility sync, the activity log's visibility filtering, anonymous-identity protection surviving admin operations, CSRF enforcement on admin state-changing routes, and that public registration / admin-created accounts cannot have their role manipulated by extra form fields).
- While writing the Phase 5 tests, one genuine privacy regression was caught and fixed before it shipped: the new admin audit timeline initially showed `update.author.full_name` for every entry, which — for an anonymous case's own "report received" entry (authored by the reporter) — would have printed the reporter's real name. Fixed with a shared `update_author_label()` helper that substitutes "Reporter" whenever the update's author is the case's own reporter on an anonymous case; covered by `test_y` and re-verified live.
- Python source compilation: passed.
- Live startup: `python app.py` served the home page at `http://127.0.0.1:5000` with HTTP 200.
- Confirmed the rendered home page contains the academic-prototype notice and persistent Quick Exit control.
- Confirmed all three specified demo accounts authenticate and redirect to their correct role dashboards.
- Applied and verified all five Phase 2 incident columns against the persistent SQLite database.
- Submitted fictional incident `SHR-2026-0002` through the live UI and confirmed persistence, critical risk classification, filtered My Reports visibility, case timeline and risk explanation.
- Confirmed direct-object authorization and anonymous responder-view protections through automated tests.
- Live-verified, against the running app and the SQLite database directly: the unauthenticated emergency-access gate preserving intent through login (lands back on the SOS form), the short SOS form's fields and literal confirmation-page content, an anonymous SOS case correctly hiding reporter identity from the responder case view while still surfacing category and CRITICAL risk, and both responder and admin dashboards/queues showing the new case.
- Live-verified the full Phase 4 responder workflow against the running app with real CSRF protection active: created one normal case and one SOS case as the reporter; as the responder, claimed the normal case, acknowledged and progressed the SOS emergency through Responding, added an internal note and a reporter-visible update, recorded a referral against the seeded "Safe Harbour Support Centre" service, and moved the case to Referred; confirmed the admin dashboard reflected the new critical case; then logged back in as the reporter and confirmed the reporter-visible update and Referred status were visible while the internal note and referral details were not, and confirmed a separately submitted anonymous case stayed anonymous (no name or email) throughout the same claim/note workflow.
- Backed up and restored the existing local demo database around manual live testing so no extra fictional records were left behind; confirmed the repeat-safe schema-upgrade mechanism re-applies new columns (including backfilling `CaseUpdate.visibility` from the existing `visible_to_reporter` values) automatically on next startup without any data loss.
- Live-verified the full Phase 5 admin workflow against the running app with real CSRF protection active, following all 19 prescribed manual-verification steps: dashboard metrics and all six charts confirmed to reflect live database values (read the embedded JSON chart data directly); filtered incidents by reference; assigned an unassigned case to a responder, then deliberately reassigned it to a newly created fictional responder (both steps produced separate, distinct timeline entries); created that responder, logged in as them, deactivated them (friendly "deactivated" login message confirmed, dashboard unreachable), then reactivated them (login restored); created a fictional support service and confirmed it appeared on the public `/support` page, then deactivated it and confirmed it disappeared; did the same create/confirm/deactivate/confirm cycle for a fictional emergency contact; reviewed the admin activity log (case references, assignment/reassignment entries, visibility tags all present); and confirmed a freshly submitted anonymous case showed "Anonymous Report"/"Anonymous report" with no reporter name or email in the admin case view, the admin activity log, and the responder case view. Restored the database to its original baseline afterward; no schema changes were needed in Phase 5 (all new functionality is query/presentation logic over the existing columns).
- Phase 6 used a real headless-browser visual QA pass (Playwright, installed temporarily for this purpose only and removed again afterward — not a project dependency) rather than a code-only review: screenshotted every major public/reporter/responder/admin page at 1366×768 (the target defence resolution) and 390×844 (mobile), checked the browser console and network tab for errors on each, and confirmed zero JavaScript errors, zero unexpected 404s (the two expected ones are the not-yet-supplied `hero-women-support.jpg`/`community-support.jpg`, which fall back gracefully by design) and zero remote network requests anywhere in the app. This is how the five bugs listed above were actually found, not inferred from reading CSS. Verified the mobile hamburger menu, the demo-resolution admin dashboard with charts, and real end-to-end form submission (login → navigate → fill → submit → flash message → rendered result) through the browser, not just the test client.

### Phase 7 verification

- Baseline: 75/75 tests passed before any Phase 7 change.
- Final suite: 83/83 tests passed, including repeat safety, canonical hashed accounts, distribution quality, linked SOS integrity, both responder workloads, meaningful chart inputs, legacy cleanup and anonymous operational-view protection.
- Live `seed-final-demo` ran twice without duplicate users, cases, alerts, updates, services or contacts.
- Resulting SQLite data: 17 cases (13 normal / 4 SOS), nine categories, all four risks, all seven case statuses, six populated months, all four alert statuses, 6/5 cases across the two active responders and five unassigned cases.
- Live route QA: all public, reporter, responder and administrator pages in the Phase 7 checklist returned HTTP 200 using the seeded persistent database; Emergency Access correctly resolves at `/emergency`.
- Live security QA: reporter-to-responder, reporter-to-admin and responder-to-admin access returned 403; unsigned logout POST returned 400; dependent legacy account login was denied as deactivated; anonymous reporter identity and internal notes were absent from reporter/responder/admin operational responses as applicable.
- Offline QA: Chart.js loads from `shield/static/vendor/chartjs/chart.umd.min.js`; all six chart datasets were present in page-local JSON; no remote scripts, fonts or images are required; Playwright/Selenium were not added.
- Public directory QA: four active contacts use non-dialable `DEMO-*` values, all active services/contacts are explicitly fictional, and the unverified legacy `112` entry is inactive and absent from the public page.

## Demo accounts

- Reporter: `demo@sheild.local` / `Demo123!`
- Responder: `responder@sheild.local` / `Responder123!`
- Additional responder: `responder2@sheild.local` / `Responder2Pass!`
- Administrator: `admin@sheild.local` / `Admin123!`

## Final completion status

- **Core application development: COMPLETE**
- **Final QA: COMPLETE**
- **Remaining external task:** insert the five approved local photography files, capture final screenshots, and update the academic report.
