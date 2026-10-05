# SHEild Response defence demonstration guide

This is a concise 5–8 minute walkthrough. Keep the browser at approximately 1366 × 768 and start from a freshly seeded database.

## Before the defence

```powershell
cd D:\SHEild-Response
.\.venv\Scripts\Activate.ps1
python -m flask --app app seed-final-demo
python app.py
```

Open <http://127.0.0.1:5000>. All people, organisations, cases, contacts and phone-like values in the demonstration dataset are fictional.

## A. Public home page — 45 seconds

1. Open `/`.
2. Explain the purpose: a confidential digital pathway for GBV incident reporting, assistance requests and support tracking.
3. Point out the permanent **Academic prototype** notice: the system is not connected to police, hospitals, NGOs or dispatch services.
4. Show **Report Incident**, **Get Support**, **Emergency SOS** and the persistent **Quick Exit** control.
5. Briefly open `/support` to show that every listed organisation/contact is explicitly fictional.

## B. Reporter workflow — 90 seconds

Sign in with `demo@sheild.local` / `Demo123!`.

1. Show the reporter dashboard: total, active and resolved cases; recent cases; latest safe-to-share updates.
2. Open **Report Incident** and point out the calm multi-section form, minimal location request and safety indicators.
3. Explain the deterministic scoring: it is rules-based, not AI.
4. Select **Hide my identity from responder-facing views** to demonstrate the privacy option.
5. Submit a fictional normal report and show the generated `SHR-YEAR-XXXX` reference.
6. Open **My Reports**, use one filter, then open the new case and its reporter-visible timeline.

## C. Emergency SOS — 60 seconds

1. Choose **Emergency SOS** from the main navigation or reporter dashboard.
2. Read the deliberate warning: recording a request does not contact real emergency services.
3. Complete the short fictional request and select **Send Emergency Request**.
4. On confirmation, show the case reference, timestamp, `CRITICAL` risk and `NEW` alert status.
5. Explain that the operation atomically creates an Incident, EmergencyAlert and CaseUpdate.

## D. Responder workflow — 90 seconds

Sign out, then use `responder@sheild.local` / `Responder123!`.

1. Show the dashboard's Emergency Queue, critical count, assigned work and unassigned priority queue.
2. Open **Emergency Queue** and demonstrate **Acknowledge**, **Start Response** and **Resolve Emergency** on a fictional alert as time permits.
3. Open an assigned case and point out its controlled status transitions.
4. Add an **Internal Note** and explain that it is structurally excluded from reporter responses.
5. Add an **Update for Reporter** and explain that it appears on the reporter timeline.
6. Show a typed response action or fictional support-service referral.

Optional reassignment demonstration account: `responder2@sheild.local` / `Responder2Pass!`.

## E. Administrator workflow — 90 seconds

Sign out, then use `admin@sheild.local` / `Admin123!`.

1. Show the live metric cards and six SQLite-backed charts: category, risk, status, six-month trend, source and emergency-alert status.
2. Open **Incidents**, demonstrate filtering, and assign or reassign a fictional case between the two responders.
3. Show **Users** and **Responders**, including workload distribution and account activation controls.
4. Show **Emergency Alerts**, **Activity Log**, **Support Services** and **Emergency Contacts**.
5. Explain that assignment changes and operational actions remain in the timeline/audit history.

## F. Security and privacy close — 45 seconds

Conclude with:

- passwords use Werkzeug hashes; no plaintext passwords are stored;
- Flask-Login roles and server-side ownership checks protect routes and case IDs;
- Flask-WTF CSRF protects state-changing forms;
- anonymous reports retain internal ownership for tracking but hide reporter identity in operational views;
- internal notes never reach reporter-facing queries;
- Quick Exit navigates away but does not claim to erase browser history;
- risk scoring is deterministic and explainable, not AI;
- SOS remains an academic workflow and never contacts real emergency services.

Stop after the security summary and invite questions. Do not imply the fictional contacts or organisations are real.
