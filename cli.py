#!/usr/bin/env python3

import argparse
import os
import sys

from aggregation import count_errors, count_per_user
from log_parser import parse_file
from reporting import write_error_csv, write_user_csv


def build_parser():
    parser = argparse.ArgumentParser(description="Analyze ticky log entries")
    parser.add_argument("logfile", nargs="?", default="syslog.log",
                        help="Path to the syslog log file")
    parser.add_argument("--error-csv", default="error_message.csv",
                        help="Output path for error message CSV")
    parser.add_argument("--user-csv", default="user_statistics.csv",
                        help="Output path for user statistics CSV")
    parser.add_argument("--encoding", default="utf-8",
                        help="Encoding of the log file (default: utf-8)")
    return parser


def _validate_output_paths(logfile, error_csv, user_csv):
    log_real = os.path.normcase(os.path.realpath(logfile))
    error_real = os.path.normcase(os.path.realpath(error_csv))
    user_real = os.path.normcase(os.path.realpath(user_csv))

    if error_real == log_real:
        raise ValueError(f"--error-csv must not overwrite the source log file: {error_csv}")
    if user_real == log_real:
        raise ValueError(f"--user-csv must not overwrite the source log file: {user_csv}")
    if error_real == user_real:
        raise ValueError(f"--error-csv and --user-csv must not point to the same file: {error_csv}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if os.path.isdir(args.logfile):
        print(f"Error: log file path is a directory: {args.logfile}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.logfile):
        print(f"Error: log file not found: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    try:
        _validate_output_paths(args.logfile, args.error_csv, args.user_csv)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = parse_file(args.logfile, encoding=args.encoding)
        error_data = count_errors(entries)
        user_data = count_per_user(entries)

        write_error_csv(error_data, args.error_csv)
        write_user_csv(user_data, args.user_csv)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
