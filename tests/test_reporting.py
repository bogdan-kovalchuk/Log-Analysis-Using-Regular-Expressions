#!/usr/bin/env python3

import csv
import os
import tempfile
import unittest

from reporting import _sanitize, write_error_csv, write_user_csv


class TestWriteErrorCsv(unittest.TestCase):
    def test_writes_header_and_rows(self):
        data = [("Timeout", 5), ("Permission denied", 3)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_error_csv(data, tmp_path)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[0], ["Error", "Count"])
            self.assertEqual(reader[1], ["Timeout", "5"])
            self.assertEqual(reader[2], ["Permission denied", "3"])
        finally:
            os.unlink(tmp_path)

    def test_empty_data(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_error_csv([], tmp_path)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0], ["Error", "Count"])
        finally:
            os.unlink(tmp_path)

    def test_formula_injection_is_sanitized(self):
        data = [("=SUM(A1:A10)", 5), ("+cmd", 3), ("-drop", 2), ("@evil", 1)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_error_csv(data, tmp_path)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[1][0], "'=SUM(A1:A10)")
            self.assertEqual(reader[2][0], "'+cmd")
            self.assertEqual(reader[3][0], "'-drop")
            self.assertEqual(reader[4][0], "'@evil")
        finally:
            os.unlink(tmp_path)


class TestWriteUserCsv(unittest.TestCase):
    def test_writes_header_and_rows(self):
        data = [("alice", 2, 1), ("bob", 0, 3)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_user_csv(data, tmp_path)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[0], ["Username", "INFO", "ERROR"])
            self.assertEqual(reader[1], ["alice", "2", "1"])
            self.assertEqual(reader[2], ["bob", "0", "3"])
        finally:
            os.unlink(tmp_path)

    def test_max_users_limits_output(self):
        data = [("alice", 1, 0), ("bob", 2, 1), ("charlie", 0, 3)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_user_csv(data, tmp_path, max_users=2)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(len(reader), 3)
            self.assertEqual(reader[1], ["alice", "1", "0"])
            self.assertEqual(reader[2], ["bob", "2", "1"])
        finally:
            os.unlink(tmp_path)

    def test_user_formula_injection_is_sanitized(self):
        data = [("=alice", 1, 0), ("+bob", 2, 1)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmp_path = f.name
        try:
            write_user_csv(data, tmp_path)
            with open(tmp_path, "r") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[1][0], "'=alice")
            self.assertEqual(reader[2][0], "'+bob")
        finally:
            os.unlink(tmp_path)

    def test_atomic_write_no_temp_left_on_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "errors.csv")
            write_error_csv([("Timeout", 3)], out_path)
            leftovers = [f for f in os.listdir(tmpdir) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])
            self.assertTrue(os.path.exists(out_path))

    def test_utf8_output_with_special_characters(self):
        data = [("Timeout café", 5)]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "errors.csv")
            write_error_csv(data, out_path)
            with open(out_path, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[1][0], "Timeout café")


class TestSanitizeHardening(unittest.TestCase):
    def test_plain_leading_whitespace_before_formula_is_neutralized(self):
        self.assertEqual(_sanitize(" =SUM(A1:A10)"), "' =SUM(A1:A10)")
        self.assertEqual(_sanitize("  +cmd"), "'  +cmd")
        self.assertEqual(_sanitize("   -drop"), "'   -drop")
        self.assertEqual(_sanitize(" @evil"), "' @evil")

    def test_tab_before_formula_is_neutralized(self):
        self.assertEqual(_sanitize("\t=cmd"), "'\t=cmd")

    def test_cr_before_formula_is_neutralized(self):
        self.assertEqual(_sanitize("\r=cmd"), "'\r=cmd")

    def test_lf_before_formula_is_neutralized(self):
        self.assertEqual(_sanitize("\n=cmd"), "'\n=cmd")

    def test_mixed_whitespace_combination_before_formula_is_neutralized(self):
        self.assertEqual(_sanitize(" \t\r\n =cmd"), "' \t\r\n =cmd")
        self.assertEqual(_sanitize("\t\t+cmd"), "'\t\t+cmd")

    def test_ordinary_leading_whitespace_without_formula_char_is_preserved(self):
        self.assertEqual(_sanitize("  hello world"), "  hello world")
        self.assertEqual(_sanitize("\thello"), "\thello")
        self.assertEqual(_sanitize("\r\nhello"), "\r\nhello")

    def test_ordinary_data_is_unmodified(self):
        self.assertEqual(_sanitize("Timeout while retrieving information"), "Timeout while retrieving information")
        self.assertEqual(_sanitize("alice"), "alice")
        self.assertEqual(_sanitize(42), "42")

    def test_whitespace_only_value_does_not_crash(self):
        self.assertEqual(_sanitize("   "), "   ")
        self.assertEqual(_sanitize(""), "")

    def test_formula_char_in_middle_is_not_touched(self):
        self.assertEqual(_sanitize("a=b"), "a=b")
        self.assertEqual(_sanitize("cost-benefit"), "cost-benefit")

    def test_csv_output_neutralizes_whitespace_padded_formula(self):
        data = [("\t=cmd|'/C calc'!A1", 1), ("  +2+3", 2), (" \r-1+1", 3)]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "errors.csv")
            write_error_csv(data, out_path)
            with open(out_path, "r", newline="") as f:
                reader = list(csv.reader(f))
            self.assertTrue(reader[1][0].startswith("'"))
            self.assertTrue(reader[2][0].startswith("'"))
            self.assertTrue(reader[3][0].startswith("'"))


if __name__ == "__main__":
    unittest.main()
