"""NSS Event & Camp Management Portal — Flask application."""

from __future__ import annotations

import csv
import io
import os
from datetime import date, datetime

from flask import Flask, Response, flash, redirect, render_template, request, url_for

from database import connect, initialize

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("NSS_PORTAL_SECRET", "local-demo-key-change-before-deployment")
initialize()


@app.template_filter("pretty_date")
def pretty_date(value: str, pattern: str = "%d %b %Y") -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime(pattern)
    except (TypeError, ValueError):
        return value or "—"


def rows(query: str, values: tuple = ()):
    with connect() as db:
        return db.execute(query, values).fetchall()


def row(query: str, values: tuple = ()):
    with connect() as db:
        return db.execute(query, values).fetchone()


def clean(name: str, label: str, maximum: int = 240) -> str:
    value = request.form.get(name, "").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    if len(value) > maximum:
        raise ValueError(f"{label} must be {maximum} characters or fewer.")
    return value


def positive_int(name: str, label: str) -> int:
    try:
        value = int(request.form.get(name, ""))
    except ValueError as exc:
        raise ValueError(f"Enter a valid number for {label.lower()}.") from exc
    if value < 1:
        raise ValueError(f"{label} must be at least 1.")
    return value


@app.context_processor
def inject_today():
    return {"today_iso": date.today().isoformat()}


@app.get("/")
def dashboard():
    stats = {
        "volunteers": row("SELECT COUNT(*) AS n FROM volunteers")["n"],
        "upcoming": row("SELECT COUNT(*) AS n FROM events WHERE event_date >= ? AND status IN ('Open', 'Planned')", (date.today().isoformat(),))["n"],
        "camps": row("SELECT COUNT(*) AS n FROM camps WHERE status IN ('Recruiting', 'In progress')")["n"],
        "hours": row("SELECT COUNT(*) * 3 AS n FROM registrations WHERE attended = 1")["n"],
    }
    upcoming = rows(
        """SELECT e.*, COUNT(r.id) AS registered FROM events e
           LEFT JOIN registrations r ON r.event_id = e.id
           WHERE e.event_date >= ? AND e.status IN ('Open', 'Planned')
           GROUP BY e.id ORDER BY e.event_date LIMIT 4""",
        (date.today().isoformat(),),
    )
    categories = rows(
        """SELECT category, COUNT(*) AS total FROM events
           WHERE event_date >= ? GROUP BY category ORDER BY total DESC LIMIT 4""",
        (date.today().isoformat(),),
    )
    return render_template("dashboard.html", stats=stats, upcoming=upcoming, categories=categories)


