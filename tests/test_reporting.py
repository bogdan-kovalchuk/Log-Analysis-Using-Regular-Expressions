#!/usr/bin/env python3

import csv
import os
import tempfile
import unittest

from reporting import write_error_csv, write_user_csv


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


if __name__ == "__main__":
    unittest.main()
