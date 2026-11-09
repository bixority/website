# Single document per language, with a CSS-only page change (v3 and v4)

Date: 2026-11-10. Status: design, waiting for the owner's review.

## Goal

The v4 page change (the mark spins as two solids while it travels to its place on the next page) runs only in
browsers with cross-document view transitions, so Firefox never shows it. The owner wants it in Chrome, Edge and
Firefox with CSS alone. Pages therefore become sections of one HTML document per language, switched with `:target`,
and the motion is driven by CSS transitions. v3 gets the same structure without the spin.

A throwaway spike (2026-11-09, scratchpad) proved the mechanism in Firefox 159 and Chromium 158: one spin per change,
Back and Forward included, no motion on load, reload or a new tab, reduced motion respected.

## Decisions (owner, 2026-11-09 and 2026-11-10)

| Topic | Decision |
|---|---|
| Versions | v3 and v4 both become single-document. v3: no spin. v4: the spin. |
| Pages in the document | Home, Services, Open source, Company and Privacy. The 404 page stays a separate file. |
| Title, search | One `<title>` and description per language. |
| Old URLs | `/services/` and the other page folders go away; no redirects ("I don't care about old page URLs"). |
| Language link | Keeps the open page: on Services, "Latviski" opens `/lv/#services`. |
| Mark placement during travel | Layout formulas (calc from the layout tokens), not anchor positioning (Firefox does not animate a change of anchor). |
| Inner-page mark (v4) | Top-aligned with the page head instead of centred on the heading text, so its place is computable. |
| Click while scrolled down | The page jumps to the top, then the mark spins into place. |
| Page without a mark (Privacy) | The mark fades while it spins. |
| Phones and upright tablets (v4) | No travel: the arriving page's own mark spins once in place. |
| v3 page change | Content fade only; the mark appears in its place. |

## 1. Document and build (v3 and v4)

`build.py` writes, per language, one `index.html` (`/` and `/lv/`) and keeps the 404 page as it is. The page sources
in `src/pages/<lang>/` stay one file per page.

- The document's `<main>` holds one `<section class="pg pg--<key>" id="<key>">` per page in `site.json` order;
  Home's section has no id and is the default. Page ids are `services`, `open-source`, `company`, `privacy`; no page
  uses these ids today.
- A page is shown when its section is the target or holds the target:
  `:root:has(#services:target, #services :target)` rules generated per page, so sub-section links
  (`#development`, `#devops`, `#consulting`) open Services and scroll to the sub-section. Home shows when no page is
  targeted. All other sections are `display: none` (so they are also out of the accessibility tree and out of print).
- Ids used on more than one page (`page-title`, and `principle` on Home and Company) get the page key as a prefix
  on the non-home pages (`services-title`, `company-principle`), with their `aria-labelledby` references. The build
  fails on any remaining duplicate id in a document.
- Links between pages become fragments: `{{ url_services }}` renders `#services`, `{{ url_index }}` renders `#`
  (an empty fragment: no target, so Home), `{{ url_services }}#development` renders `#development`. The header logo
  and the footer logo link to `#`.
- Scrolling: a page section starts at the top of `<main>`, just under the header, so `scroll-margin-top: 100svh` on
  page sections makes every page jump land at scroll 0, with the header in view, whatever the header's height
  (the browser cannot scroll above 0). Sub-section targets keep the browser's normal scroll.
- Header: the current-page underline is chosen by `:has()` rules per nav item (`aria-current` cannot follow a CSS
  state; the visual underline stays). The language link is rendered once per page, each `href` pointing at the same
  page in the other language (`/lv/#services`), and CSS shows the one for the open page.
- `<title>` and description: the home page's. Canonical and hreflang alternates: `/` and `/lv/`. JSON-LD as today.
  The sitemap lists `/` and `/lv/` only.
- No JavaScript: `site.js` and its `<script>` tag are removed (its two jobs, the old view-transition types and the
  `file://` link rewrite for folder links, no longer apply). The content security policy already allows no scripts
  other than `'self'`; nothing changes there.
- `@view-transition` and the cross-document rules are removed from v4's CSS.
- The 404 page links to the pages as `/#services` and `/lv/#services` (root-relative, as today).
- Home keeps its scroll-driven reveal (the chevrons split and grey on the problem line) inside its section.
- Print: prints the open section only (the others are `display: none`), without the mark, as the print rules say today.
- The link check in `build.py --strict` also checks fragments: every `#id` link must name an id in its document.
- `infra/` is unchanged: the CloudFront function still serves `/` and `/lv/` from `index.html`, and its tests use
  example paths that stay valid. The site's README files and the v3 and v4 design notes are updated.

## 2. Motion in v4

### State

- `:root` sets `--n` per page: Home 0, Services 1, Open source 2, Company 3, Privacy 4.
- Registered properties (`@property`, `<number>`, inherited): `--cur` takes `--n` and transitions over `--spin`
  (.7 s, `cubic-bezier(.45, 0, .2, 1)`); `--old` takes `--n` with a 0 s transition delayed by `--spin`, so it keeps the
  old page's number for the whole change.
