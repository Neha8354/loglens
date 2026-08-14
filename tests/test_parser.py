import unittest

from parser import parse_line
from rules import classify_event


class ParserTests(unittest.TestCase):
    def test_parses_syslog_line(self):
        line = (
            "Aug 14 09:10:03 server01 sshd[421]: "
            "Failed password for admin"
        )

        event = parse_line(line)

        self.assertEqual(event["hostname"], "server01")
        self.assertEqual(event["service"], "sshd")
        self.assertEqual(event["process_id"], "421")

    def test_classifies_failed_login(self):
        event = {
            "message": "Failed password for admin"
        }

        severity, category = classify_event(event)

        self.assertEqual(severity, "WARNING")
        self.assertEqual(category, "AUTHENTICATION")

    def test_classifies_disk_full(self):
        event = {
            "message": "Disk full on /var"
        }

        severity, category = classify_event(event)

        self.assertEqual(severity, "CRITICAL")
        self.assertEqual(category, "SYSTEM")


if __name__ == "__main__":
    unittest.main()