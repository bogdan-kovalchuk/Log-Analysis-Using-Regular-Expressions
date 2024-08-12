#!/usr/bin/env python3

from aggregation import count_errors, count_per_user
from log_parser import parse_file
from reporting import write_error_csv, write_user_csv


def main():
    entries = parse_file("syslog.log")

    error_data = count_errors(entries)
    user_data = count_per_user(entries)

    write_error_csv(error_data, "error_message.csv")
    write_user_csv(user_data, "user_statistics.csv", max_users=8)


if __name__ == "__main__":
    main()
