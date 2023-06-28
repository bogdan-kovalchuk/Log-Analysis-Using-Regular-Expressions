#!/usr/bin/env python3

import csv
import os
import tempfile
import unittest

from cli import build_parser, main


class TestBuildParser(unittest.TestCase):
    def test_default_logfile(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.logfile, "syslog.log")

    def test_custom_logfile(self):
        parser = build_parser()
        args = parser.parse_args(["custom.log"])
        self.assertEqual(args.logfile, "custom.log")

    def test_default_csv_paths(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.error_csv, "error_message.csv")
        self.assertEqual(args.user_csv, "user_statistics.csv")


class TestMain(unittest.TestCase):
    def test_end_to_end(self):
        log_content = (
            "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#4217] (mdouglas)\n"
            "Jan 31 00:21:30 ubuntu.local ticky: ERROR Timeout while retrieving information (breee)\n"
            "Jan 31 00:44:34 ubuntu.local ticky: ERROR Timeout while retrieving information (ac)\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            error_path = os.path.join(tmpdir, "errors.csv")
            user_path = os.path.join(tmpdir, "users.csv")

            with open(log_path, "w") as f:
                f.write(log_content)

            main([log_path, "--error-csv", error_path, "--user-csv", user_path])

            with open(error_path, "r") as f:
                error_rows = list(csv.reader(f))
            self.assertEqual(error_rows[0], ["Error", "Count"])
            self.assertEqual(error_rows[1], ["Timeout while retrieving information", "2"])

            with open(user_path, "r") as f:
                user_rows = list(csv.reader(f))
            self.assertEqual(user_rows[0], ["Username", "INFO", "ERROR"])
            self.assertEqual(user_rows[1], ["ac", "0", "1"])
            self.assertEqual(user_rows[2], ["breee", "0", "1"])
            self.assertEqual(user_rows[3], ["mdouglas", "1", "0"])

    def test_missing_logfile_exits_with_error(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["/nonexistent/path/to/log.log"])
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
