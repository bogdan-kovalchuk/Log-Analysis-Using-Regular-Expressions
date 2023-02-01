#!/usr/bin/env python3

import operator
import re
import csv

def main():
    per_error={}
    per_user={}
    with open("syslog.log", "r") as file:
        for line in file:
            match = re.search(r"ticky: ([\w]+) (.+) \(([\w.]+)\)", line)
            message_type, error, user = match.group(1), match.group(2), match.group(3)
            if message_type == "ERROR":
                if error not in per_error:
                    per_error[error]=1
                else:
                    per_error[error]+=1
            if user not in per_user:
                per_user[user]={"INFO":0,"ERROR":0}
            per_user[user][message_type]+=1

    per_error = sorted(per_error.items(), key=operator.itemgetter(1), reverse=True)
    per_error = tuple(map(lambda x: (x[0], x[1]), per_error))

    per_user = sorted(per_user.items(), key=operator.itemgetter(0))
    per_user = tuple(map(lambda x: (x[0], x[1]["INFO"], x[1]["ERROR"]), per_user))

    with open("error_message.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Error", "Count"])
        writer.writerows(per_error)

    with open("user_statistics.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "INFO", "ERROR"])
        writer.writerows(per_user[0:8])

if __name__ == "__main__":
    main()