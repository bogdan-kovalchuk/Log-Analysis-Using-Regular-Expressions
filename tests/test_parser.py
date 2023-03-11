#!/usr/bin/env python3

import os
import tempfile
import unittest

from log_parser import LogEntry, parse_file, parse_line


class TestParseLine(unittest.TestCase):
    def test_error_line(self):
        line = "Jan 31 00:21:30 ubuntu.local ticky: ERROR The ticket was modified while updating (breee)"
        entry = parse_line(line)
        self.assertEqual(entry, LogEntry("ERROR", "The ticket was modified while updating", "breee"))

    def test_info_line(self):
        line = "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#4217] (mdouglas)"
        entry = parse_line(line)
        self.assertEqual(entry, LogEntry("INFO", "Created ticket [#4217]", "mdouglas"))

    def test_user_with_dots(self):
        line = "Jan 31 01:29:16 ubuntu.local ticky: INFO Commented on ticket [#6518] (rr.robinson)"
        entry = parse_line(line)
        self.assertEqual(entry, LogEntry("INFO", "Commented on ticket [#6518]", "rr.robinson"))

    def test_non_matching_line(self):
        self.assertIsNone(parse_line("some random log line"))

    def test_empty_line(self):
        self.assertIsNone(parse_line(""))


class TestParseFile(unittest.TestCase):
    def test_parse_small_file(self):
        content = (
            "Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#4217] (mdouglas)\n"
            "Jan 31 00:21:30 ubuntu.local ticky: ERROR The ticket was modified while updating (breee)\n"
            "unrelated line\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            entries = parse_file(tmp_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].message_type, "INFO")
            self.assertEqual(entries[0].user, "mdouglas")
            self.assertEqual(entries[1].message_type, "ERROR")
            self.assertEqual(entries[1].user, "breee")
        finally:
            os.unlink(tmp_path)

    def test_parse_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            tmp_path = f.name
        try:
            entries = parse_file(tmp_path)
            self.assertEqual(entries, [])
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
