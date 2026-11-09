# Single Document per Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** v3 and v4 each build one HTML document per language (`/`, `/lv/`) whose pages are `:target` sections, with a CSS-only page change: v4 travels and spins the mark, v3 fades the content.

**Architecture:** `build.py` renders every page source as before, then assembles them into one document per language (fragment links, unique ids, one mark `<defs>`); CSS shows the targeted section. v4's motion is CSS transitions on registered custom properties (`--cur`, `--old`, `--ready`) that yield a progress `--t`; a shared mark `.mk` travels between layout-formula positions on wide landscape screens, and each page's own mark spins in place elsewhere.

**Tech Stack:** Python 3.10+ standard library (`build.py`, `unittest`), plain CSS, Playwright (Firefox and Chromium) for the browser check, run with `uvx --with playwright python`.

**Spec:** `docs/superpowers/specs/2026-11-10-single-document-design.md`

## Global Constraints

- Pages in each document, in this order: index (Home, no id), `services`, `open-source`, `company`, `privacy`; `404.html` stays a separate file.
- One `<title>` and description per language: the home page's. Sitemap: `/` and `/lv/` only. No redirects.
- No JavaScript: remove `site.js`, its `<script>` tag and its bundling.
- Every id in a document is unique; the build fails otherwise.
- `--n`: Home 0, Services 1, Open source 2, Company 3, Privacy 4. `--spin: .7s`; spin easing `cubic-bezier(.45, 0, .2, 1)`; travel easing `cubic-bezier(.33, 0, .2, 1)`; content fade `.2s`; load gate `ready 0s 1s both`.
- All motion inside `@media screen and (prefers-reduced-motion: no-preference)`.
- Travel only at `(min-width: 48rem) and (orientation: landscape)`; elsewhere v4 spins the arriving page's own mark in place.
- Hand-over: the travelling mark and the resting mark differ by at most 1 px in x, y, width and height.
- Versions stay self-contained: v3 and v4 each get their own copy of every changed file; v1 and v2 do not change.
- Python passes `ruff check`, `ty check` and `pyright`. Commits are signed, and no commit message mentions Claude. Commit only when the owner asks; the "Commit" steps below are checkpoints to stage and show, and they run only with the owner's go-ahead.
- Content, colours and type do not change.

## Review Focus

1. A page link clicked while a change is still running (within .7 s): the new change must start from where the mark is, and no stale page may stay visible. Test in Task 4: double click within 300 ms ends on the second page with `--t` 0 within 1 s.
2. A sub-section link from another page (`#development` from Company): Services shows, the browser scrolls to the sub-section, and the header underline is on Services. Test in Task 2.
3. The Latvian document: its own home stage formula (2fr : 1fr) and its language link back to `/#<page>`. Test in Task 4 (hand-over at 1440x900 in `lv`) and Task 2 (language links in both languages).
4. A window resized between two changes (formulas use `cqw` and `svh`): the hand-over still holds at the new size. Test in Task 4: resize from 1440x900 to 1280x720, then change pages.
5. Gradients and the shadow filter on every page's mark when the first mark in the document is in a hidden section. Test in Task 1 (one `<defs>` at the top of `<body>`) and Task 4 (the inner-page mark's face is painted with its gradient: a pixel sample is not grey).

---

### Task 1: Single-document build (v4)

**Files:**
- Modify: `v4/build.py`
- Modify: `v4/src/layout.html` (remove the `<script>` tag; `<body>` gets the shared mark defs)
- Modify: `v4/tools/gen_mark.py` (write the defs as a separate partial; wrap each face SVG in `<div class="mark__face">`)
- Create: `v4/src/partials/mark-defs.html` (generated)
- Modify: `v4/src/partials/mark.html` (regenerated: no `<defs>`)
- Delete: `v4/src/assets/js/site.js`
- Create: `v4/tests/test_build.py`