- Progress `--t = --ready * (cur - old) / (n - old + .0001)`: 0 at rest, 0 to 1 during a change. `--m` is 1 while a
  change runs and 0 at rest (`clamp(0, min(t, 1 - t) * 10000, 1)`).
- `--ready` (registered number) is 0 for the first second after a load and then 1, by a one-off animation
  (`ready 0s 1s both`). Firefox matches `:target` only after the first style, so a reload or a link to `#company`
  would otherwise look like a change from Home; the gate lets that change run unseen. A click within the first second
  after a load changes the page without motion.
- Transitions never run on a page's first style, so loading never moves anything.
- All transitions are inside `@media screen and (prefers-reduced-motion: no-preference)`; otherwise pages change
  instantly.

### Wide landscape screens (min-width 48rem and landscape): travel

- One extra mark, `.mk` (`aria-hidden`, the same partial), absolutely positioned in `<main>`, is visible only while
  `--m` is 1. Each page's own mark is hidden while `--m` is 1 (`opacity: calc(1 - var(--m))`), so at rest the page's
  own mark, in the layout, is what shows.
- `.mk`'s left, top and height are registered lengths (`--mx`, `--my`, `--mh`) that transition over `--spin`
  (`cubic-bezier(.33, 0, .2, 1)`), each page setting them by formula, measured against a full-width container
  (`container-type: inline-size` on `body`, so `100cqw` excludes a scrollbar):
  - wrap width `W = min(100cqw - 2 * var(--gutter), 82rem)`, wrap left `L = (100cqw - W) / 2`;
  - Home (EN): stage columns 5fr : 6fr with `column-gap: var(--gutter)`: column 2 starts at
    `L + (W - gutter) * 5/11 + gutter` and is `(W - gutter) * 6/11` wide; the mark's height is
    `min(66svh, colwidth * 548/520)`, centred in the column; its top is `50svh - h/2` (the sticky position) measured
    from the top of the page, since the page is at scroll 0 after a change;
  - Home (LV): the same with 2fr : 1fr;
  - inner pages: three equal columns, the mark right-aligned in column 3 (`left = L + W - h * 520/548`),
    `h = min(36svh, 18rem)`, top = the page head's top (`var(--hd)` plus the page head's top padding).
- The page heads of Services, Open source and Company align the mark to the top (`align-items: start` for the
  figure), so the formula's top is exact.
- Hand-over: at both ends `.mk` must cover the resting mark within 1 px; tests check this at every tested size.
- Privacy has no mark: in a change to or from Privacy, `.mk` stays at the other page's place and fades
  (`opacity` follows `t`) while it spins.
- The solid during the change (sides, back, cast shadow) is v4's, driven by `--t` instead of keyframes:
  `rotate3d(1, -1, 0, t * 360deg)` (cyan `-360deg`), sides and back shown by `--m`, the drawn sides and drawn shadow
  hidden by `--m`. The face SVGs are wrapped in a `<div class="mark__face">` (generated by `tools/gen_mark.py`),
  because Firefox paints an SVG that is itself part of a 3D scene at the wrong place.

### Phones and upright screens: spin in place

- No `.mk`. The arriving page's own mark (Home on phones; Home and the inner pages on upright tablets from 48rem)
  turns once in place by the same `--t`, as a solid. Pages without a mark there get the content fade only.

### Content

- The arriving section fades in over .2 s (`@starting-style { opacity: 0 }`); the section being left disappears at
  once.

## 3. v3

- The document structure of section 1.
- Page change: the arriving section fades in over .2 s; the mark appears in its place. No `@property` state, no
  `.mk`. The inner-page mark stays centred as today.

## 4. Testing

- `python3 v3/build.py --strict` and `python3 v4/build.py --strict` (with the fragment check). v1 and v2 still
  build.
- A Playwright check (kept in the repository as a tool, like `gen_mark.py`, or in the scratchpad if the owner prefers)
  that runs in Firefox and Chromium at 1440x900, 1920x1080, 1280x720, 1024x768, 820x1180 (upright) and 390x844
  (phone), and checks:
  - each change (Home to Services, Services to Company, Company to Privacy, Back, the logo) runs once; travel only on
    wide landscape screens, spin in place on the others (v4); content fade only (v3);
  - no motion on load, reload, a new tab at `#company`, a link to `#development`, or with reduced motion;
  - hand-over: at the end of a travel `.mk` and the resting mark differ by at most 1 px in x, y and size;
  - the right section, header underline and language link show for every target, in both languages;
  - print shows only the open section.
- `node --test 'infra/functions/*.test.mjs'` still passes; `terraform plan` shows only the site's objects changing
  (page folders removed, `index.html` and assets changed).

## Out of scope

- v1 and v2 stay multi-page.
- Redirects for old URLs.
- Per-page titles or descriptions.
- Any change to the content, the colours or the type.

## Risks

- The formulas copy the layout: a later change to the stage or page-head grid must update them. The hand-over test
  catches a mismatch.
- The 1 s load gate is a timing assumption about when Firefox applies `:target`; measured at well under .3 s.
- Safari is still untested.
