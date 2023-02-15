#!/usr/bin/env python3

import re
from collections import namedtuple

LOG_PATTERN = re.compile(r"ticky: ([\w]+) (.+) \(([\w.]+)\)")

LogEntry = namedtuple("LogEntry", ["message_type", "message", "user"])


VALID_TYPES = {"INFO", "ERROR"}


def parse_line(line):
    match = LOG_PATTERN.search(line)
    if not match:
        return None
    msg_type = match.group(1)
    if msg_type not in VALID_TYPES:
        return None
    return LogEntry(msg_type, match.group(2), match.group(3))


def parse_file(filepath):
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
    return entries