**Interfaces:**
- Produces: `build.py --out DIR` writes `DIR/index.html`, `DIR/lv/index.html`, `DIR/404.html`, `DIR/lv/404.html` if present, `DIR/sitemap.xml`, `DIR/robots.txt`, `DIR/assets/…` and nothing else.
- Produces, in each document: `<section class="pg pg--index">` (no id) and `<section class="pg pg--<key>" id="<key>">` for the other pages; header links `<a class="hd__link hd__link--<key>" href="#<key>">`; one language link per page `<a class="hd__lang hd__lang--<key>" href="/lv/#<key>">` (Home: `/lv/`; LV to EN: `/#<key>` and `/`), relativized like other links; logo links `href="#"`.
- Produces: `prefix_ids(key: str, html: str, shared: set[str]) -> str` (prefixes every id in `shared` and its `aria-labelledby`/`href="#…"` references with `<key>-`), `check_fragments(dist: Path) -> list[tuple[str, str]]` (page, broken `#id`), `duplicate_ids(html: str) -> list[str]`.
- Produces: the mark partial without `<defs>`; `{{ partial_mark-defs }}` once, right after `<body>`, inside `<svg class="mark-defs" width="0" height="0" aria-hidden="true" focusable="false">` with `position: absolute` in CSS (never `display: none`).

- [ ] **Step 1: Write the failing tests** in `v4/tests/test_build.py` (`unittest`, builds once into a `tempfile.TemporaryDirectory` with `build.main(["--out", tmp, "--strict"])`):

```python
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
    for doc in ("index.html", "lv/index.html"):
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
    self.assertLess(html.index('class="mark-defs"'), html.index('<main'))
    self.assertEqual(html.count('class="mark__face"'), 2 * html.count('<div class="mark">'))

def test_sitemap_two_urls(self):
    locs = re.findall(r"<loc>([^<]+)</loc>", (self.out / "sitemap.xml").read_text())
    self.assertEqual(locs, ["https://www.bixority.com/", "https://www.bixority.com/lv/"])

def test_404_links_to_sections(self):
    html = self.doc("404.html")
    self.assertIn('href="/#services"', html)
```

Also a test that `check_fragments` reports a broken `#nope` link in a hand-written document in a temp dir.

- [ ] **Step 2: Run them and see them fail**

Run: `cd v4 && python3 -m unittest discover -s tests -v`
Expected: FAIL (`index.html` still links to `services/`, no `pg` sections).

- [ ] **Step 3: Regenerate the mark partials.** `gen_mark.py` writes `src/partials/mark-defs.html` (the current `<defs>` content) and `src/partials/mark.html` without `<defs>`, with `<div class="mark__face">…</div>` around `svg.mark__c` and `svg.mark__l`. Run `python3 tools/gen_mark.py` and `python3 tools/gen_mark.py --css` (the side CSS must be unchanged: diff it against `site.css`).

- [ ] **Step 4: Implement the build.** Render each page body exactly as today (same context, but `url_<key>` is `#<key>`, `url_index` and `home_url` are `#`, and the `privacy_url` is `#privacy`). Apply `prefix_ids` to every non-home page with `shared` = ids that occur in more than one page of that language. Wrap each body in its `<section class="pg pg--<key>">` (id on non-home pages) and render `layout.html` once per language with the home page's meta. The nav and language links are generated as in the Interfaces block. The 404 page keeps its own render with `url_<key>` = `/<prefix>/#<key>` root-relative. Then `relativize`, the sitemap with two URLs, `check_links` (files) plus `check_fragments` (ids in the same document; `#` alone is valid), and fail on any `duplicate_ids`. Remove the JS bundling from `build_assets`.

- [ ] **Step 5: Run the tests and the strict build**

Run: `cd v4 && python3 -m unittest discover -s tests -v && python3 build.py --strict && ruff check build.py tools tests && ty check build.py tools tests && pyright build.py tools tests`
Expected: all pass; `build: 2 documents and 1 error page written to dist/` (or the existing count line, updated).

