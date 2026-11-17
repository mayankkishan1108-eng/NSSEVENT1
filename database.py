"""SQLite persistence for the NSS Event & Camp Management Portal.

All database creation, seed data, and queries are handled from Python using
the standard-library sqlite3 module. The database file is created on first run.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTANCE_DIR = ROOT / "instance"
DATABASE_PATH = INSTANCE_DIR / "nss_portal.sqlite3"


class ClosingConnection(sqlite3.Connection):
    """Commit or roll back on context exit, then always release the file handle."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    """Open a connection with dictionary-like rows and foreign keys enabled."""
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize() -> None:
    """Create the schema and add realistic demo records once."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                enrollment_no TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                year TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                joined_on TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                venue TEXT NOT NULL,
                coordinator TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 50 CHECK (capacity > 0),
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Planned'
                    CHECK (status IN ('Planned', 'Open', 'Completed', 'Cancelled')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS camps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                location TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                coordinator TEXT NOT NULL,
                volunteers_needed INTEGER NOT NULL DEFAULT 20 CHECK (volunteers_needed > 0),
                status TEXT NOT NULL DEFAULT 'Planning'
                    CHECK (status IN ('Planning', 'Recruiting', 'In progress', 'Completed')),
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
                registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                attended INTEGER NOT NULL DEFAULT 0 CHECK (attended IN (0, 1)),
                UNIQUE (event_id, volunteer_id)
            );

            CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
            CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
            """
        )

        if connection.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0] > 0:
            return

        today = date.today()
        volunteers = [
            ("Aarav Mehta", "NSS2024-017", "Computer Science", "Second year", "98765 41021", "aarav.mehta@campus.edu", today.isoformat()),
            ("Diya Nair", "NSS2023-042", "Psychology", "Third year", "98765 41022", "diya.nair@campus.edu", today.isoformat()),
            ("Rohan Iyer", "NSS2024-031", "Commerce", "Second year", "98765 41023", "rohan.iyer@campus.edu", today.isoformat()),
            ("Mira Kapoor", "NSS2022-008", "Environmental Science", "Final year", "98765 41024", "mira.kapoor@campus.edu", today.isoformat()),
            ("Kabir Das", "NSS2023-055", "Sociology", "Third year", "98765 41025", "kabir.das@campus.edu", today.isoformat()),
            ("Ananya Rao", "NSS2024-063", "Biotechnology", "Second year", "98765 41026", "ananya.rao@campus.edu", today.isoformat()),
        ]
        connection.executemany(
            """INSERT INTO volunteers
               (name, enrollment_no, department, year, phone, email, joined_on)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            volunteers,
        )

        events = [
            ("Neighbourhood Clean-up Drive", "Community service", (today + timedelta(days=3)).isoformat(), "07:30", "Lakeview Park Gate 2", "Diya Nair", 40, "A morning clean-up with local residents. Gloves, bags and drinking water will be provided.", "Open"),
            ("Health & Wellness Check-up", "Health", (today + timedelta(days=8)).isoformat(), "09:00", "Campus Health Centre", "Mira Kapoor", 30, "Support the campus health team with registration, queue guidance and visitor assistance.", "Open"),
            ("Digital Literacy Workshop", "Education", (today + timedelta(days=14)).isoformat(), "10:00", "Community Learning Centre", "Aarav Mehta", 24, "Help school students build confidence with email, online safety and basic documents.", "Planned"),
            ("Blood Donation Camp", "Health", (today - timedelta(days=12)).isoformat(), "08:30", "Main Auditorium", "Rohan Iyer", 60, "A campus blood donation day in partnership with City General Hospital.", "Completed"),
        ]
        connection.executemany(
            """INSERT INTO events
               (title, category, event_date, event_time, venue, coordinator, capacity, description, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            events,
        )

        camps = [
            ("Village Immersion Camp", "Keshavpur, North District", (today + timedelta(days=21)).isoformat(), (today + timedelta(days=25)).isoformat(), "Mira Kapoor", 28, "Recruiting", "Five days of community surveys, school activities and local outreach. Accommodation and meals are arranged."),
            ("Monsoon Preparedness Camp", "Riverside Ward 6", (today + timedelta(days=6)).isoformat(), (today + timedelta(days=7)).isoformat(), "Kabir Das", 18, "Planning", "Work with ward teams on awareness material and household preparedness kits."),
            ("Annual Service Camp", "Campus & nearby communities", (today - timedelta(days=42)).isoformat(), (today - timedelta(days=38)).isoformat(), "Diya Nair", 32, "Completed", "The annual week-long programme is complete. Final report and attendance records are archived."),
        ]
        connection.executemany(
            """INSERT INTO camps
               (title, location, start_date, end_date, coordinator, volunteers_needed, status, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            camps,
        )

        # A few registrations make the dashboard useful on the first visit.
        connection.executemany(
            "INSERT INTO registrations (event_id, volunteer_id, attended) VALUES (?, ?, ?)",
            [(1, 1, 0), (1, 2, 0), (1, 3, 0), (1, 5, 0), (2, 2, 0), (2, 4, 0), (4, 1, 1), (4, 2, 1), (4, 3, 1), (4, 4, 1), (4, 5, 1)],
        )

