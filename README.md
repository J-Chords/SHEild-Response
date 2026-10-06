# SHEild Response

**Project Title:** Design and Development of an Emergency Response System for Gender-Based Violence and Femicide Prevention  
**Application Name:** SHEild Response  
**Student:** Blessed Atumkezi Wa Kumche  
**Registration Number:** ICTU20212614  
**Supervisor:** Engr. Nkiamboh Tanwi  

SHEild Response is a web-based academic prototype designed to demonstrate a structured workflow for reporting gender-based violence (GBV) incidents, creating emergency SOS requests, prioritising cases, managing responder actions, tracking case status, and providing administrative oversight.

> **Important safety notice:** SHEild Response is an academic prototype. It is **not connected to police, hospitals, NGOs, ambulance services, or any real emergency dispatch system**. Use fictional/demo information only.

---

## 1. Main Features

### Reporter

- Register and sign in securely
- Submit a GBV incident report
- Submit an optional anonymous report
- Send an emergency SOS request
- Receive a public case reference such as `SHR-2026-0001`
- Track personal reports and case status
- View safe reporter-visible case updates
- Access support services and emergency/support contacts
- Use the Quick Exit control on sensitive pages

### Responder

- View assigned and unassigned cases
- View the emergency queue
- Claim eligible cases
- Acknowledge emergency alerts
- Start emergency response
- Update case status through controlled transitions
- Add internal case notes
- Add reporter-visible updates
- Record response actions and referrals
- Resolve emergency alerts without automatically closing the whole case

### Administrator

- View operational statistics and charts
- Manage incidents and emergency alerts
- Assign or reassign responders
- Manage users and responder accounts
- Activate or deactivate accounts
- Manage support services and emergency contacts
- View responder workload
- Review system/case activity history
- View database-driven analytics

---

## 2. Technology Stack

The project uses:

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Werkzeug password hashing
- SQLite
- Jinja2
- HTML5
- CSS3
- Vanilla JavaScript
- Chart.js (stored locally for offline use)
- Pytest

The project does **not** require:

- Node.js
- npm
- React
- Docker
- PostgreSQL
- Firebase
- MongoDB

---

## 3. System Requirements

Before installing the project, make sure the computer has:

- Windows 10/11, macOS, or Linux
- Python 3 installed
- `pip` available
- A modern browser such as Chrome, Edge, or Firefox
- Approximately 500 MB free disk space for the project, virtual environment, and dependencies

For the easiest defence/demo setup, Windows with PowerShell is recommended because the project was developed and tested in that environment.

---

## 4. Project Folder

A typical project structure is:

```text
SHEild-Response/
|
|-- app.py
|-- requirements.txt
|-- README.md
|-- PROJECT_STATUS.md
|-- DEFENCE_DEMO_GUIDE.md
|-- SCREENSHOT_CHECKLIST.md
|-- .env.example
|-- .gitignore
|
|-- shield/
|   |-- __init__.py
|   |-- models.py
|   |-- forms.py
|   |-- schema.py
|   |-- seed.py
|   |-- final_demo.py
|   |
|   |-- auth/
|   |-- main/
|   |-- reporter/
|   |-- responder/
|   |-- admin/
|   |
|   |-- templates/
|   `-- static/
|       |-- css/
|       |-- js/
|       |-- images/
|       `-- vendor/
|
|-- instance/
|   `-- shield.db
|
`-- tests/
```

The exact internal file list may contain additional helper files, templates, tests, and documentation.

---

# INSTALLATION GUIDE

## 5. Windows Installation - Recommended

### Step 1: Copy or extract the project folder

Place the project anywhere on the computer. Example:

```text
D:\SHEild-Response
```

### Step 2: Open PowerShell in the project folder

```powershell
D:
cd D:\SHEild-Response
```

Confirm that `app.py` and `requirements.txt` are visible:

```powershell
Get-ChildItem
```

### Step 3: Create the Python virtual environment

If the project folder does not already contain a working `.venv`:

```powershell
py -m venv .venv
```

If `py` is unavailable, use:

```powershell
python -m venv .venv
```

### Step 4: Activate the virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

The terminal should now begin with something similar to:

```text
(.venv) PS D:\SHEild-Response>
```

If PowerShell blocks script execution, run this for the current terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 5: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Step 6: Install project dependencies

```powershell
pip install -r requirements.txt
```

Wait until installation completes without errors.

---

## 6. macOS / Linux Installation

Open a terminal inside the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The rest of the commands in this README can normally be run with `python` after the virtual environment has been activated.

---

# DATABASE AND DEMO DATA

## 7. Prepare the Final Demonstration Database

SHEild Response uses SQLite. The database file is normally located at:

```text
instance/shield.db
```

The project includes a repeat-safe final demo seed command:

```powershell
python -m flask --app app seed-final-demo
```