- [ ] **Step 6: Commit checkpoint** — `git add v4/build.py v4/src v4/tools v4/tests` (with `site.js` removed); message `v4: build one document per language`.

### Task 2: Sections, header and content fade in CSS (v4)

**Files:**
- Modify: `v4/src/assets/css/site.css` (new block "THE DOCUMENT" near the top-of-file component notes; header rules; remove `@view-transition` and the whole cross-document block from the page-change section, keeping `@keyframes` only if Task 3 reuses them)
- Create: `v4/tools/check_pages.py` (Playwright; serves a dist folder on a free port with `http.server` in a thread)

**Interfaces:**
- Consumes: Task 1's classes (`pg`, `pg--<key>`, `hd__link--<key>`, `hd__lang--<key>`, `mark-defs`).
- Produces: `check_pages.py --dist DIR [--engine firefox|chromium|both] [--only NAME]` exiting non-zero on any failed check; checks are functions `check_<name>(page, base) -> list[str]` (failure messages), registered in a list so Tasks 3 and 4 add theirs.

- [ ] **Step 1: Write the failing checks** in `check_pages.py`, both engines, 1440x900 and 390x844:
  - `check_sections`: for targets `""`, `#services`, `#open-source`, `#company`, `#privacy`, `#development`: exactly one `.pg` is displayed and it is the expected one (`#development` shows `pg--services`); `scrollY` is 0 for page targets and above 0 for `#development`.
  - `check_header`: for each page target the displayed underline (`text-decoration-line` of `.hd__link--<key>`) is on that page only; Home has none; exactly one `.hd__lang` is displayed and its `href` ends with the same fragment (in both `/` and `/lv/`).
  - `check_print`: `page.emulate_media(media="print")` at `#company`: only `pg--company` is displayed and no `.mark` is displayed.
  - `check_defs_painted` (Review Focus 5): at `#services` 1440x900, a screenshot pixel at the mark's face centre is not equal in R, G and B (a gradient, not grey or missing).
- [ ] **Step 2: Run and see them fail**

Run: `python3 v4/build.py --strict && uvx --with playwright python v4/tools/check_pages.py --dist v4/dist`
Expected: FAIL in `check_sections` (every section displayed).

- [ ] **Step 3: Implement the CSS.** `.pg { display: none }`; Home shown by `:root:not(:has(.pg[id]:target, .pg[id] :target)) .pg--index`; each page by `:root:has(#<key>:target, #<key> :target) .pg--<key>`; `.pg[id] { scroll-margin-top: 100svh }`; the underline rule of today moved from `[aria-current]` to the same `:has` selectors on `.hd__link--<key>`; `.hd__lang` hidden except the one for the open page; `.mark-defs { position: absolute; width: 0; height: 0; overflow: hidden }`; under the motion media query `.pg { transition: opacity .2s }` and `@starting-style { .pg { opacity: 0 } }`. Inner-page head: the figure aligns to the top (`.page-head__obj { align-self: start }` at 48rem and up). Delete the `@view-transition` rule and every `:active-view-transition` rule.
- [ ] **Step 4: Run the checks and the build**

Run: `python3 v4/build.py --strict && uvx --with playwright python v4/tools/check_pages.py --dist v4/dist`
Expected: PASS for `sections`, `header`, `print`, `defs_painted` in both engines.

- [ ] **Step 5: Commit checkpoint** — `v4: show one page at a time with :target`.

### Task 3: The CSS-only page change (v4)

**Files:**
- Modify: `v4/src/assets/css/site.css` (replace the page-change section with "THE PAGE CHANGE": state, `.mk`, formulas, solids, spin in place, Privacy fade; update the top-of-file notes)
- Modify: `v4/build.py` (insert `.mk`: `<div class="mk" aria-hidden="true">{{ partial_mark }}</div>` as the first child of `<main>`, ids none since defs are shared)
- Modify: `v4/tools/check_pages.py` (motion checks)
- Modify: `v4/tests/test_build.py` (`.mk` present once per document)

