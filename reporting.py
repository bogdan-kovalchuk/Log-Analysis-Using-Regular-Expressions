#!/usr/bin/env python3

import csv

FORMULA_PREFIXES = ("=", "+", "-", "@")


def _sanitize(value):
    s = str(value)
    if s and s[0] in FORMULA_PREFIXES:
        return "'" + s
    return s


def write_error_csv(error_data, filepath):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Error", "Count"])
        for msg, count in error_data:
            writer.writerow([_sanitize(msg), count])


def write_user_csv(user_data, filepath, max_users=None):
    rows = user_data[:max_users] if max_users is not None else user_data
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "INFO", "ERROR"])
        for name, info_count, error_count in rows:
            writer.writerow([_sanitize(name), info_count, error_count])