The command creates or confirms the final fictional demonstration data used by the dashboards.

It is designed to be repeat-safe, so running it again should not create duplicate canonical demo records.

The final demo data includes:

- multiple incident categories
- LOW, MEDIUM, HIGH, and CRITICAL risk cases
- cases in different workflow statuses
- normal reports and SOS reports
- multiple responders
- unassigned cases
- anonymous reports
- fictional support services
- fictional support contacts
- several months of data for analytics charts

> The seeded incidents are fictional demonstration data. They are not research respondents and must not be presented as real GBV case statistics.

---

## 8. Run the Automated Tests

Before starting the application, verify that the project passes its test suite:

```powershell
python -m pytest -q
```

The final verified project state passed:

```text
84 tests
```

If tests fail on another computer, first confirm that the virtual environment is active and all dependencies were installed from `requirements.txt`.

---

# RUNNING THE APPLICATION

## 9. Start SHEild Response

From the project folder, with the virtual environment active:

```powershell
python app.py
```

The terminal should show that Flask is serving the application locally.

Open a browser and go to:

```text
http://127.0.0.1:5000
```

Do not close the terminal while using the application. The Flask server must remain running.

To stop the application, return to the terminal and press:

```text
Ctrl + C
```

---

# DEMONSTRATION ACCOUNTS

## 10. Login Credentials

The final demonstration accounts are:

### Administrator

```text
Email: admin@sheild.local
Password: Admin123!
```

### Responder 1

```text
Email: responder@sheild.local
Password: Responder123!
```

### Responder 2

```text
Email: responder2@sheild.local
Password: Responder2Pass!
```

### Reporter

```text
Email: demo@sheild.local
Password: Demo123!
```

These credentials are for demonstration only.

Do not reuse them for a real deployment.

---

# HOW TO USE THE SYSTEM

## 11. Public/User Flow

From the home page, users can:

- read the purpose of SHEild Response
- select **Report an Incident**
- select **Get Support**
- select **Emergency SOS**
- sign in
- create a reporter account
- use **Quick Exit**

The public pages also state clearly that the system is an academic prototype.

---

## 12. Reporter Workflow

Sign in with:

```text
demo@sheild.local
Demo123!
```

### Submit a normal report

1. Open **Submit a report**.
2. Select an incident category.
3. Enter the incident date.
4. Enter a general location.
5. Enter a short description.
6. Complete the safety/risk questions.
7. Select anonymous reporting if required.
8. Submit the report.
9. The system generates a case reference in this format:

```text
SHR-2026-XXXX
```

10. Open **My reports** to track the case.

### Emergency SOS

1. Open **Emergency SOS**.
2. Read the prototype warning.
3. Complete the short emergency form.
4. Confirm the emergency request.
5. The system creates a CRITICAL case and linked emergency alert inside SHEild Response.

The SOS feature does **not** contact real emergency authorities.

---

## 13. Responder Workflow

Sign in with:

```text
responder@sheild.local
Responder123!
```

The Responder workspace allows the user to:

1. View the dashboard.
2. Review the **Emergency queue**.
3. Review the **Case queue**.
4. Claim an eligible unassigned case.
5. Open a case.
6. Acknowledge an emergency alert.
7. Start response work.
8. Change case status where allowed.
9. Add an internal note.
10. Add a reporter-visible update.
11. Record a referral or other response action.
12. Resolve an emergency alert when appropriate.

Internal notes are not shown to the Reporter.

---

## 14. Administrator Workflow

Sign in with:

```text
admin@sheild.local
Admin123!
```

The Administrator workspace allows the user to:

- view total reports and active cases
- view critical active cases
- view SOS alerts
- view charts and analytics
- search/filter incidents
- assign or reassign responders
- manage user accounts
- activate/deactivate users
- create responder accounts
- review responder workload
- manage support services
- manage emergency/support contacts
- review the activity log

The analytics are generated from SQLite and are not hardcoded.

---

# RISK CLASSIFICATION

## 15. Rules-Based Risk Model

SHEild Response uses a simple, transparent rule-based model.

Example scoring:

| Condition | Score |
|---|---:|
| Immediate danger | +4 |
| Threat to life | +4 |
| Weapon involved | +4 |
| Medical attention may be required | +2 |
| Dependants/children at immediate risk | +2 |

Classification:

| Total | Risk Level |
|---:|---|
| 0 | LOW |
| 1-3 | MEDIUM |
| 4-7 | HIGH |
| 8+ | CRITICAL |

SOS reports are treated as CRITICAL by design.

This is **not AI** and is not a professional clinical, legal, or forensic risk assessment.

---

# CASE AND EMERGENCY STATUSES

## 16. Case Statuses

Normal case workflow may include:

```text
RECEIVED
UNDER_REVIEW
RESPONDER_ASSIGNED
IN_PROGRESS
REFERRED
RESOLVED
CLOSED
```