**Interfaces:**
- Consumes: Task 2's sections and `check_pages.py` registry.
- Produces: registered properties `--cur`, `--old` (`<number>`), `--ready` (`<number>`), `--mx`, `--my`, `--mh` (`<length>`); derived `--t`, `--m` on `:root`; per-page `--n`; formula tokens `--W`, `--L` on the full-width container.

- [ ] **Step 1: Write the failing checks**, both engines, sizes 1440x900, 1920x1080, 1280x720, 1024x768 (landscape: travel), 820x1180 and 390x844 (spin in place). Sampling as in the spike (`--cur`, `--old`, the chevron's computed `transform`, the side opacity, element rects) at 0, 120, 360, 760 ms:
  - `check_no_motion_on_load`: load `/`, reload at `#company`, a new page at `#services`, a load at `#development`: for 1100 ms `--t` is 0 and every `.mark__side` has opacity 0.
  - `check_change_runs_once`: after the 1 s gate, Home to Services, Services to Company, Company to Privacy, Back, the logo: at 360 ms the side opacity is 1 and the chevron transform is not the rest matrix; at 760 ms `--t` is 0 and the transform is the rest matrix `matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, -0.4, 1, 0, 0, 0, 0, 1)`.
  - `check_travel_or_in_place`: landscape sizes: `.mk` is displayed with opacity 1 at 360 ms on a change between two pages with marks and the page's own mark has opacity 0; portrait and phone: `.mk` is not displayed and the arriving page's own mark turns (Home on phones; Home and inner pages on 820x1180).
  - `check_handover` (spec 1 px): landscape sizes, both languages at 1440x900: at 0 ms after a click `.mk`'s rect equals the old page's mark rect, and after 760 ms it equals the new page's mark rect, within 1 px.
  - `check_privacy_fade`: Services to Privacy at 1440x900: `.mk` opacity falls below .5 by 600 ms and its rect stays at the Services mark's place.
  - `check_reduced_motion`: with `reduced_motion="reduce"`, 100 ms after a click `--cur` already equals the new `--n`.
- [ ] **Step 2: Run and see them fail**

Run: `python3 v4/build.py --strict && uvx --with playwright python v4/tools/check_pages.py --dist v4/dist`
Expected: FAIL in `change_runs_once` (no motion yet).

- [ ] **Step 3: Implement the state and the solid** (spec section 2, State and the solid paragraph): the registered properties, `--n` per page via the Task 2 selectors, `--t` and `--m` on `:root`, the gate animation, transitions of `--cur` and `--old`; the chevron transforms `matrix3d(…, 0, -.4, 1, 0, …) rotate3d(1, -1, 0, calc(var(--t) * 360deg))` (cyan `-360deg`), sides and back and cast shadow by `--m`, the drawn sides and shadow by `1 - --m`, `.mark__face` with `backface-visibility: hidden`.
- [ ] **Step 4: Implement the travel** for `(min-width: 48rem) and (orientation: landscape)`: `body { container-type: inline-size }`; `.mk` absolutely positioned in `main` at `--mx`, `--my`, height `--mh`, shown only while `--m` is 1; the page's own marks at `opacity: calc(1 - var(--m))`; formulas per spec section 2 (Home EN 5:6, Home LV 2:1, inner pages column 3 right-aligned, top at the page head's top); `--mx`, `--my`, `--mh` transition over `--spin` with the travel easing; Privacy: `.mk` keeps the other page's place and fades with `t`. Phones and portrait: no `.mk`; the arriving section's own mark uses the same transforms.
- [ ] **Step 5: Run the checks, the tests and the build**

Run: `cd v4 && python3 -m unittest discover -s tests -v && python3 build.py --strict && cd .. && uvx --with playwright python v4/tools/check_pages.py --dist v4/dist`
Expected: every check passes in Firefox and Chromium.

