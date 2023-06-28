#!/usr/bin/env python3

import os
import tempfile
import unittest

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


class TestWriteHtmlFile(unittest.TestCase):
    def test_writes_html_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.html")
            write_html_file("<html>test</html>", out_path)
            with open(out_path, "r") as f:
                self.assertEqual(f.read(), "<html>test</html>")


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


if __name__ == "__main__":
    unittest.main()
