# ⚡ AutoTask - Python Automation System
> **Academic Project:** Task Automation with Python Scripts  
> **Course / Assignment:** Full-Stack Web Development & Python Automation Project  
> **Target Environment:** Windows 10/11, PyCharm, XAMPP (MySQL Server)

---

## 📖 1. Project Overview

**AutoTask** is a modern, responsive, full-stack web application developed using **Python, Django, and MySQL (via XAMPP)** that automates repetitive daily tasks. It provides beginner-friendly web interfaces to execute backend Python automation scripts, monitor execution logs, view status metrics, and download generated output files.

### 🎯 Key Project Features
1. **JPG File Organizer (`os`, `shutil`):**
   - Automatically moves `.jpg` and `.jpeg` images from a source directory to a destination directory.
   - **Non-Destructive Collision Handling:** If duplicate filenames exist in the destination folder, AutoTask appends an incremental suffix (e.g. `photo_1.jpg`) without silently overwriting.
   - **Safe Workspace Containment:** Strictly confines operations to an approved application workspace to prevent arbitrary filesystem traversal.

2. **Email Address Extractor (`re`, File I/O):**
   - Upload any plain text (`.txt`) file (up to 5 MB).
   - Extracts all RFC-compliant email addresses using regular expressions.
   - Automatically eliminates duplicate addresses while strictly **preserving original occurrence order**.
   - Generates a timestamped `.txt` output file available for immediate download.

3. **Webpage Title Scraper (`requests`, `BeautifulSoup4`):**
   - Scrapes and parses the `<title>` tag from any public webpage.
   - **Server-Side Request Forgery (SSRF) Defense:** Hardened DNS and IP address resolution that blocks loopback (`127.0.0.1`, `localhost`), private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), cloud metadata (`169.254.169.254`), and unsupported URI schemes (`file://`, `ftp://`).
   - Re-verifies IP addresses on every HTTP redirect hop.
   - Exports the title into a downloadable text file.

4. **Security & Session Management:**
   - Django built-in user authentication with secure password hashing (`PBKDF2`).
   - CSRF protection on all forms and asynchronous requests.
   - Strict data isolation: regular users only access their own history and files.
   - Dedicated Administrator Dashboard and Django Admin portal for staff.

---

## 🛠️ 2. Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (Modern ES6 Fetch API, Responsive Sidebar, Toast Alerts, Dropzone)
- **Backend:** Python 3.10+ / 3.14+, Django 5.x / 6.x
- **Database:** MySQL Server (managed via XAMPP) with PyMySQL driver
- **Libraries:** `requests`, `beautifulsoup4`, `python-dotenv`, `pymysql`
- **IDE / OS:** PyCharm (Community or Professional), Windows OS

---

## 📁 3. Project Directory Structure

```text
codealpha/
│
├── manage.py                     # Django management entry point
├── requirements.txt              # Project package dependencies
├── .env.example                  # Environment variable template
├── .env                          # Active local environment settings
├── README.md                     # Comprehensive setup and user guide
│
├── config/                       # Project configuration package
│   ├── __init__.py               # PyMySQL registration & MariaDB 10.4 patch
│   ├── settings.py               # Django settings, MySQL config, media/static
│   ├── urls.py                   # Master routing & media serving
│   ├── wsgi.py                   # WSGI server entry point
│   └── asgi.py                   # ASGI server entry point
│
├── automation/                   # Core application
│   ├── __init__.py
│   ├── admin.py                  # Django Admin customization
│   ├── apps.py                   # App config & media folder bootstrapping
│   ├── forms.py                  # Validation forms (Auth, Tasks)
│   ├── models.py                 # AutomationTask, AutomationConfiguration, AutomationActivity
│   ├── services.py               # Pure Python automation logic & SSRF guard
│   ├── urls.py                   # View routing endpoints
│   ├── views.py                  # 11 Page controllers & AJAX endpoints
│   ├── tests.py                  # 18 Automated unit tests
│   └── migrations/               # Database schema migrations
│
├── templates/                    # HTML5 templates
│   ├── base.html                 # Master layout (sidebar, topbar, toasts)
│   ├── dashboard.html            # Metrics, 3 task cards, recent history
│   ├── tasks.html                # Automation tasks catalog
│   ├── move_jpg.html             # JPG organizer UI
│   ├── extract_emails.html       # Email extractor dropzone & table
│   ├── scrape_title.html         # Web title scraper UI
│   ├── history.html              # Searchable, filterable, paginated history
│   ├── task_details.html         # In-depth task execution audit view
│   ├── about.html                # Project documentation & tech stack
│   ├── login.html                # User login page
│   ├── register.html             # User registration page
│   └── admin_dashboard.html      # System analytics & configuration oversight
│
├── static/
│   ├── css/
│   │   └── style.css             # Light theme, blue/purple accents, animations
│   └── js/
│       └── main.js               # Vanilla JS AJAX handler, toast notifications
│
└── media/
    ├── generated/                # Auto-generated .txt output files
    ├── uploads/                  # Temporary uploaded files
    └── workspace/                # Approved application workspace
        ├── sample_emails.txt     # Pre-loaded sample text file for instant testing
        ├── source_sample/        # Pre-loaded sample JPG images
        └── destination/          # Destination directory for organized images
```

