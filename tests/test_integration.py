#!/usr/bin/env python3

import csv
import os
import tempfile
import unittest

from aggregation import count_errors, count_per_user
from cli import main
from log_parser import parse_file


class TestSyslogSample(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.syslog_path = os.path.join(self.repo_root, "syslog.log")

    def test_syslog_parses_without_errors(self):
        entries = parse_file(self.syslog_path)
        self.assertGreater(len(entries), 0)
        types = {e.message_type for e in entries}
        self.assertLessEqual(types, {"INFO", "ERROR"})

    def test_syslog_expected_total_entries(self):
        entries = parse_file(self.syslog_path)
        self.assertEqual(len(entries), 100)

    def test_syslog_error_count(self):
        entries = parse_file(self.syslog_path)
        errors = [e for e in entries if e.message_type == "ERROR"]
        self.assertEqual(len(errors), 66)

    def test_syslog_top_error_is_timeout(self):
        entries = parse_file(self.syslog_path)
        error_data = count_errors(entries)
        self.assertEqual(error_data[0][0], "Timeout while retrieving information")
        self.assertEqual(error_data[0][1], 15)

    def test_syslog_cli_produces_expected_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            error_path = os.path.join(tmpdir, "errors.csv")
            user_path = os.path.join(tmpdir, "users.csv")
            main([self.syslog_path, "--error-csv", error_path, "--user-csv", user_path])

            with open(error_path, "r", encoding="utf-8") as f:
                error_rows = list(csv.reader(f))
            self.assertEqual(error_rows[0], ["Error", "Count"])
            self.assertEqual(error_rows[1], ["Timeout while retrieving information", "15"])

            with open(user_path, "r", encoding="utf-8") as f:
                user_rows = list(csv.reader(f))
            self.assertEqual(user_rows[0], ["Username", "INFO", "ERROR"])
            usernames = [r[0] for r in user_rows[1:]]
            self.assertEqual(usernames, sorted(usernames))
            self.assertIn("oren", usernames)
            self.assertIn("noel", usernames)


if __name__ == "__main__":
    unittest.main()
