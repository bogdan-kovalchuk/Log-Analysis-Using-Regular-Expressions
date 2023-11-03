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

    def test_unknown_message_type_is_skipped(self):
        line = "Jan 31 00:00:00 host ticky: WARNING Something happened (alice)"
        self.assertIsNone(parse_line(line))

    def test_debug_message_type_is_skipped(self):
        line = "Jan 31 00:00:00 host ticky: DEBUG Trace info (bob)"
        self.assertIsNone(parse_line(line))


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

    def test_parse_file_with_non_utf8_bytes(self):
        content = b"Jan 31 00:09:39 ubuntu.local ticky: INFO Created ticket [#1] (alice)\n"
        content += b"Jan 31 00:10:00 ubuntu.local ticky: INFO Bad line \xff\xfe (bob)\n"
        content += b"Jan 31 00:11:00 ubuntu.local ticky: ERROR Timeout (charlie)\n"
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            entries = parse_file(tmp_path)
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].user, "alice")
            self.assertEqual(entries[2].user, "charlie")
        finally:
            os.unlink(tmp_path)

    def test_parse_file_missing_raises_descriptive_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            parse_file("/nonexistent/path/to/syslog.log")
        self.assertIn("/nonexistent/path/to/syslog.log", str(ctx.exception))

    def test_parse_file_directory_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(IsADirectoryError) as ctx:
                parse_file(tmpdir)
            self.assertIn(tmpdir, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
