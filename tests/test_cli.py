#!/usr/bin/env python3

import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

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

    def test_default_encoding(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.encoding, "utf-8")

    def test_custom_encoding(self):
        parser = build_parser()
        args = parser.parse_args(["--encoding", "latin-1"])
        self.assertEqual(args.encoding, "latin-1")


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

    def test_directory_logfile_reports_the_actual_problem(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stderr = io.StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
                main([tmpdir])
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("is a directory", stderr.getvalue())

    def test_invalid_output_path_exits_with_error(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            with open(log_path, "w") as f:
                f.write(log_content)
            bad_output = os.path.join(tmpdir, "nonexistent_dir", "out.csv")
            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--error-csv", bad_output])
            self.assertEqual(ctx.exception.code, 1)


class TestOutputPathCollisionPreservation(unittest.TestCase):
    def _write_log(self, tmpdir, content):
        log_path = os.path.join(tmpdir, "test.log")
        with open(log_path, "w") as f:
            f.write(content)
        return log_path

    def test_error_csv_same_as_logfile_is_rejected_and_log_preserved(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = self._write_log(tmpdir, log_content)
            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--error-csv", log_path])
            self.assertEqual(ctx.exception.code, 1)
            with open(log_path, "r") as f:
                self.assertEqual(f.read(), log_content)

    def test_user_csv_same_as_logfile_is_rejected_and_log_preserved(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = self._write_log(tmpdir, log_content)
            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--user-csv", log_path])
            self.assertEqual(ctx.exception.code, 1)
            with open(log_path, "r") as f:
                self.assertEqual(f.read(), log_content)

    def test_error_csv_via_relative_traversal_equal_to_logfile_is_rejected(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub")
            os.mkdir(subdir)
            log_path = self._write_log(tmpdir, log_content)
            aliased_path = os.path.join(subdir, "..", "test.log")
            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--error-csv", aliased_path])
            self.assertEqual(ctx.exception.code, 1)
            with open(log_path, "r") as f:
                self.assertEqual(f.read(), log_content)

    def test_error_csv_same_as_user_csv_is_rejected_and_existing_output_preserved(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        existing_content = "sentinel,do-not-touch\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = self._write_log(tmpdir, log_content)
            shared_path = os.path.join(tmpdir, "shared.csv")
            with open(shared_path, "w") as f:
                f.write(existing_content)

            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--error-csv", shared_path, "--user-csv", shared_path])
            self.assertEqual(ctx.exception.code, 1)

            with open(shared_path, "r") as f:
                self.assertEqual(f.read(), existing_content)

    @unittest.skipUnless(os.name == "nt", "Windows paths are case-insensitive")
    def test_output_paths_differing_only_by_case_are_rejected(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = self._write_log(tmpdir, log_content)
            error_path = os.path.join(tmpdir, "Reports.csv")
            user_path = os.path.join(tmpdir, "reports.csv")

            with self.assertRaises(SystemExit) as ctx:
                main([log_path, "--error-csv", error_path, "--user-csv", user_path])
            self.assertEqual(ctx.exception.code, 1)
            self.assertFalse(os.path.exists(error_path))
            self.assertFalse(os.path.exists(user_path))

    def test_valid_distinct_paths_still_succeed(self):
        log_content = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = self._write_log(tmpdir, log_content)
            error_path = os.path.join(tmpdir, "errors.csv")
            user_path = os.path.join(tmpdir, "users.csv")
            main([log_path, "--error-csv", error_path, "--user-csv", user_path])
            self.assertTrue(os.path.exists(error_path))
            self.assertTrue(os.path.exists(user_path))


if __name__ == "__main__":
    unittest.main()
