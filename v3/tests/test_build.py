"""Tests for build.py: one document per language. Standard library only.

    python3 -m unittest discover -s tests -v
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "site"
        build.main(["--out", str(cls.out), "--strict"])

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def doc(self, name):
        return (self.out / name).read_text(encoding="utf-8")

    def test_one_document_per_language(self):
        self.assertTrue((self.out / "index.html").is_file())
        self.assertTrue((self.out / "lv/index.html").is_file())
        for gone in ("services", "open-source", "company", "privacy", "lv/services"):
            self.assertFalse((self.out / gone).exists(), gone)

    def test_sections_in_order(self):
        html = self.doc("index.html")
        keys = re.findall(r'<section class="pg pg--([\w-]+)"', html)
        self.assertEqual(keys, ["index", "services", "open-source", "company", "privacy"])
        self.assertIn('<section class="pg pg--services" id="services"', html)
        self.assertNotIn('class="pg pg--index" id=', html)

    def test_ids_unique(self):
        for doc in ("index.html", "lv/index.html", "404.html"):
            self.assertEqual(build.duplicate_ids(self.doc(doc)), [], doc)

    def test_shared_ids_prefixed(self):
        html = self.doc("index.html")
        self.assertIn('id="services-page-title"', html)
        self.assertIn('aria-labelledby="services-page-title"', html)
        self.assertIn('id="company-principle"', html)
        self.assertIn('id="principle"', html)  # Home keeps its own

    def test_links_are_fragments(self):
        html = self.doc("index.html")
        self.assertIn('href="#development"', html)
        self.assertNotRegex(html, r'href="[^"#]*services/')
        self.assertIn('class="hd__lang hd__lang--services" href="lv/#services"', html)
        self.assertIn('class="hd__lang hd__lang--services" href="../#services"', self.doc("lv/index.html"))

    def test_one_title_no_script(self):
        html = self.doc("index.html")
        self.assertEqual(html.count("<title>"), 1)
        self.assertNotIn("<script src=", html)
        self.assertFalse(list((self.out / "assets").glob("site.*.js")))

    def test_mark_defs_once_and_rendered(self):
        html = self.doc("index.html")
        self.assertEqual(html.count('id="g-l"'), 1)
        self.assertLess(html.index('class="mark-defs"'), html.index("<main"))
        self.assertGreater(html.count('class="mark"'), 1)  # several marks share the one set of defs

    def test_sitemap_two_urls(self):
        locs = re.findall(r"<loc>([^<]+)</loc>", (self.out / "sitemap.xml").read_text())
        self.assertEqual(locs, ["https://www.bixority.com/", "https://www.bixority.com/lv/"])

    def test_404_links_to_sections(self):
        html = self.doc("404.html")
        self.assertIn('href="/#services"', html)


class CheckFragmentsTest(unittest.TestCase):
    def test_broken_fragment_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            (dist / "index.html").write_text(
                '<a href="#">top</a><a href="#ok">ok</a><a href="#nope">bad</a><p id="ok"></p>', encoding="utf-8")
            self.assertEqual(build.check_fragments(dist), [("index.html", "#nope")])


class PrefixIdsTest(unittest.TestCase):
    def test_prefixes_shared_ids_and_references(self):
        html = '<section aria-labelledby="t"><h1 id="t">x</h1><a href="#t">y</a><b id="own"></b></section>'
        out = build.prefix_ids("p", html, {"t"})
        self.assertEqual(
            out, '<section aria-labelledby="p-t"><h1 id="p-t">x</h1><a href="#p-t">y</a><b id="own"></b></section>')


if __name__ == "__main__":
    unittest.main()