@app.route("/events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        try:
            title = clean("title", "Event name")
            category = clean("category", "Category", 80)
            event_date = clean("event_date", "Date", 10)
            event_time = clean("event_time", "Time", 5)
            venue = clean("venue", "Venue")
            coordinator = clean("coordinator", "Coordinator", 120)
            capacity = positive_int("capacity", "Capacity")
            description = request.form.get("description", "").strip()[:2000]
            if event_date < date.today().isoformat():
                raise ValueError("Choose today or a future date for a new event.")
            with connect() as db:
                db.execute(
                    """INSERT INTO events
                       (title, category, event_date, event_time, venue, coordinator, capacity, description, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open')""",
                    (title, category, event_date, event_time, venue, coordinator, capacity, description),
                )
            flash("Event added to the calendar.", "success")
            return redirect(url_for("events"))
        except ValueError as exc:
            flash(str(exc), "error")

    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    sql = """SELECT e.*, COUNT(r.id) AS registered FROM events e
             LEFT JOIN registrations r ON r.event_id = e.id WHERE 1=1"""
    params: list[str] = []
    if search:
        sql += " AND (e.title LIKE ? OR e.venue LIKE ? OR e.category LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    if status_filter in {"Open", "Planned", "Completed", "Cancelled"}:
        sql += " AND e.status = ?"
        params.append(status_filter)
    sql += " GROUP BY e.id ORDER BY e.event_date DESC"
    items = rows(sql, tuple(params))
    coordinators = rows("SELECT name FROM volunteers ORDER BY name")
    return render_template("events.html", events=items, search=search, status_filter=status_filter, coordinators=coordinators)


@app.route("/events/<int:event_id>", methods=["GET", "POST"])
def event_detail(event_id: int):
    event = row("SELECT * FROM events WHERE id = ?", (event_id,))
    if event is None:
        flash("That event could not be found.", "error")
        return redirect(url_for("events"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "register":
            try:
                volunteer_id = int(request.form.get("volunteer_id", ""))
                volunteer = row("SELECT id FROM volunteers WHERE id = ?", (volunteer_id,))
                if volunteer is None:
                    raise ValueError("Choose a volunteer from the list.")
                count = row("SELECT COUNT(*) AS n FROM registrations WHERE event_id = ?", (event_id,))["n"]
                if count >= event["capacity"]:
                    raise ValueError("This event has reached its volunteer capacity.")
                with connect() as db:
                    db.execute("INSERT INTO registrations (event_id, volunteer_id) VALUES (?, ?)", (event_id, volunteer_id))
                flash("Volunteer registered.", "success")
            except ValueError as exc:
                message = "That volunteer is already registered." if "UNIQUE" in str(exc) else str(exc)
                flash(message, "error")
            except Exception as exc:
                if "UNIQUE" in str(exc):
                    flash("That volunteer is already registered.", "error")
                else:
                    raise
            return redirect(url_for("event_detail", event_id=event_id))
        if action == "attendance":
            selected = {int(value) for value in request.form.getlist("attended_ids") if value.isdigit()}
            registrations = rows("SELECT id FROM registrations WHERE event_id = ?", (event_id,))
            with connect() as db:
                db.executemany(
                    "UPDATE registrations SET attended = ? WHERE id = ? AND event_id = ?",
                    [(1 if item["id"] in selected else 0, item["id"], event_id) for item in registrations],
                )
            flash("Attendance has been saved.", "success")
            return redirect(url_for("event_detail", event_id=event_id))

    registrations = rows(
        """SELECT r.id AS registration_id, r.attended, v.* FROM registrations r
           JOIN volunteers v ON v.id = r.volunteer_id WHERE r.event_id = ? ORDER BY v.name""",
        (event_id,),
    )
    registered_ids = {item["id"] for item in registrations}
    available_volunteers = [v for v in rows("SELECT * FROM volunteers ORDER BY name") if v["id"] not in registered_ids]
    return render_template("event_detail.html", event=event, registrations=registrations, available_volunteers=available_volunteers)


@app.post("/events/<int:event_id>/delete")
def delete_event(event_id: int):
    with connect() as db:
        db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    flash("Event and its registrations removed.", "success")
    return redirect(url_for("events"))


@app.post("/events/<int:event_id>/status")
def update_event_status(event_id: int):
    status = request.form.get("status", "")
    if status not in {"Open", "Planned", "Completed", "Cancelled"}:
        flash("Choose a valid event status.", "error")
    else:
        with connect() as db:
            db.execute("UPDATE events SET status = ? WHERE id = ?", (status, event_id))
        flash("Event status updated.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/camps", methods=["GET", "POST"])
def camps():
    if request.method == "POST":
        try:
            title = clean("title", "Camp name")
            location = clean("location", "Location")
            start_date = clean("start_date", "Start date", 10)
            end_date = clean("end_date", "End date", 10)
            coordinator = clean("coordinator", "Coordinator", 120)
            volunteers_needed = positive_int("volunteers_needed", "Volunteer requirement")
            description = request.form.get("description", "").strip()[:2000]
            if end_date < start_date:
                raise ValueError("The end date must be on or after the start date.")
            with connect() as db:
                db.execute(
                    """INSERT INTO camps
                       (title, location, start_date, end_date, coordinator, volunteers_needed, status, description)
                       VALUES (?, ?, ?, ?, ?, ?, 'Planning', ?)""",
                    (title, location, start_date, end_date, coordinator, volunteers_needed, description),
                )
            flash("Camp added to the programme.", "success")
            return redirect(url_for("camps"))
        except ValueError as exc:
            flash(str(exc), "error")
    items = rows("SELECT * FROM camps ORDER BY start_date DESC")
    coordinators = rows("SELECT name FROM volunteers ORDER BY name")
    return render_template("camps.html", camps=items, coordinators=coordinators)


@app.post("/camps/<int:camp_id>/status")
def update_camp_status(camp_id: int):
    status = request.form.get("status", "")
    if status not in {"Planning", "Recruiting", "In progress", "Completed"}:
        flash("Choose a valid camp status.", "error")
    else:
        with connect() as db:
            db.execute("UPDATE camps SET status = ? WHERE id = ?", (status, camp_id))
        flash("Camp status updated.", "success")
    return redirect(url_for("camps"))


@app.post("/camps/<int:camp_id>/delete")
def delete_camp(camp_id: int):
    with connect() as db:
        db.execute("DELETE FROM camps WHERE id = ?", (camp_id,))
    flash("Camp removed.", "success")
    return redirect(url_for("camps"))


@app.route("/volunteers", methods=["GET", "POST"])
def volunteers():
    if request.method == "POST":
        try:
            name = clean("name", "Full name", 120)
            enrollment_no = clean("enrollment_no", "Enrollment number", 40)
            department = clean("department", "Department", 100)
            year = clean("year", "Year", 40)
            phone = clean("phone", "Phone number", 30)
            email = clean("email", "Email address", 160)
            with connect() as db:
                db.execute(
                    """INSERT INTO volunteers
                       (name, enrollment_no, department, year, phone, email, joined_on)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (name, enrollment_no, department, year, phone, email, date.today().isoformat()),
                )
            flash("Volunteer profile created.", "success")
            return redirect(url_for("volunteers"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception as exc:
            if "UNIQUE" in str(exc):
                flash("That enrollment number is already in the directory.", "error")
            else:
                raise
    search = request.args.get("q", "").strip()
    if search:
        pattern = f"%{search}%"
        items = rows(
            """SELECT v.*, COUNT(r.id) AS event_count FROM volunteers v
               LEFT JOIN registrations r ON r.volunteer_id = v.id
               WHERE v.name LIKE ? OR v.enrollment_no LIKE ? OR v.department LIKE ?
               GROUP BY v.id ORDER BY v.name""",
            (pattern, pattern, pattern),
        )
    else:
        items = rows(
            """SELECT v.*, COUNT(r.id) AS event_count FROM volunteers v
               LEFT JOIN registrations r ON r.volunteer_id = v.id GROUP BY v.id ORDER BY v.name"""
        )
    return render_template("volunteers.html", volunteers=items, search=search)


@app.post("/volunteers/<int:volunteer_id>/delete")
def delete_volunteer(volunteer_id: int):
    with connect() as db:
        db.execute("DELETE FROM volunteers WHERE id = ?", (volunteer_id,))
    flash("Volunteer profile removed from the directory.", "success")
    return redirect(url_for("volunteers"))


@app.get("/reports")
def reports():
    summary = rows(
        """SELECT e.id, e.title, e.category, e.event_date, e.status,
                  COUNT(r.id) AS registered,
                  COALESCE(SUM(r.attended), 0) AS attended
           FROM events e LEFT JOIN registrations r ON r.event_id = e.id
           GROUP BY e.id ORDER BY e.event_date DESC"""
    )
    total_registrations = sum(item["registered"] for item in summary)
    total_attended = sum(item["attended"] for item in summary)
    return render_template(
        "reports.html",
        events=summary,
        total_registrations=total_registrations,
        total_attended=total_attended,
        attendance_rate=round(total_attended / total_registrations * 100) if total_registrations else 0,
    )


@app.get("/reports/export.csv")
def export_report():
    items = rows(
        """SELECT e.title, e.category, e.event_date, e.venue, e.status,
                  v.name, v.enrollment_no, r.attended
           FROM events e LEFT JOIN registrations r ON r.event_id = e.id
           LEFT JOIN volunteers v ON v.id = r.volunteer_id
           ORDER BY e.event_date DESC, v.name"""
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Event", "Category", "Date", "Venue", "Status", "Volunteer", "Enrollment number", "Attended"])
    for item in items:
        writer.writerow([item["title"], item["category"], item["event_date"], item["venue"], item["status"], item["name"] or "", item["enrollment_no"] or "", "Yes" if item["attended"] else "No" if item["name"] else ""])
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=nss-participation-report.csv"},
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=os.environ.get("NSS_DEBUG") == "1")

