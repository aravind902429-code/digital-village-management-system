# Digital Village Management System 🌿

An advanced, full-stack E-Governance Web Application built with **Python Flask**, **SQLAlchemy ORM**, and **Bootstrap 5**. Designed specifically for rural administration to digitize village governance, streamline certificate applications, automate civic complaint resolution, broadcast public announcements, and manage welfare schemes.

---

## 🌟 Key Features & Modules

### 1. Authentication & Security Module
- **Role-Based Access Control (RBAC):** Distinct dashboards and permissions for **Admin** (Gram Panchayat Officer) and **Villagers** (Residents).
- **Secure Credentials:** Password hashing and verification using industry-standard `Werkzeug.security` (PBKDF2 SHA-256).
- **Session Management:** Built on top of `Flask-Login` for secure user authentication and session persistence.

### 2. Villager Dashboard & Profile Management
- **Responsive Portal:** Interactive sidebar, summary statistics cards, and real-time activity tracking.
- **Digital Profile:** Residents can view and update their personal demographic information, contact numbers, and residential addresses.

### 3. Certificate Management Module
- **Online Applications:** Apply for Residence, Income, Community, Birth, and Death certificates with document verification attachments.
- **Status Tracking:** Live status updates (`Pending`, `Approved`, `Rejected`) with admin remarks.
- **Printable Acknowledgements:** Instant download and print generation of official certificates upon admin approval.

### 4. Complaint & Grievance Redressal Module
- **Civic Issue Reporting:** Categorized grievance filing (Water Supply, Street Light, Road Damage, Drainage, Electricity, Sanitation) with image upload support.
- **Workflow Resolution:** Track investigation progress from submission to resolution (`Pending` ➔ `In Progress` ➔ `Resolved`).

### 5. Government Schemes & Subsidies Module
- **Welfare Directory:** Explore agricultural grants, housing subsidies, and financial aid schemes with detailed eligibility criteria and benefits.
- **Instant Search & Bookmarking:** Keyword filtering and one-click "Save to Favourites" bookmarking for quick reference.

### 6. Circulars & Public Announcements Module
- **Live Broadcasts:** Village administration can publish emergency notices, Gram Sabha meeting circulars, and announcements directly to villager dashboards.
- **Draft & Publish Lifecycle:** Toggle publication status with instant dashboard updates.

### 7. Analytical Reports & Data Export Module
- **Real-Time Analytics:** Graphical data visualization using **Chart.js** displaying application approval ratios and grievance resolution status.
- **Multi-Format Exports:** Download comprehensive administrative summary reports as **CSV** or export cleanly as **PDF/Print**.

### 8. Global Portal Search & Custom Error Handlers
- **Unified Search:** Admin global search bar querying names, Aadhaar numbers, keywords, and categories across all modules simultaneously.
- **Tax Management Module:** Issue and track Property Tax, House Tax, and Water Tax bills. Residents can view dues, simulate secure online payments, and download official PDF/print receipts. Includes real-time tax revenue auditing and collection reports.
- **Professional Error Pages:** Custom **404 (Page Not Found)** and **500 (Internal Server Error)** layouts ensuring a smooth user experience.

---

## 🛠️ Technology Stack

- **Backend Framework:** Python 3 + Flask 3.0
- **Database ORM:** SQLAlchemy (`Flask-SQLAlchemy`) + SQLite (Easily swappable to MySQL via connection URI)
- **Frontend Styling:** HTML5, CSS3, Bootstrap 5.3, FontAwesome 6 Icons
- **Data Visualization:** Chart.js
- **Authentication:** Flask-Login, Werkzeug Security

---

## 📁 Architecture & Folder Structure

The application strictly adheres to the **Model-View-Controller (MVC)** architectural pattern:

```text
digital-village/
├── app.py                   # Application factory & Blueprint registration
├── config.py                # Configuration & Database URI settings
├── requirements.txt         # Project dependencies
├── test_phase6.py           # Phase 6 integration test suite
├── test_phase7.py           # Phase 7 Tax Management automated test suite
├── database/                # Database directory
│   └── digital_village.db   # SQLite database (auto-generated)
├── models/                  # Database Models (ORMs)
│   ├── __init__.py
│   ├── user.py              # User & Villager models
│   ├── certificate.py       # Certificate application model
│   ├── complaint.py         # Civic complaint model
│   ├── scheme.py            # Government scheme & Favourites association
│   ├── announcement.py      # Public announcement model
│   └── tax.py               # Tax assessment and payment receipt model
├── routes/                  # Controller Blueprints
│   ├── __init__.py
│   ├── main.py              # Home & public landing routes
│   ├── auth.py              # Login, register, logout routes
│   ├── villager.py          # Resident portal routes & logic
│   └── admin.py             # Administrative portal routes & logic
├── static/                  # Static Assets
│   ├── css/style.css        # Custom CSS styling & animations
│   └── js/script.js         # Frontend interactive logic & sidebar toggle
└── templates/               # HTML Views (Jinja2 Templates)
    ├── index.html           # Landing page
    ├── dashboard_base.html  # Main dashboard layout wrapper
    ├── 404.html             # Custom Not Found error page
    ├── 500.html             # Custom Internal Server Error page
    ├── admin/               # Admin views (Dashboards, Reports, Search, CRUD forms)
    └── villager/            # Villager views (Dashboards, Application forms, Lists)
```

