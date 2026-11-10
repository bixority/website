# Version 4: design notes

Version 4 is version 3, "Keynote", built as one document per language, plus the page change: the mark spins as two solids while the next page opens (see [The document](#the-document) and [The page change](#the-page-change)). Everything else is as in version 3, which redesigned the whole site, English at `/` and Latvian at `/lv/`. Versions 1 and 2 are kept as the git tags `v1` and `v2`. This file records the principles, the decisions the owner made, the token system, the components for inner pages, and what is still open.

## Principles

The design follows Steve Jobs's design principles, taken from primary sources where they could be checked (never from apple.com). Each rule below has a check.

1. **One sentence carries the page.** Each page opens with one declarative H1. The home H1 is "We build it. We run it." No eyebrows, kickers or section numbers.
2. **Focus means saying no.** The home has few sections; every list is short, except real inventories such as the repositories.
3. **Design is how it works.** The page is a readable document first: the outline is h1, h2, h3 with no skipped levels, every link and fact works with CSS and JavaScript off.
4. **Start from the reader's question.** What you do, how you work, whether the company is real and reachable. The email address is in the footer of every page, and the registration number is one click away.
5. **Typography is the product.** Geist for text, Geist Mono only for repository names. At most six font sizes on the whole site. `text-wrap: balance` on headings, a 55 to 75 character measure for text, curly quotes in copy.
6. **The back of the fence.** The parts nobody looks at are as careful as the front: print, the 404 page, Latvian, focus rings, alt text.
7. **Simplicity by depth, not by hiding.** Cut decoration, never the facts a buyer needs.
8. **The presentation is evidence.** Page weight of 150 KB or less including fonts, no cookies, no analytics, no third-party requests, no console errors.
9. **Honest about being high-tech.** No costumes of tools: no fake terminals, pipelines or file names, and no coordinates or "est." used as decoration.
10. **One reveal, one page change, then stillness.** The site has two motions and no more: the home reveal and the page change (both below). The page change is the owner's decision of 2026-11-07 and amends the earlier "one reveal" rule; nothing else on a page moves. Reduced motion gives a static, full-colour, closed mark, and pages that change without motion.
11. **Plain words.** Concrete nouns (Kubernetes, PostgreSQL, Rust), short sentences, no hype or AI wording, no client names, no unverified numbers.
12. **Iconic, few elements.** Navy or aluminium, the mark, Geist. Lime appears only in the logo and the mark; cyan only as a UI accent.
13. **The whole widget.** English and Latvian, dark and light, print and the 404 page get the same care.
14. **Unobtrusive and long-lasting.** No glass blur, gradient text, marquees, custom cursors, card grids or buttons. The header is not fixed. The footer is at most 160 px tall at 1440 px wide.

## Owner decisions

1. Home copy is approved and used verbatim in English and Latvian. H1: "We build it. We run it."
2. Both themes follow the system preference, with no toggle. Dark, the navy stage, is the default when there is no preference; light is the "aluminium room" (ground `#e3e6e9`). The page declares `<meta name="color-scheme" content="dark light">` and two `theme-color` metas (`#001b35` for dark, `#e3e6e9` for light), each with a `prefers-color-scheme` media query.
3. Logo: `brand/bixority-logo-dark-tight.svg` on dark grounds, `brand/bixority-logo-ink-tight.svg` (navy wordmark, "quality" in deep cyan) on light grounds and in print. Wherever the logo appears it is the full logo with its tagline "because quality matters", in its original proportion and place. It is never cropped, stripped, recoloured or separated from the tagline. The mark alone appears only as an illustration (the 3D mark).
4. On phones the Design / Build / Run word column is sized to the word "Design", not to a percentage.
5. Inner pages (Services, Open source, Company, Privacy, 404) keep their v2 copy, in both languages. Only markup and styling changed. The Riga clock, the section index with its progress bar, the copy buttons, the repository tree ornaments, label eyebrows, figure captions, guide lines, crosshairs and coordinates are removed.

Hard rules: no cookies, no analytics, no third-party requests (fonts and images are self-hosted; outbound links are fine). Contact is `info@bixority.com` only: no phone, no founders section. URLs are relative, so `dist/` also works from `file://`, except that the language link, which points at a folder, shows a folder listing there.

## Token system

All of it is in `src/assets/css/site.css`; the comment block at the top of that file is the reference for page authors.

- **Roles, dark (bare `:root`, the default):** `--ground #001b35`, `--ink #eef2f6`, `--quiet #8aa0b6`, `--accent #00ccff` (hover underline, focus ring), `--line #0097c2` (resting link underline).
- **Roles, light (`@media (prefers-color-scheme: light)`):** `--ground #e3e6e9`, `--ink #001b35`, `--quiet #4a5664`, `--accent #006b85`, `--line #006b85`.
- **The mark as an object:** `--shade` and `--shade-o` (its soft shadow), `--off` (brightness of the unlit, grey chevrons).
- **Which logo file:** `--logo-dark` and `--logo-light` are `block` or `none`; the layout holds both images and the tokens choose one. Print forces the ink logo.
- **Type scale:** `--t-small .875rem`, `--t-base 1rem`, `--t-lead clamp(1.125rem, 1rem + .45vw, 1.375rem)`, `--t-ask clamp(2rem, 1.2rem + 1.4vw, 2.5rem)`, `--t-say clamp(2.125rem, 1.1rem + 3.1vw, 4rem)`; the home H1 is a size of its own (up to 9.5rem). That makes six tokens. Where a word has to fit its column, container-query caps take the size slightly below its token (`.col h3` and `.proof h2` at 15cqi, `.ft__ask` at 9.5cqi, `.names`, and the Latvian H1), so the measured sizes on a page differ by a few pixels from the tokens (up to 8 distinct computed sizes at 1440). These fitted sizes come from the approved prototype; making them exact is an open owner decision.
- **Space and layout:** `--gutter clamp(1rem, 4vw, 4rem)`, `--hd` (header height), `--mark-h` (height of the mark); `.wrap` is the 82rem content column.
- **Weights:** 400 and 600 for text; the static 250, 500 and 800 weights only on the words Design, Build and Run. The fonts carry the full 100 to 900 axis.
- **Contrast:** all UI text passes WCAG AA in both themes (ink on ground 15.45:1 dark and 13.87:1 light; quiet 6.44:1 and 5.97:1). The focus ring is 3 px with a 4 px offset and is never clipped. `prefers-contrast: more` makes the quiet colour equal to ink.

### The home reveal

The mark is two chevrons (`.part--c`, `.part--l`). Scrolling through the problem statement moves them apart and takes the colour out (a split of 46 units, brightness `--off`), then closes them and brings the colour back. It is CSS only, driven by a scroll timeline (`animation-timeline: view()`), and only runs when motion is allowed and the browser supports scroll timelines. In every other case the mark is closed and in full colour. `tools/gen_mark.py` generates the mark's markup; the 404 page shows the split, grey state without animation by wrapping the mark in `.apart`.

### The document

Each language is one HTML document: `/` and `/lv/`. Its pages are sections, in the order Home, Services, Open source, Company, Privacy: `<section class="pg pg--<key>">`, with `id="<key>"` on every page except Home. A page address is a fragment (`/#services`, `/lv/#company`); the sitemap lists the two documents only, and the title, description and canonical URL of a document are the home page's. There are no redirects and no per-page files.

- **Which page shows.** CSS only: `.pg` is `display: none`; Home shows unless a `.pg[id]` (or something inside one) is the `:target`; each other page shows by `:root:has(#<key>:target, #<key> :target)`. A link to a sub-section (`#development`) therefore shows Services and scrolls to the sub-section. `.pg[id]` has `scroll-margin-top: 100svh`, so following a page link scrolls to the top of the document.
- **Header.** The nav links carry `hd__link--<key>`; the open page's link has the 2 px accent underline by the same `:has` selectors (Home and Privacy have none). There is one language link per page (`hd__lang--<key>`), each to the same page in the other language; only the open page's shows.
- **Unique ids.** Ids repeated across pages (`page-title`, `principle`) are prefixed with the page key on the pages other than Home (`services-page-title`), together with their `aria-labelledby` and `href="#…"` references. The build fails on any repeated id and on any `href="#id"` without its id in the same document.
- **One set of mark defs.** The mark's gradients, filter and outlines are not in each mark: `mark-defs.html` is placed once at the top of `<body>` in a zero-size `<svg class="mark-defs">`, positioned absolutely and never `display: none`, which browsers do not paint gradients inside. Each face SVG is wrapped in a `div.mark__face` (Firefox paints an SVG that is itself part of a 3D scene at the wrong place).
- **No JavaScript.** There is no script on the page except the JSON-LD data.
- **Content.** The arriving section fades in over .2 s (`@starting-style`, under `prefers-reduced-motion: no-preference`); the section being left disappears at once. Print shows the open page only.

### The page change

The owner asked for a single-page feel with a 3D animation of the mark when the page changes (2026-11-07). The first build used cross-document view transitions between separate pages; since 2026-11-10 the pages are sections of one document and the motion is CSS on registered custom properties, which also works in Firefox. The motion itself is the owner's design, tuned over several rounds of video: both chevrons spin around the arrow's own pointing axis, in opposite directions, and come back to where they started.

- **State, on `:root`.** `--n` is the open page's number (Home 0, Services 1, Open source 2, Company 3, Privacy 4). `--cur` (a registered number) takes `--n` and transitions over `--spin` (.7 s, `cubic-bezier(.45, 0, .2, 1)`); `--old` takes `--n` with a 0 s transition delayed by `--spin`, so it keeps the old page's number for the whole change. Progress is `--t = --ready * (cur - old) / (n - old + .0001)`: 0 at rest, 0 to 1 in a change. `--m` is 1 while a change runs and 0 at rest. Transitions do not run on a page's first style, so loading moves nothing.
- **The load gate.** Firefox matches `:target` only after the first style, so a reload or a link to `#company` would look like a change from Home. `--ready` (a registered number) is 0 for the first second after load (`animation: ready 0s 1s both`, longer than `--spin`) and multiplies `--t` and the mark's drawn position. A click inside that first second changes the page without motion. (It multiplies values: a transition duration that depends on `--ready` is not read in Chromium.)
- **The solid.** Each chevron is a closed solid 30 drawing units deep: its face, a side on each edge and a back, in the drawn sides' darker tones. It turns by `rotate3d(1, -1, 0, t * 360deg)` (the cyan one `-360deg`) about the mark's pointing diagonal. No perspective, so shape and thickness never change; the shadow stays and falls naturally. The solids are seen from a little above, as the drawing shows them, so at 0 and 360 degrees the real solid covers exactly what the drawn mark does and there is no jump at either end. The drawn sides and shadow give way to the solid's by `--m`. The sides' positions come from `python3 tools/gen_mark.py --css`.
- **Wide landscape screens** (`min-width: 48rem` and landscape): one extra mark, `.mk` (first child of `<main>`, `aria-hidden`), travels from the old page's mark to the new one's in `--spin` (`cubic-bezier(.33, 0, .2, 1)`) while it spins. Its left, top, width and height are registered lengths (`--mx`, `--my`, `--mw`, `--mh`) set by formulas of the layout against `<main>`'s width (`100cqw`) and the viewport height: the `.wrap` width and left edge; Home's stage column 2 (5fr : 6fr, Latvian 2fr : 1fr) with the mark 66svh high and centred in it, pinned at the middle of the screen where scroll timelines exist; on Services, Open source and Company, column 3 of the page head, right-aligned, at the head's top, `min(36svh, 18rem)` high. The pages' own marks give way to `.mk` while a change runs (`opacity: 1 - --m`) and are what is seen at rest. At both ends `.mk` covers the resting mark within 1 px; `check_pages.py` tests this at 1440x900 (English and Latvian), 1920x1080, 1280x720 and 1024x768, and after a resize.
- **Phones and upright screens:** no `.mk`. The arriving page's own mark turns in place by the same `--t` (Home on phones; Home and the inner pages on upright tablets from 48rem). Pages without a mark there get the content fade only.
- **Privacy has no mark.** In a change to Privacy `.mk` stays at the old page's place and fades out while it spins; in a change from Privacy it is at the new page's place from the start and fades in.
- **Reduced motion and print.** All transitions and animations are inside `@media screen and (prefers-reduced-motion: no-preference)`; otherwise `--cur` follows `--n` at once and nothing moves. Print has no `.mk` and no mark. The 404's split, grey mark takes no part.
- **At rest nothing changes.** `.mk` is invisible, the solids' sides and back are hidden, and the mark is drawn as before. (On phones and upright screens the page's own mark carries the solid's constant at-rest transform, which shifts a few edge pixels by at most 20 levels in Chromium.) The mechanism and every value are documented at the top of `site.css`.

## Inner-page components

Documented, with markup, at the top of `site.css`: `.page-head`, `.beat` (with `.intro`), `.parts` and `.part`, `.list`, `.facts`, `.repos`, `.prose`, `.beat--legal`, `.links`. Page-specific CSS goes in `src/assets/css/page-<name>.css` (today only `page-open-source.css`); the build bundles every stylesheet into one file. Pages stay within the existing type sizes and colour roles. The home page uses its own class names (`.stage`, `.scene`, `.work`, `.proof`, `.names`) so that the component names above stay free.

### One composition with the home

The inner pages use the home's grid. From 48rem (where the home `.cols` becomes three columns) a `.beat` is a grid on the same three tracks and the same gap, so columns 2 and 3 start exactly where Build and Run start (measured: x = 520.5 and 977.1 at 1440; 368.6 and 696.3 at 1024; 276.5 at 768, where the content spans both). Column 1 holds the H2 and an optional intro (the first paragraph, styled like `.proof__text`); columns 2 and 3 hold the content as one element: `.parts` (two columns from 64rem), `.prose`, `.list`, `.facts` or `.repos`. Below 48rem everything is one column. Between 48rem and 64rem the parts, facts and repositories stay one column on columns 2-3, because a third of the row is too narrow for text at the lead size.

- **Type.** Running text is `--t-lead` in the quiet colour, as `.col p` on the home. h3 and repository names are `--t-lead` in ink; the H2 stays `--t-ask`. `--t-small` is only for meta (licence and links line, `.facts dt`, the "last updated" line). No font size was added. Two fitted sizes, as on the home: the H2 and the repository name are capped by container query so that the longest word or name fits its column (the same device as `.names`).
- **Parts.** Subsections are `div.part` inside `div.parts`, with generous row gaps and no rules, cards or boxes.
- **Privacy** is a legal margin: each of the seven clauses is its own `section.beat--legal` with the H2 in column 1 and the text at a 62ch measure in columns 2-3; the "last updated" line sits at the top of columns 2-3.
- **Compounds** that must not break at a line end (`client-side`, `6(1)(f)`, `LV-1039`, `E-pastu`) are wrapped in `.nw`.
- **Current page.** The open page's `.hd__link--<key>` has a 2 px underline in `--accent` (9.2:1 on the navy, 4.9:1 on the aluminium).
- **Print.** Inner pages print as one column at the print body size; headings keep with what follows them (`break-after: avoid` on h2, intro and h3).
- **The object on inner pages** (`.page-head--obj`). Services, Open source and Company show the same mark, closed and lit as the home ends, with no page-specific variants. It sits in column 3 of the page head, aligned to the head's top, still (`.still` switches the home reveal off), from 48rem only; phones and print leave it out. The privacy notice and the 404 keep their own heads.
- **One statement per long page** (`.beat--say`). An existing intro is set at `--t-ask`, weight 400, in ink, over columns 2-3 on the H2's cap line: "From the first design document to maintenance years later, by the same team." (Services) and "Our clients and our own standards, nobody else." (Company), and their Latvian counterparts. On phones it stays at the lead size, in ink, because at the H2's size it read as a second heading. On paper it is the plain intro again. The owner chose this direction (B, "the object on the stage") over line diagrams and glyphs on 2026-11-07, keeping the statement and the extra air, and without the thin connecting lines of the other prototypes, which looked cheap.
- **Air.** From 48rem a beat has `clamp(2.75rem, 10vh, 6rem)` above and below (was `clamp(2.25rem, 7vh, 4.5rem)`); the legal beats keep theirs.

Choice made for the hierarchy: the page H1 is at `--t-say` and the `.beat` H2 one step below at `--t-ask`, so a page never has an H1 and H2 of equal size.

## Open items

- **Latvian copy for a native speaker.** The home copy is approved, but these phrases should be read by a native speaker:
  - "katra problēma ir kāda cita atbildībā" (from approved v2 wording);
  - "Jo kvalitātei ir nozīme: pēc šā principa mūsu dibinātājs ir strādājis visu karjeru.";
  - "Sistēmas, kas veidotas, lai atkoptos.";
  - "Reģ. Nr." and "PVN Nr." in the footer;
  - "Atvērts pēc noklusējuma." reads like a software-settings phrase;
  - "Katra izmaiņa tiek testēta un pārskatīta": "izmaiņa" is singular, "izmaiņas" is the usual plural form;
  - "laidienu inženierija" is a rare term for release engineering;
  - "Kam mēs esam atbildīgi" (Company): the section text calls the company "tās dibinātājam" (feminine, as for "sabiedrība") and then "uzņēmumam ... tas" (masculine); check that the mix reads naturally;
  - "Rust un Python servisi, TypeScript tīmeklim" (home; kept short so the Latvian home still prints on one page). Software services are "servisi" (owner, 2026-11-10), also "Rust servisiem" and "Python servisiem" on Services; the company's services stay "pakalpojumi";
  - "Mēs apšaubām plānu" and "problēmas vislētāk novērst, pirms kaut kas ir uzbūvēts" (Company, fourth principle).
- **Safari was not tested** (no WebKit on the build machine). Its fail-safe path is verified: without `animation-timeline` support the mark is static and in full colour. The page change (registered properties, `:has()`, `@starting-style`, 3D transforms) is checked in Firefox and Chromium only; Safari is untested.
- **A click during a running change** starts the next one from where the mark is (its place is continuous), and the page always ends correct, but the spin angle can jump once, because progress is measured from the first old page's number.
- **Opened from disk** (`file://`) the language link, which points at a folder (`lv/#services`), shows a folder listing. The deployed site is not affected.
- **Phones held sideways** (844 by 390) use the pinned stage; the page there is long and the Latvian H1 is 1.27 times the statement size, just under the 1.3 aim.
- **The Latvian mark** is about a quarter smaller than the English one on landscape screens (the cost of the 2 : 1 split that keeps each H1 sentence on one line).

## Decided after the build (2026-11-07)

- The v2 block "Talk to us / Write to us about the system you run or the one you want to build." (LV: "Sazinieties ar mums") stays removed from Services, Open source and Company. The footer ask "Write to us." with the email replaces it on every page.
- The Services sections keep the v2 order (DevOps and SRE, Software development, Consulting, then how an engagement starts), with the main offer first. The home page's Design / Build / Run order is not mirrored there.
- The site names services in both Rust and Python, and TypeScript for web front ends. JavaScript, Node.js, AWS CDK and CloudFormation are not named, in any version (v1, v2 and v3). The home Build column now reads "Software development: services in Rust and Python, web front ends in TypeScript."
- The Company page has a section "Who we answer to" (LV "Kam mēs esam atbildīgi", `#independence`) between "Our principle" and "Company details", in all three versions: the company is owned by its founder alone, with no investors, subsidies or grants, loans or parent group. The owner confirmed each fact; the text claims nothing about how the company is funded beyond them.
- "Our principle" on the Company page has a fourth item, "We question the plan" (LV "Mēs apšaubām plānu"), in all three versions: we ask awkward questions early, and when a plan looks risky or wrong we say so directly, explain why and propose an alternative. The owner chose the Company principle over a paragraph in the Services engagement section. Four parts fill the two-column grid two by two. The v1 and v2 home pages list it as well, under "Quality, in practice"; the v3 home has no principle list.
- Single document per language (2026-11-10): v3 and v4 build `/` and `/lv/` only, with the pages as sections (see "The document" above). A page change animates the mark: the two chevrons spin as solids around their pointing axis, in opposite directions (see "The page change" above, and principle 10).
