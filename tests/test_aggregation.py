#!/usr/bin/env python3

import unittest

from aggregation import count_errors, count_per_user
from log_parser import LogEntry


class TestCountErrors(unittest.TestCase):
    def test_counts_only_errors(self):
        entries = [
            LogEntry("ERROR", "Timeout", "alice"),
            LogEntry("INFO", "Created ticket", "bob"),
            LogEntry("ERROR", "Timeout", "charlie"),
            LogEntry("ERROR", "Permission denied", "alice"),
        ]
        result = count_errors(entries)
        self.assertEqual(result, [("Timeout", 2), ("Permission denied", 1)])

    def test_empty_entries(self):
        self.assertEqual(count_errors([]), [])

    def test_no_errors(self):
        entries = [LogEntry("INFO", "Created ticket", "alice")]
        self.assertEqual(count_errors(entries), [])

    def test_sorted_by_count_descending(self):
        entries = [
            LogEntry("ERROR", "A", "u1"),
            LogEntry("ERROR", "B", "u2"),
            LogEntry("ERROR", "B", "u3"),
            LogEntry("ERROR", "B", "u4"),
        ]
        result = count_errors(entries)
        self.assertEqual(result[0], ("B", 3))
        self.assertEqual(result[1], ("A", 1))

    def test_tie_break_is_alphabetical_by_message(self):
        entries = [
            LogEntry("ERROR", "Zebra", "u1"),
            LogEntry("ERROR", "Alpha", "u2"),
            LogEntry("ERROR", "Mango", "u3"),
        ]
        result = count_errors(entries)
        messages = [msg for msg, _ in result]
        self.assertEqual(messages, ["Alpha", "Mango", "Zebra"])


class TestCountPerUser(unittest.TestCase):
    def test_counts_info_and_error(self):
        entries = [
            LogEntry("INFO", "Created ticket", "alice"),
            LogEntry("ERROR", "Timeout", "alice"),
            LogEntry("INFO", "Closed ticket", "bob"),
        ]
        result = count_per_user(entries)
        self.assertEqual(result, [("alice", 1, 1), ("bob", 1, 0)])

    def test_empty_entries(self):
        self.assertEqual(count_per_user([]), [])

    def test_sorted_alphabetically(self):
        entries = [
            LogEntry("INFO", "msg", "charlie"),
            LogEntry("INFO", "msg", "alice"),
            LogEntry("INFO", "msg", "bob"),
        ]
        result = count_per_user(entries)
        names = [r[0] for r in result]
        self.assertEqual(names, ["alice", "bob", "charlie"])

    def test_unknown_message_type_is_ignored(self):
        entries = [
            LogEntry("INFO", "msg", "alice"),
            LogEntry("WARNING", "msg", "alice"),
            LogEntry("DEBUG", "msg", "bob"),
            LogEntry("ERROR", "msg", "bob"),
        ]
        result = count_per_user(entries)
        self.assertEqual(result, [("alice", 1, 0), ("bob", 0, 1)])


if __name__ == "__main__":
    unittest.main()