---

## 🚀 4. Beginner-Friendly Step-by-Step Setup Guide (Windows & PyCharm)

Follow these exact steps to run the application on Windows using PyCharm and XAMPP.

### STEP 1: Install Python and PyCharm
1. Ensure Python 3.10+ (or Python 3.12/3.14) is installed from [python.org](https://www.python.org/). Check the box **"Add Python to PATH"** during installation.
2. Download and install **PyCharm** (Community or Professional Edition) from [jetbrains.com/pycharm](https://www.jetbrains.com/pycharm/).

---

### STEP 2: Install XAMPP and Start MySQL Service
1. Download **XAMPP for Windows** from [apachefriends.org](https://www.apachefriends.org/).
2. Open the **XAMPP Control Panel**.
3. Locate the **MySQL** module row and click the **"Start"** button.
4. Verify that the label turns green and indicates port **3306**.

---

### STEP 3: Open phpMyAdmin and Create Database `autotask_db`
1. In the XAMPP Control Panel, click the **"Admin"** button next to MySQL (or open your browser and navigate to `http://localhost/phpmyadmin/`).
2. Click on the **"New"** button in the left sidebar.
3. In the "Database name" input field, type:
   ```text
   autotask_db
   ```
4. Choose collation `utf8mb4_general_ci` or `utf8mb4_unicode_ci`.
5. Click **"Create"**.

---

### STEP 4: Open Project & Virtual Environment in PyCharm
1. Launch **PyCharm**.
2. Click **File -> Open...** and select this project directory:
   ```text
   E:\Users\Abhishek\PycharmProjects\PythonProject\codealpha
   ```
3. PyCharm will automatically detect the virtual environment in `.venv`.
4. Open the PyCharm built-in Terminal (**Alt + F12** or click `Terminal` at the bottom left). Ensure the prompt starts with `(.venv)`.

If the virtual environment is not already active, activate it:
```powershell
.venv\Scripts\activate
```

---

### STEP 5: Install Required Python Packages
Run the following command in the PyCharm terminal:
```powershell
pip install -r requirements.txt
```
This installs `django`, `pymysql`, `requests`, `beautifulsoup4`, and `python-dotenv`.

---

### STEP 6: Verify Environment Settings (`.env`)
A `.env` file has been provided in the project root:
```ini
SECRET_KEY=django-insecure-autotask-academic-project-key-replace-with-secure-key-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=autotask_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
APPROVED_WORKSPACE=
```
*(Default XAMPP installations have user `root` with no password `""`. If you configured a MySQL root password in XAMPP, update `DB_PASSWORD` accordingly).*

---

### STEP 7: Run Database Migrations
Create and execute migrations to generate all database tables in MySQL:
```powershell
python manage.py makemigrations automation
python manage.py migrate
```
You will see all migrations apply with `OK`.

---

### STEP 8: Seed Pre-Configured Users (Or Create a Superuser)
The database has already been seeded with two ready-to-use accounts:

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Administrator (Staff)** | `admin` | `admin123` | `admin@autotask.org` |
| **Standard User** | `student` | `student123` | `student@example.com` |

*(Optional)* If you wish to create your own new superuser manually:
```powershell
python manage.py createsuperuser
```
Follow the interactive prompts to choose your username, email, and password.

---

### STEP 9: Run the Automated Tests
Verify that all 18 automated test cases pass:
```powershell
python manage.py test
```
**Expected Output:**
```text
Creating test database for alias 'default'...
..................
----------------------------------------------------------------------
Ran 18 tests in ~1.5s

OK
Destroying test database for alias 'default'...
```

---

### STEP 10: Run the Django Development Server
Start the local web server:
```powershell
python manage.py runserver
```
**Terminal Output:**
```text
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### STEP 11: Open the Application in Your Browser
Open Chrome, Edge, or Firefox and go to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

1. Log in with:
   - **Username:** `student`
   - **Password:** `student123`
   *(or create a new account via the "Register" link).*
2. You will be redirected to the **AutoTask Dashboard**!

---

## 🧪 5. Testing the 3 Automation Tasks (Quick Demonstration)

### Demonstration 1: JPG File Organizer
1. In the sidebar, click **"Move JPG Files"**.
2. Notice the pre-filled fields:
   - **Source Folder:** `source_sample` *(contains pre-created sample JPGs)*
   - **Destination Folder:** `destination`
3. Click the **"Move Images"** button.
4. AutoTask executes the Python script in the background, shows the loading animation, and dynamically updates the page displaying:
   - Total number of images moved.
   - List of moved files with non-destructive destination names.
   - Direct link to the task execution log.

---

### Demonstration 2: Email Address Extractor
1. In the sidebar, click **"Extract Emails"**.
2. Click the upload dropzone and select the pre-loaded sample file:
   ```text
   media/workspace/sample_emails.txt
   ```
3. Click **"Extract Emails"**.
4. The system parses the document, deduplicates addresses, preserves original order, and displays:
   - An interactive results table listing all unique emails.
   - A **"📥 Download Output (.txt)"** button.
5. Click **"Download Output"** to download the clean text file!

---

### Demonstration 3: Webpage Title Scraper
1. In the sidebar, click **"Scrape Webpage Title"**.
2. Enter any public website URL:
   ```text
   https://example.com
   ```
   *(or `https://www.python.org`)*
3. Click **"Scrape Title"**.
4. The backend verifies the target is not a private IP / loopback address (SSRF guard), fetches the HTML, extracts the `<title>` tag, and presents:
   - The webpage title.
   - HTTP response code (`200 OK`).
   - A **"📥 Download Title (.txt)"** button.

---

### Demonstration 4: Admin Oversight
1. Log out and sign in with the administrator account:
   - **Username:** `admin`
   - **Password:** `admin123`
2. Click **"Admin Dashboard"** in the sidebar.
3. Review system-wide metrics across all users, active workspace configurations, and the real-time audit trail.
4. Click **"Django Admin ↗"** to access Django's native administrative panel (`/admin/`).

---

## 🔒 6. Key Security & Architecture Highlights

1. **SSRF Defense-in-Depth:**
   - Hostname resolution via DNS is validated before opening connections.
   - Blocks `127.0.0.0/8`, `::1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`, and `localhost`.
   - Validates redirects iteratively up to 3 hops.

2. **Filesystem Jail:**
   - Resolves canonical paths with `pathlib.Path.resolve()`.
   - Uses `os.path.commonpath()` to ensure operations remain within the approved workspace.
   - Blocks path traversal strings such as `../` and absolute system roots.

3. **Database Version Compatibility:**
   - Standard XAMPP Windows packages bundle MariaDB 10.4.
   - AutoTask includes a lightweight compatibility patch in `config/__init__.py` that disables unsupported `INSERT ... RETURNING` syntax without requiring manual database upgrades.

---

## 🎓 7. Academic Assessment Summary

| Requirement | Implementation Detail | Status |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JS (No React/Node/PHP) | ✅ Completed |
| **Backend** | Python Django with `services.py` separation | ✅ Completed |
| **Database** | MySQL Server via XAMPP with Django ORM | ✅ Completed |
| **JPG Organizer** | `os`, `shutil` with safe duplicate resolution | ✅ Completed |
| **Email Extractor** | `re`, file handling with order preservation | ✅ Completed |
| **Title Scraper** | `requests`, `bs4` with hardened SSRF filter | ✅ Completed |
| **Authentication** | Registration, Login, Logout, CSRF, Password Hashing | ✅ Completed |
| **History & Audit** | Search, Filter, Sort, Pagination, Download | ✅ Completed |
| **Admin Panel** | Custom Admin Dashboard + Django Admin | ✅ Completed |
| **Automated Tests** | 18 Unit Tests covering all modules | ✅ Completed |
| **Deliverables** | Source code, requirements.txt, .env.example, README | ✅ Completed |
