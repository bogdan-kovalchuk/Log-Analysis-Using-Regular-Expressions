#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch

from csv_to_html import data_to_html, process_csv, write_html_file


class TestDataToHtml(unittest.TestCase):
    def test_html_escapes_special_characters(self):
        data = [["Name", "Value"], ["<script>alert(1)</script>", "a&b"]]
        result = data_to_html("Test", data)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("a&amp;b", result)

    def test_header_row_uses_th(self):
        data = [["Col1", "Col2"], ["v1", "v2"]]
        result = data_to_html("Title", data)
        self.assertIn("<th>Col1</th>", result)
        self.assertIn("<td>v1</td>", result)

    def test_title_is_escaped_for_non_empty_table(self):
        title = "<img src=x onerror=alert(1)>"
        data = [["Col1"], ["v1"]]
        result = data_to_html(title, data)
        self.assertNotIn("<img", result)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", result)

    def test_title_is_escaped_for_empty_table(self):
        title = "<script>alert(1)</script>"
        result = data_to_html(title, [])
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", result)

    def test_title_with_quotes_is_escaped(self):
        title = '"><svg onload=alert(1)>'
        data = [["Col1"], ["v1"]]
        result = data_to_html(title, data)
        self.assertNotIn('"><svg', result)
        self.assertIn("&quot;&gt;&lt;svg onload=alert(1)&gt;", result)


class TestProcessCsv(unittest.TestCase):
    def test_reads_csv_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write("a,b\n1,2\n")
            tmp_path = f.name
        try:
            result = process_csv(tmp_path)
            self.assertEqual(result, [["a", "b"], ["1", "2"]])
        finally:
            os.unlink(tmp_path)

    def test_reads_bom_prefixed_csv_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("\ufeffName,Value\nalice,1\n")
            tmp_path = f.name
        try:
            self.assertEqual(process_csv(tmp_path), [["Name", "Value"], ["alice", "1"]])
        finally:
            os.unlink(tmp_path)

    def test_rejects_directory_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(IsADirectoryError):
                process_csv(tmpdir)

    def test_rejects_nonexistent_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = os.path.join(tmpdir, "missing.csv")
            with self.assertRaises(FileNotFoundError):
                process_csv(missing)


class TestWriteHtmlFile(unittest.TestCase):
    def test_writes_html_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.html")
            write_html_file("<html>test</html>", out_path)
            with open(out_path, "r") as f:
                self.assertEqual(f.read(), "<html>test</html>")

    def test_rejects_directory_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "out.html")
            os.mkdir(out_dir)
            with self.assertRaises(IsADirectoryError):
                write_html_file("<html>test</html>", out_dir)
            # Directory itself must remain untouched (no files written inside)
            self.assertEqual(os.listdir(out_dir), [])

    def test_atomic_write_no_temp_left_on_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.html")
            write_html_file("<html>test</html>", out_path)
            leftovers = [f for f in os.listdir(tmpdir) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])

    def test_preserves_existing_output_on_injected_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.html")
            with open(out_path, "w") as f:
                f.write("<html>original</html>")

            with patch("csv_to_html.os.replace", side_effect=OSError("simulated failure")):
                with self.assertRaises(OSError):
                    write_html_file("<html>new</html>", out_path)

            with open(out_path, "r") as f:
                self.assertEqual(f.read(), "<html>original</html>")

            leftovers = [f for f in os.listdir(tmpdir) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])


class TestHtmlStructure(unittest.TestCase):
    def test_no_duplicate_closing_tr(self):
        data = [["H1"], ["V1"]]
        result = data_to_html("T", data)
        self.assertEqual(result.count("</tr>"), 2)

    def test_extension_validation_uses_endswith(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "data.csv")
            with open(csv_path, "w", newline="") as f:
                f.write("a,b\n1,2\n")
            html_path = os.path.join(tmpdir, "data.html")
            from csv_to_html import main as csv_main
            import sys
            old_argv = sys.argv
            try:
                sys.argv = ["csv_to_html.py", csv_path, html_path]
                csv_main()
                self.assertTrue(os.path.exists(html_path))
            finally:
                sys.argv = old_argv

    def test_empty_data_returns_no_data_message(self):
        result = data_to_html("Empty", [])
        self.assertIn("No data", result)
        self.assertNotIn("<table>", result)

    def test_main_rejects_directory_csv_input_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_dir = os.path.join(tmpdir, "data.csv")
            os.mkdir(csv_dir)
            html_path = os.path.join(tmpdir, "data.html")
            from csv_to_html import main as csv_main
            import sys
            old_argv = sys.argv
            try:
                sys.argv = ["csv_to_html.py", csv_dir, html_path]
                with self.assertRaises(SystemExit) as ctx:
                    csv_main()
                self.assertEqual(ctx.exception.code, 1)
                self.assertFalse(os.path.exists(html_path))
            finally:
                sys.argv = old_argv

    def test_main_rejects_directory_html_output_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "data.csv")
            with open(csv_path, "w", newline="") as f:
                f.write("a,b\n1,2\n")
            html_dir = os.path.join(tmpdir, "data.html")
            os.mkdir(html_dir)
            from csv_to_html import main as csv_main
            import sys
            old_argv = sys.argv
            try:
                sys.argv = ["csv_to_html.py", csv_path, html_dir]
                with self.assertRaises(SystemExit) as ctx:
                    csv_main()
                self.assertEqual(ctx.exception.code, 1)
                self.assertEqual(os.listdir(html_dir), [])
            finally:
                sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
