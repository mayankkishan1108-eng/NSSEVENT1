# NSS Event & Camp Management Portal

A working campus level model for planning National Service Scheme activities, coordinating camps and keeping volunteer participation records.

## Technology

- **Python 3.10+** runs the application and all database setup and queries.
- **SQLite**, accessed with Python's built in `sqlite3` module, stores the records locally. There is no separate database server, SQL setup file, ORM, or database language dependency.
- **Flask** handles the website routes. **Gunicorn** is included for Linux web hosting and skipped on Windows.
- HTML, CSS and a small amount of JavaScript provide the website interface. No front end framework, CDN, external font, or paid service is required.

The database is created automatically at `instance/nss_portal.sqlite3` the first time the app starts. The first run seeds sample events, camps, volunteers and attendance so the screens are useful immediately. The `instance` directory is ignored by Git so every installation gets its own database. Delete that file to reset the demo data.

## Start the portal

Open a terminal in this folder and run:

```text
python start_portal.py
```

On first use, the launcher installs Flask into the ignored `.local_packages` folder if it is missing, starts the server, and opens the portal in your default browser. Keep the terminal window open while using the site; press `Ctrl+C` there to stop it. The address `http://127.0.0.1:5000` is local to the computer running this command, so it is reachable only while the server is running on that same computer.

You can also manage dependencies yourself with `python -m pip install -r requirements.txt` and then start the site with `python app.py`.

## Publish the working Python app

GitHub Pages only hosts static files and cannot run this Flask application. Keep this repository as the source code, then deploy it to a Python web host such as Render.

For a Render Web Service, use:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

The repository root must contain `app.py`, `database.py`, `requirements.txt`, and the `templates/` and `static/` folders. On Render's free service, the local SQLite database is temporary and can reset when the service sleeps or restarts. Use this setup for a demo; do not rely on it for permanent volunteer records.

## How to use it

1. **Overview** summarizes the volunteer directory, upcoming activities, active camps and estimated service hours. Select an activity to open its working roster.
2. **Events** lets the unit create and search activities, review capacity and status, and open an event brief. On the brief, register a volunteer, mark attendance and update the event status.
3. **Camps** stores dates, location, coordinator, volunteer goal and programme brief. Camp status can be updated as planning moves into recruitment, delivery and completion.
4. **Volunteers** keeps student contact records, supports directory search and shows how many event registrations each student has.
5. **Reports** summarizes event registrations and recorded attendance. Download CSV creates a spreadsheet friendly participation report.

The forms provide basic required field and date checks. Destructive actions ask for confirmation in the browser.

## Project files

```text
app.py                  Flask routes and page logic
database.py             SQLite schema, sample data and Python database setup
requirements.txt        Flask and production web-server dependencies
templates/              Website pages
static/css/site.css     Responsive visual design
static/js/site.js       Small interface interactions
instance/               Generated local database (created on first run, not committed)
```

## Before putting it on a public server

This is a local working model for evaluation and development. It does not include user accounts or role based access, so keep it on a trusted machine or add authentication before making it publicly accessible. Set a private `NSS_PORTAL_SECRET` environment variable for Flask sessions. For a Windows PowerShell session:

```powershell
$env:NSS_PORTAL_SECRET = "replace-with-a-long-random-value"
python app.py
```

The built in Flask server is for local development; use a production WSGI server and HTTPS for a real deployment.
