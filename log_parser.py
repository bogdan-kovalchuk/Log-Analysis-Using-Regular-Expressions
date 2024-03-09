#!/usr/bin/env python3

import codecs
import os
import re
from collections import namedtuple

LOG_PATTERN = re.compile(r"ticky: ([\w]+) (.+) \(([\w.-]+)\)\s*$")

LogEntry = namedtuple("LogEntry", ["message_type", "message", "user"])


VALID_TYPES = {"INFO", "ERROR"}


def parse_line(line):
    match = LOG_PATTERN.search(line)
    if not match:
        return None
    msg_type = match.group(1)
    if msg_type not in VALID_TYPES:
        return None
    message = match.group(2).strip()
    if not message:
        return None
    return LogEntry(msg_type, message, match.group(3))


def parse_file(filepath, encoding="utf-8"):
    if os.path.isdir(filepath):
        raise IsADirectoryError(f"Path is a directory, not a file: {filepath}")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Log file not found: {filepath}")
    actual_encoding = encoding
    if codecs.lookup(encoding).name == "utf-8":
        with open(filepath, "rb") as f:
            if f.read(3) == b"\xef\xbb\xbf":
                actual_encoding = "utf-8-sig"
    entries = []
    with open(filepath, "r", encoding=actual_encoding, errors="replace") as f:
        for line in f:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
    return entries