- [ ] **Step 6: Review Focus checks** (add to `check_pages.py`, then pass):
  - `check_double_click` (Review Focus 1): Home, then Services, then Company within 300 ms: within 1100 ms of the last click `--t` is 0, only `pg--company` is displayed, and the mark rect equals Company's.
  - `check_subsection_from_other_page` (Review Focus 2): from `#company`, click a link to `#development`: `pg--services` displayed, `.hd__link--services` underlined, `scrollY` above 0.
  - `check_resize_then_change` (Review Focus 4): load at 1440x900, resize to 1280x720, wait 1100 ms, Home to Services: hand-over within 1 px.
- [ ] **Step 7: Commit checkpoint** — `v4: CSS-only page change in every browser`.

### Task 4: v3 (structure and content fade)

**Files:**
- Modify: `v3/build.py`, `v3/src/layout.html`, `v3/tools/gen_mark.py`, `v3/src/partials/` (copies of Task 1's changes, with v3's own mark partial: defs split out; v3 has no 3D, so no `.mark__face` and no `.mk`)
- Delete: `v3/src/assets/js/site.js`
- Modify: `v3/src/assets/css/site.css` (Task 2's block, without `align-self: start` for the inner mark: v3 keeps it centred)
- Create: `v3/tests/test_build.py` (Task 1's tests minus the `.mark__face` assertion), `v3/tools/check_pages.py` (Task 2's checks plus `check_no_motion`: during a change no element other than `.pg` has a running animation or transition)

**Interfaces:**
- Consumes: Task 1 and Task 2 (copied, not imported).

- [ ] **Step 1: Copy the tests and checks; run them and see them fail**

Run: `cd v3 && python3 -m unittest discover -s tests -v`
Expected: FAIL (v3 still multi-page).

- [ ] **Step 2: Port the build and the CSS** as listed above.

- [ ] **Step 3: Run everything**

Run: `cd v3 && python3 -m unittest discover -s tests -v && python3 build.py --strict && cd .. && uvx --with playwright python v3/tools/check_pages.py --dist v3/dist && ruff check v3 && ty check v3 && pyright v3`
Expected: all pass.

- [ ] **Step 4: Commit checkpoint** — `v3: one document per language`.

### Task 5: CI, docs and final verification

**Files:**
- Modify: `.github/workflows/ci.yaml` (the check job runs `python3 -m unittest discover -s v3/tests` and `-s v4/tests` after the builds; the Playwright check is not run in CI)
- Modify: `v3/README.md`, `v4/README.md`, `v3/docs/v3-design.md`, `v4/docs/v4-design.md` ("The page change" and the open items: Firefox now covered; Safari still untested; the 1 s gate), `README.md` (one line: v3 and v4 are one document per language)
- Modify: `v4/src/assets/css/site.css` and `v3/src/assets/css/site.css` top-of-file notes (THE DOCUMENT, THE PAGE CHANGE)

- [ ] **Step 1: Update CI and the docs** as listed.
- [ ] **Step 2: Final verification**

Run:
```bash
for v in v1 v2 v3 v4; do python3 $v/build.py --strict || exit 1; done
python3 -m unittest discover -s v3/tests && python3 -m unittest discover -s v4/tests
uvx --with playwright python v3/tools/check_pages.py --dist v3/dist
uvx --with playwright python v4/tools/check_pages.py --dist v4/dist
node --test 'infra/functions/*.test.mjs'
actionlint .github/workflows/ci.yaml
```
Expected: all pass. Then record a short video of v4 in Firefox and Chromium (Home, Services, Company, Privacy, Back, LV) for the owner to judge the motion.
- [ ] **Step 3: Commit checkpoint** — `Document the single-document v3 and v4`. Pushing deploys v4 (the `production` environment has no required reviewer): push only when the owner asks.
