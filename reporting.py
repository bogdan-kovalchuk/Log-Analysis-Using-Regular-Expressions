#!/usr/bin/env python3

import csv
import os
import tempfile

FORMULA_PREFIXES = ("=", "+", "-", "@")


def _sanitize(value):
    s = str(value)
    stripped = s.lstrip()
    if stripped and stripped[0] in FORMULA_PREFIXES:
        return "'" + s
    return s


def _atomic_write(filepath, write_fn, encoding="utf-8"):
    dirpath = os.path.dirname(os.path.abspath(filepath)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding=encoding) as f:
            write_fn(f)
        os.replace(tmp_path, filepath)
    except BaseException:
        os.unlink(tmp_path)
        raise


def write_error_csv(error_data, filepath, encoding="utf-8"):
    def _write(f):
        writer = csv.writer(f)
        writer.writerow(["Error", "Count"])
        for msg, count in error_data:
            writer.writerow([_sanitize(msg), count])
    _atomic_write(filepath, _write, encoding=encoding)


def write_user_csv(user_data, filepath, max_users=None, encoding="utf-8"):
    if max_users is not None and max_users < 0:
        raise ValueError("max_users must be non-negative")
    rows = user_data[:max_users] if max_users is not None else user_data

    def _write(f):
        writer = csv.writer(f)
        writer.writerow(["Username", "INFO", "ERROR"])
        for name, info_count, error_count in rows:
            writer.writerow([_sanitize(name), info_count, error_count])
    _atomic_write(filepath, _write, encoding=encoding)
