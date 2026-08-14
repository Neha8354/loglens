# LogLens

LogLens is a syslog-style log analysis and incident dashboard.

## Features

- Parses syslog-style `.log` and `.txt` files
- Supports sample log processing and user file upload
- Extracts timestamps, hostnames, services, process IDs, and messages
- Classifies Critical, Error, Warning, and Info events
- Detects failed login attempts
- Stores parsed events in SQLite
- Filters events by search term, severity, service, and source file
- Supports Open, Acknowledged, and Resolved event states

## Supported File Format

LogLens accepts `.log` and `.txt` files containing syslog-style entries.

Example:

```text
Aug 14 09:10:03 server01 sshd[421]: Failed password for admin from 192.168.1.20
Aug 14 09:12:45 server01 nginx[610]: ERROR connection timeout