## 17. Emergency Alert Statuses

```text
NEW
ACKNOWLEDGED
RESPONDING
RESOLVED
```

The emergency alert and the wider incident case have separate lifecycles. Resolving an immediate SOS alert does not necessarily close the entire case.

---

# SECURITY AND PRIVACY

## 18. Security Controls Included

The prototype includes:

- hashed passwords
- authenticated sessions
- role-based authorisation
- reporter case ownership checks
- CSRF protection
- anonymous-report presentation controls
- separate internal and reporter-visible updates
- inactive-account enforcement
- controlled case-status transitions
- Quick Exit functionality
- restricted administrator/responder routes

The project should still be treated as an academic prototype and not as a production GBV system.

A production deployment would require additional controls such as secure HTTPS hosting, hardened secret management, encrypted backups, formal governance, monitoring, professional service integration, verified emergency contacts, and legal/ethical review.

---

# OFFLINE DEMONSTRATION

## 19. Internet Connection

After Python dependencies have been installed, the main demonstration is designed to work locally without relying on remote frontend assets.

The project includes:

- local Chart.js
- local website photographs
- local CSS and JavaScript
- local SQLite database

Therefore, the primary application can be demonstrated without an active internet connection.

---

# COMMON COMMANDS

## 20. Quick Start - Windows

```powershell
cd D:\SHEild-Response
.\.venv\Scripts\Activate.ps1
python -m flask --app app seed-final-demo
python -m pytest -q
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## 21. Install From Scratch - Windows

```powershell
cd D:\SHEild-Response
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m flask --app app seed-final-demo
python -m pytest -q
python app.py
```

---

# TROUBLESHOOTING

## 22. `ModuleNotFoundError`

Make sure the virtual environment is active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then reinstall requirements:

```powershell
pip install -r requirements.txt
```

---

## 23. PowerShell Cannot Activate `.venv`

Use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This changes policy only for the current PowerShell process.

---

## 24. Port 5000 Is Already in Use

Stop the other process using port 5000, or close another running copy of the Flask application.

On Windows you can inspect the port with:

```powershell
netstat -ano | findstr :5000
```

Then stop the correct process if necessary.

---

## 25. Database Problems

The normal development database is:

```text
instance/shield.db
```

Before manually replacing or deleting the database, create a backup.

Example:

```powershell
Copy-Item .\instance\shield.db .\instance\shield-backup.db
```

Do not delete the database simply to solve an unrelated application error.

To ensure the demonstration data exist, run:

```powershell
python -m flask --app app seed-final-demo
```

---

## 26. Charts Do Not Display

Confirm this local file exists:

```text
shield/static/vendor/chartjs/chart.umd.min.js
```

The project should not require a Chart.js CDN connection.

---

## 27. Images Do Not Display

Confirm these files exist under:

```text
shield/static/images/
```

Expected final photography includes:

```text
hero-women-support.jpg
community-support.jpg
professional-woman.jpg
safe-family.jpg
support-team.jpg
```

Then refresh the browser using:

```text
Ctrl + F5
```

---

# FINAL DEFENCE CHECKLIST

## 28. Before Demonstrating the Project

Run:

```powershell
cd D:\SHEild-Response
.\.venv\Scripts\Activate.ps1
python -m flask --app app seed-final-demo
python -m pytest -q
python app.py
```

Confirm:

- the application opens at `http://127.0.0.1:5000`
- all final tests pass
- the home page loads correctly
- Reporter login works
- Responder login works
- Administrator login works
- charts display
- emergency queue contains demo data
- Quick Exit is visible
- support-service pages display only fictional/demo resources

For the full presentation order, read:

```text
DEFENCE_DEMO_GUIDE.md
```

---

# IMPORTANT PROJECT LIMITATIONS

## 29. Academic Prototype Limitations

SHEild Response currently:

- does not contact real emergency services
- does not automatically contact police or hospitals
- does not integrate live NGO networks
- does not send SMS or WhatsApp alerts
- does not perform live GPS tracking
- does not perform professional danger assessment
- does not use AI or machine learning for risk classification
- uses SQLite for local academic demonstration
- uses fictional support resources and demonstration cases

These limitations are intentional and must be clearly explained during the defence.

---

# DEVELOPMENT STATUS

## 30. Final Status

Core application development: **COMPLETE**  
Final QA: **COMPLETE**  
Final verified automated tests: **84 passed**  
Final photography integration: **COMPLETE**  

Remaining academic tasks may include final dissertation formatting, screenshots, source-code submission, and defence presentation preparation.

---

## 31. Disclaimer

SHEild Response was developed for academic demonstration as part of a Bachelor final-year project. It should not be relied upon during a real emergency and must not be deployed with real survivor information without substantial additional security, governance, service-provider integration, ethical review, and professional safeguarding procedures.
