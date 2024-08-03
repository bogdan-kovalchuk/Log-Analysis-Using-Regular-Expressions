#!/usr/bin/env python3

import sys
import csv
import os
import html
import tempfile

def process_csv(csv_file):
    """Turn the contents of the CSV file into a list of lists"""
    if os.path.isdir(csv_file):
        raise IsADirectoryError(f"CSV input path is a directory: {csv_file}")
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(f"CSV input path is not a regular file: {csv_file}")
    print("Processing {}".format(csv_file))
    with open(csv_file, "r", encoding="utf-8-sig", newline="") as datafile:
        data = list(csv.reader(datafile))
    return data

def data_to_html(title, data):
    """Turns a list of lists into an HTML table"""
    escaped_title = html.escape(title, quote=True)

    if not data:
        return "<html><body><h2>{}</h2><p>No data</p></body></html>".format(escaped_title)

    # HTML Headers
    html_content = """
<html>
<head>
<style>
table {
  width: 25%;
  font-family: arial, sans-serif;
  border-collapse: collapse;
}

tr:nth-child(odd) {
  background-color: #dddddd;
}

td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}
</style>
</head>
<body>
"""


    # Add the header part with the given title
    html_content += "<h2>{}</h2><table>".format(escaped_title)

    # Add each row in data as a row in the table
    # The first line is special and gets treated separately
    for i, row in enumerate(data):
        html_content += "<tr>"
        for column in row:
            escaped = html.escape(column, quote=True)
            if i == 0:
                html_content += "<th>{}</th>".format(escaped)
            else:
                html_content += "<td>{}</td>".format(escaped)
        html_content += "</tr>"

    html_content += """</table></body></html>"""
    return html_content


def write_html_file(html_string, html_file):

    if os.path.isdir(html_file):
        raise IsADirectoryError(f"HTML output path is a directory: {html_file}")

    # Making a note of whether the html file we're writing exists or not
    if os.path.exists(html_file):
        print("{} already exists. Overwriting...".format(html_file))

    dirpath = os.path.dirname(os.path.abspath(html_file)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as htmlfile:
            htmlfile.write(html_string)
        os.replace(tmp_path, html_file)
    except BaseException:
        os.unlink(tmp_path)
        raise
    print("Table succesfully written to {}".format(html_file))

def main(argv=None):
    """Verifies the arguments and then calls the processing function"""
    args = sys.argv[1:] if argv is None else argv

    # Check that command-line arguments are included
    if len(args) < 2:
        print("ERROR: Missing command-line argument!")
        print("Exiting program...")
        sys.exit(1)

    # Open the files
    csv_file, html_file = args[:2]

    # Check that file extensions are included
    if os.path.splitext(csv_file)[1].lower() != ".csv":
        print('Missing ".csv" file extension from first command-line argument!')
        print("Exiting program...")
        sys.exit(1)

    if os.path.splitext(html_file)[1].lower() != ".html":
        print('Missing ".html" file extension from second command-line argument!')
        print("Exiting program...")
        sys.exit(1)

    # Check that the csv file exists
    if not os.path.exists(csv_file):
        print("{} does not exist".format(csv_file))
        print("Exiting program...")
        sys.exit(1)

    if os.path.normcase(os.path.realpath(csv_file)) == os.path.normcase(os.path.realpath(html_file)):
        print("Input CSV and output HTML paths must differ")
        print("Exiting program...")
        sys.exit(1)

    # Process the data and turn it into an HTML
    try:
        data = process_csv(csv_file)
        title = os.path.splitext(os.path.basename(csv_file))[0].replace("_", " ").title()
        html_string = data_to_html(title, data)
        write_html_file(html_string, html_file)
    except (OSError, UnicodeError) as e:
        print(f"Error: {e}")
        print("Exiting program...")
        sys.exit(1)

if __name__ == "__main__":
    main()
