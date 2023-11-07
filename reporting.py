#!/usr/bin/env python3

import csv


def write_error_csv(error_data, filepath):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Error", "Count"])
        writer.writerows(error_data)


def write_user_csv(user_data, filepath, max_users=None):
    rows = user_data[:max_users] if max_users is not None else user_data
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "INFO", "ERROR"])
        writer.writerows(rows)
