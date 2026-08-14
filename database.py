import hashlib
from pathlib import Path
import sqlite3


PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
DATABASE_PATH = DATA_DIR / "loglens.db"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS log_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hostname TEXT NOT NULL,
                service TEXT NOT NULL,
                process_id TEXT,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                raw_line TEXT NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                source_file TEXT NOT NULL DEFAULT 'sample_logs/system.log'
            )
            """
        )

        columns = connection.execute(
            "PRAGMA table_info(log_events)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        if "source_file" not in column_names:
            connection.execute(
                """
                ALTER TABLE log_events
                ADD COLUMN source_file TEXT
                NOT NULL DEFAULT 'sample_logs/system.log'
                """
            )


def save_events(events, source_file):
    inserted_count = 0

    with get_connection() as connection:
        for event in events:
            fingerprint = hashlib.sha256(
                event["raw_line"].encode("utf-8")
            ).hexdigest()

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO log_events (
                    timestamp,
                    hostname,
                    service,
                    process_id,
                    message,
                    severity,
                    category,
                    raw_line,
                    fingerprint,
                    source_file
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["timestamp"],
                    event["hostname"],
                    event["service"],
                    event["process_id"],
                    event["message"],
                    event["severity"],
                    event["category"],
                    event["raw_line"],
                    fingerprint,
                    source_file,
                ),
            )

            if cursor.rowcount == 1:
                inserted_count += 1

    return inserted_count


def get_summary():
    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM log_events"
        ).fetchone()[0]

        critical = connection.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE severity IN ('CRITICAL', 'ERROR')
            """
        ).fetchone()[0]

        warnings = connection.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE severity = 'WARNING'
            """
        ).fetchone()[0]

        failed_logins = connection.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE category = 'AUTHENTICATION'
            """
        ).fetchone()[0]

    return {
        "total": total,
        "critical": critical,
        "warnings": warnings,
        "failed_logins": failed_logins,
    }


def get_events(search="", severity="", service="", source=""):
    query = """
        SELECT *
        FROM log_events
        WHERE 1 = 1
    """
    parameters = []

    if search:
        query += """
            AND (
                message LIKE ?
                OR service LIKE ?
                OR hostname LIKE ?
            )
        """
        search_value = f"%{search}%"
        parameters.extend([
            search_value,
            search_value,
            search_value,
        ])

    if severity:
        query += " AND severity = ?"
        parameters.append(severity)

    if service:
        query += " AND service = ?"
        parameters.append(service)

    if source:
        query += " AND source_file = ?"
        parameters.append(source)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def get_services():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT service
            FROM log_events
            ORDER BY service
            """
        ).fetchall()

    return [row["service"] for row in rows]


def get_sources():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT source_file
            FROM log_events
            ORDER BY source_file
            """
        ).fetchall()

    return [row["source_file"] for row in rows]


def update_event_status(event_id, status):
    allowed_statuses = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}

    if status not in allowed_statuses:
        raise ValueError("Invalid event status")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE log_events
            SET status = ?
            WHERE id = ?
            """,
            (status, event_id),
        )