import re
from pathlib import Path


SYSLOG_PATTERN = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<service>[^\[:]+)"
    r"(?:\[(?P<process_id>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)


def parse_line(line):
    line = line.strip()

    if not line:
        return None

    match = SYSLOG_PATTERN.match(line)

    if not match:
        return {
            "timestamp": "Unknown",
            "hostname": "Unknown",
            "service": "Unknown",
            "process_id": None,
            "message": line,
            "raw_line": line,
        }

    return {
        "timestamp": match.group("timestamp"),
        "hostname": match.group("hostname"),
        "service": match.group("service"),
        "process_id": match.group("process_id"),
        "message": match.group("message"),
        "raw_line": line,
    }


def parse_log_file(file_path):
    path = Path(file_path)
    events = []

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as log_file:
        for line in log_file:
            event = parse_line(line)

            if event:
                events.append(event)

    return events