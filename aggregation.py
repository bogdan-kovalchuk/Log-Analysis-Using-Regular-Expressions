#!/usr/bin/env python3

def count_errors(entries):
    per_error = {}
    for entry in entries:
        if entry.message_type == "ERROR":
            per_error[entry.message] = per_error.get(entry.message, 0) + 1
    sorted_errors = sorted(per_error.items(), key=lambda x: (-x[1], x[0].casefold(), x[0]))
    return [(msg, count) for msg, count in sorted_errors]


def count_per_user(entries):
    per_user = {}
    for entry in entries:
        if entry.message_type not in ("INFO", "ERROR"):
            continue
        if entry.user not in per_user:
            per_user[entry.user] = {"INFO": 0, "ERROR": 0}
        per_user[entry.user][entry.message_type] += 1
    sorted_users = sorted(per_user.items(), key=lambda item: (item[0].casefold(), item[0]))
    return [(name, counts["INFO"], counts["ERROR"]) for name, counts in sorted_users]
