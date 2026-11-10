"""Tests for build.py: one document per language, and the minified output.

    uv run --python ">=3.10,<3.15" --with-requirements build.py python -m unittest discover -s tests -v
"""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "site"
        build.main(["--out", str(cls.out), "--strict", "--no-minify"])  # the checks below read quoted attributes

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
        self.assertEqual(html.count('class="mark__face"'), 2 * html.count('<div class="mark">'))

    def test_travelling_mark_once_per_document(self):
        for doc in ("index.html", "lv/index.html"):
            html = self.doc(doc)
            self.assertEqual(html.count('class="mk"'), 1, doc)
            self.assertLess(html.index('class="mk"'), html.index('<section class="pg pg--index"'), doc)
        self.assertNotIn('class="mk"', self.doc("404.html"))

    def test_sitemap_two_urls(self):
        locs = re.findall(r"<loc>([^<]+)</loc>", (self.out / "sitemap.xml").read_text())
        self.assertEqual(locs, ["https://www.bixority.com/", "https://www.bixority.com/lv/"])

    def test_sitemap_lastmod(self):
        # a date for each URL in a git checkout; none outside one
        sitemap = (self.out / "sitemap.xml").read_text()
        dates = re.findall(r"<lastmod>([^<]+)</lastmod>", sitemap)
        if build.last_changed() is None:
            self.assertEqual(dates, [])
        else:
            self.assertEqual(len(dates), 2)
            for d in dates:
                self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$")

    def test_one_h1_per_document(self):
        for doc in ("index.html", "lv/index.html", "404.html"):
            self.assertEqual(len(re.findall(r"<h1[ >]", self.doc(doc))), 1, doc)
        self.assertIn('<h2 id="services-page-title">', self.doc("index.html"))

    def test_jsonld_company_and_website(self):
        for doc, here, lang in (("index.html", "/", "en"), ("lv/index.html", "/lv/", "lv")):
            m = re.search(r'<script type="application/ld\+json">(.*?)</script>', self.doc(doc), re.DOTALL)
            assert m is not None, doc
            org, site = json.loads(m.group(1))["@graph"]
            self.assertEqual(org["@type"], ["Organization", "ProfessionalService"])
            self.assertEqual(org["@id"], "https://www.bixority.com/#organization")
            self.assertEqual(org["contactPoint"]["email"], "info@bixority.com")
            self.assertIn("Kubernetes", org["knowsAbout"])
            meta = re.search(r'<meta name="description" content="([^"]*)">', self.doc(doc))
            assert meta is not None, doc
            self.assertEqual(org["description"], meta.group(1))
            self.assertEqual(site["@type"], "WebSite")
            self.assertEqual(site["url"], "https://www.bixority.com" + here)
            self.assertEqual(site["inLanguage"], lang)
            self.assertEqual(site["publisher"], {"@id": org["@id"]})

    def test_404_links_to_sections(self):
        html = self.doc("404.html")
        self.assertIn('href="/#services"', html)


class Outline(HTMLParser):
    """Start tags with sorted attributes, and the text with whitespace runs collapsed."""

    def __init__(self, normalise=True):
        super().__init__(convert_charrefs=True)
        self.normalise = normalise
        self.tags, self.chunks = [], []

    def handle_starttag(self, tag, attrs):
        # The only values the minifier rewrites: the space after the commas of the viewport content, and (below) the CSS name.
        # The stylesheet name carries the hash of its bytes, which differ when minified.
        attrs = [(k, v or "") for k, v in attrs]
        if self.normalise:
            attrs = [(k, re.sub(r"site\.[0-9a-f]{10}\.css", "site.css", v) if k == "href" else v) for k, v in attrs]
            attrs = [(k, v.replace(", ", ",") if tag == "meta" and k == "content" and "initial-scale" in v else v)
                     for k, v in attrs]
        self.tags.append((tag, sorted(attrs)))

    def handle_data(self, data):
        self.chunks.append(data)

    @property
    def text(self):
        # Whitespace runs collapse to one space. The minifier also drops whitespace between block elements
        # (and between the language links, of which only one is shown), so the spaces are removed in the end.
        return re.sub(r"\s+", "", "".join(self.chunks))


def outline(page_html, normalise=True):
    parser = Outline(normalise)
    parser.feed(page_html)
    parser.close()
    return parser


JSONLD = re.compile(r'<script type="?application/ld\+json"?>(.*?)</script>', re.DOTALL)
DOCS = ("index.html", "lv/index.html", "404.html")


class MinifiedBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.min = Path(cls._tmp.name) / "min"
        cls.raw = Path(cls._tmp.name) / "raw"
        build.main(["--out", str(cls.min), "--strict"])
        build.main(["--out", str(cls.raw), "--strict", "--no-minify"])

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def pair(self, name):
        return (self.min / name).read_text(encoding="utf-8"), (self.raw / name).read_text(encoding="utf-8")

    def css_files(self, root):
        return list((root / "assets").glob("site.*.css"))

    def test_smaller_without_comments(self):
        for name in DOCS:
            small, big = self.pair(name)
            self.assertLess(len(small), len(big), name)
            self.assertNotIn("<!--", small, name)

    def test_doctype_first(self):
        for name in DOCS:
            self.assertTrue(self.pair(name)[0].lstrip().lower().startswith("<!doctype html>"), name)

    def test_same_tags_and_text(self):
        for name in DOCS:
            small, big = (outline(t) for t in self.pair(name))
            self.assertEqual(small.tags, big.tags, name)
            self.assertEqual(small.text, big.text, name)

    def test_ids_unique(self):
        for name in DOCS:
            found = [dict(a)["id"] for _, a in outline(self.pair(name)[0]).tags if "id" in dict(a)]
            self.assertTrue(found, name)
            self.assertEqual(len(found), len(set(found)), name)

    def test_css_minified_and_fingerprinted(self):
        (small,), (big,) = self.css_files(self.min), self.css_files(self.raw)
        data = small.read_bytes()
        self.assertLess(len(data), big.stat().st_size)
        self.assertNotIn(b"/*", data)
        self.assertEqual(small.name, f"site.{hashlib.sha256(data).hexdigest()[:10]}.css")
        for name in DOCS:
            hrefs = [dict(a)["href"] for t, a in outline(self.pair(name)[0], normalise=False).tags
                     if t == "link" and dict(a).get("rel") == "stylesheet"]
            self.assertEqual(len(hrefs), 1, name)
            self.assertEqual(Path(hrefs[0]).name, small.name, name)

    def test_jsonld_same(self):
        for name in ("index.html", "lv/index.html"):
            blocks = [JSONLD.findall(t) for t in self.pair(name)]
            self.assertEqual(len(blocks[0]), 1, name)
            self.assertEqual(json.loads(blocks[0][0]), json.loads(blocks[1][0]), name)


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
