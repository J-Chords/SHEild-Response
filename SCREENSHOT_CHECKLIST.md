# SHEild Response screenshot checklist

Use a browser viewport of **1366 × 768** for the final report unless a mobile comparison is specifically required. Hide browser bookmarks, notifications and unrelated tabs. Use only fictional demo records. Do not capture the final Home/Login photography images until the five approved local image files have been supplied.

| # | Filename | Account | Recommended URL | What should be visible | Privacy check |
|---:|---|---|---|---|---|
| 01 | `01-home-page.png` | Public | `/` | Hero, academic-prototype notice, report/support/SOS actions, Quick Exit | No case information; wait for final photography |
| 02 | `02-login.png` | Public | `/auth/login` | Branded login form and demo-account disclosure | Do not show a typed password; wait for final photography |
| 03 | `03-reporter-dashboard.png` | Reporter | `/reporter/dashboard` | Metrics, recent cases, latest updates, SOS and report CTAs | Use fictional references only |
| 04 | `04-new-incident-form.png` | Reporter | `/reporter/reports/new` | Multi-section form, safety indicators and privacy explanation | Leave description free of names/addresses |
| 05 | `05-report-confirmation.png` | Reporter | Redirect after normal report submission | New SHR reference, risk, status and prototype warning | Use a newly submitted fictional report |
| 06 | `06-my-reports.png` | Reporter | `/reporter/reports` | Filters, case references, risk/status badges | Fictional data only |
| 07 | `07-reporter-case-detail.png` | Reporter | Open a case from My Reports | Summary, assignment state, risk explanation and timeline | Internal notes must not appear |
| 08 | `08-sos-form.png` | Reporter | `/reporter/sos` | Short emergency form, deliberate warning, Cancel/Send actions | No real location or person details |
| 09 | `09-sos-confirmation.png` | Reporter | Redirect after SOS submission | Case reference, timestamp, CRITICAL/NEW and prototype warning | Use a newly submitted fictional SOS |
| 10 | `10-responder-dashboard.png` | Responder | `/responder/dashboard` | Emergency Queue, metrics, assigned and unassigned cases | Anonymous reporter identity must be absent |
| 11 | `11-emergency-queue.png` | Responder | `/responder/alerts` | NEW/ACKNOWLEDGED/RESPONDING/RESOLVED examples | Show references, not reporter identity |
| 12 | `12-responder-case-detail.png` | Responder | Open an assigned case | Case summary, transition/actions/forms and timeline | Prefer anonymous `SHR-2026-0105`; no reporter identity |
| 13 | `13-admin-dashboard.png` | Admin | `/admin/dashboard` | Page header, primary metrics, recent cases and alerts | No unnecessary reporter identity |
| 14 | `14-admin-analytics.png` | Admin | `/admin/dashboard` (chart section) | All six non-empty charts and legends | Values must come from SQLite |
| 15 | `15-admin-incidents.png` | Admin | `/admin/incidents` | Search/filters, assignment, risk/status/source columns | Use fictional case references |
| 16 | `16-user-management.png` | Admin | `/admin/users` | Roles, active/inactive state and search | Avoid highlighting emails beyond demo accounts |
| 17 | `17-responder-management.png` | Admin | `/admin/responders` | Two responders and distributed workload | Both identities must be labelled demo/fictional |
| 18 | `18-support-services.png` | Admin | `/admin/services` | Six fictional service types and active state | “Fictional demo entry” should be visible |
| 19 | `19-activity-log.png` | Admin | `/admin/activity` | Update type/visibility filters and mixed timeline entries | Anonymous case author must display as “Reporter” |

## Optional supporting screenshots

- `/admin/alerts` — emergency alert management.
- `/admin/contacts` — four fictional non-dialable demo contacts.
- `/support` — public fictional directory.
- Mobile navigation and Quick Exit at 390 × 844 after final photography is available.

Before capture, rerun `python -m flask --app app seed-final-demo`. The command is repeat-safe and restores the intended defence distribution without duplicating records.