---

## 🚀 Deployment & Local Installation Instructions

### Step 1: Clone or Navigate to the Project Directory
Ensure you have Python 3.8+ installed on your system. Open your terminal or PowerShell inside the project directory:
```powershell
cd path\to\digital-village
```

### Step 2: Create and Activate a Virtual Environment
It is recommended to use a virtual environment to isolate project dependencies:
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# (Or activate on Linux/macOS)
# source venv/bin/activate
```

### Step 3: Install Required Dependencies
Install all necessary Python packages listed in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
Start the Flask development server:
```powershell
python app.py
```
Upon startup, the system will automatically create the `database/digital_village.db` database and all required tables. The portal will be accessible at:
👉 **http://127.0.0.1:5000/**

---

## 🧪 Complete Testing Checklist

You can test the entire system automatically using the built-in test scripts (`python test_phase6.py`) or perform manual verification using the checklist below:

### ☑️ 1. Authentication & Role Security
- [ ] Access `http://127.0.0.1:5000/` and click **Join Now**.
- [ ] Register a new account and verify automatic redirection to login.
- [ ] Log in as Admin (`admin` / `admin123`) and verify redirect to **Admin Dashboard**.
- [ ] Attempt to access `/admin/dashboard` while logged in as a villager (Should deny access with flash alert).

### ☑️ 2. Profile & Dashboard
- [ ] In the Villager Portal, navigate to **Profile** and update Name, Mobile, and Address. Verify changes persist in the database.
- [ ] Check if summary cards on the dashboard accurately reflect your application and complaint counts.

### ☑️ 3. Certificates Module
- [ ] In the Villager Portal, click **Certificates** ➔ **Apply for Certificate**. Fill in details, attach a sample file, and submit.
- [ ] In the Admin Portal, navigate to **Certificates**, locate the pending request, review the attachment, change status to `Approved`, and add remarks.
- [ ] Log back in as Villager, check the approved status, and click **Download Acknowledgement** to verify the printable certificate view.

### ☑️ 4. Grievance & Complaint Redressal
- [ ] Submit a new complaint under **Water Supply** with a description and image attachment.
- [ ] In the Admin Portal, navigate to **Complaints**, filter by `Pending`, update status to `Resolved`, and verify dashboard statistics increment/decrement correctly.

### ☑️ 5. Government Schemes & Bookmarking
- [ ] In the Admin Portal, click **Gov Schemes** ➔ **Add New Scheme**. Provide banner image, eligibility, and benefits.
- [ ] In the Villager Portal, search for the scheme using keyword filtering.
- [ ] Click the heart icon (<i class="fa-regular fa-heart"></i>) to bookmark the scheme and check **Saved Schemes** tab.

### ☑️ 6. Announcements & Circulars
- [ ] In the Admin Portal, navigate to **Announcements** ➔ **Create Announcement**. Publish a notice.
- [ ] Check the **Villager Dashboard** to confirm the notice appears dynamically in the **Latest Announcements** feed.
- [ ] Toggle publication status in Admin to test hiding/showing circulars.

### ☑️ 7. Analytics Reports & Exports
- [ ] Navigate to **Analytics & Reports** (`/admin/reports`). Verify Chart.js graphical charts render for certificates and complaints.
- [ ] Click **Export CSV** and verify the instant download of `digital_village_report.csv`.
- [ ] Click **Print / Export PDF** and verify the clean report formatting.

### ☑️ 8. Global Portal Search
- [ ] In the Admin Portal, click **Global Search** and search for an applicant name, certificate type, or complaint category. Confirm results group cleanly across all modules.

---

## 📄 License & Credits
Built as a comprehensive, professional **College Mini Project** demonstrating Full-Stack Web Development, MVC Architecture, Database Design, and E-Governance Workflow Automation.
