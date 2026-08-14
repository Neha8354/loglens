from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from database import (
    get_events,
    get_services,
    get_sources,
    get_summary,
    initialize_database,
    save_events,
    update_event_status,
)
from parser import parse_log_file
from rules import enrich_event

app = Flask(__name__)

PROJECT_DIR = Path(__file__).parent
SAMPLE_LOG_PATH = PROJECT_DIR / "sample_logs" / "system.log"
UPLOADS_DIR = PROJECT_DIR / "uploads"

ALLOWED_EXTENSIONS = {"log", "txt"}

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOADS_DIR.mkdir(exist_ok=True)
initialize_database()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def process_log_file(file_path, source_file):
    parsed_events = parse_log_file(file_path)
    enriched_events = [enrich_event(event) for event in parsed_events]

    return save_events(enriched_events, source_file)


def import_sample_logs():
    return process_log_file(
        SAMPLE_LOG_PATH,
        "sample_logs/system.log",
    )


# Imports the sample log on application startup.
import_sample_logs()


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File is too large. Maximum upload size is 5 MB."
    }), 413


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/summary")
def summary_api():
    return jsonify(get_summary())


@app.route("/api/events")
def events_api():
    search = request.args.get("search", "").strip()
    severity = request.args.get("severity", "").strip()
    service = request.args.get("service", "").strip()
    source = request.args.get("source", "").strip()

    return jsonify(
        get_events(
            search=search,
            severity=severity,
            service=service,
            source=source,
        )
    )


@app.route("/api/services")
def services_api():
    return jsonify(get_services())


@app.route("/api/sources")
def sources_api():
    return jsonify(get_sources())


@app.route("/api/import", methods=["POST"])
def import_api():
    inserted_count = import_sample_logs()

    return jsonify({
        "message": "Sample logs processed successfully.",
        "inserted_count": inserted_count,
        "source_file": "sample_logs/system.log",
    })


@app.route("/api/upload", methods=["POST"])
def upload_api():
    uploaded_file = request.files.get("log_file")

    if uploaded_file is None:
        return jsonify({"error": "No file was selected."}), 400

    if not uploaded_file.filename:
        return jsonify({"error": "Please select a log file."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({
            "error": "Only .log and .txt files are supported."
        }), 400

    safe_name = secure_filename(uploaded_file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_name = f"{timestamp}_{safe_name}"
    saved_path = UPLOADS_DIR / stored_name

    uploaded_file.save(saved_path)

    inserted_count = process_log_file(
        saved_path,
        f"uploads/{stored_name}",
    )

    return jsonify({
        "message": "Log file processed successfully.",
        "inserted_count": inserted_count,
        "source_file": stored_name,
    })


@app.route("/api/events/<int:event_id>/status", methods=["POST"])
def update_status_api(event_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if not status:
        return jsonify({"error": "Status is required."}), 400

    try:
        update_event_status(event_id, status)
    except ValueError:
        return jsonify({"error": "Invalid status."}), 400

    return jsonify({
        "message": "Event status updated.",
        "status": status,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)