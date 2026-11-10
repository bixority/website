# Version 3, "Keynote": design notes

Version 3 redesigns the whole site, English at `/` and Latvian at `/lv/`; each language is one document (see [The document](#the-document)). Versions 1 and 2 are kept as the git tags `v1` and `v2`. This file records the principles, the decisions the owner made, the token system, the components for inner pages, and what is still open.

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
10. **One reveal, then stillness.** The only animations on the whole site are the home reveal and the .2 s fade of a page change (both below). Reduced motion gives a static, full-colour, closed mark and pages that change without a fade.
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
- **One set of mark defs.** `mark-defs.html` (gradients, filter, outlines) is placed once at the top of `<body>` in a zero-size `<svg class="mark-defs">`, positioned absolutely and never `display: none`, which browsers do not paint gradients inside.
- **No JavaScript**, except the JSON-LD data in the head.
- **Page change.** The arriving section fades in over .2 s (`@starting-style`, only with `prefers-reduced-motion: no-preference`); the section being left disappears at once. Nothing else moves: `check_pages.py` checks that during a change no element other than the `.pg` sections has a running animation or transition (the home reveal runs on a scroll timeline and is not counted). Print shows the open page only.

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
- **The object on inner pages** (`.page-head--obj`). Services, Open source and Company show the same mark, closed and lit as the home ends, with no page-specific variants. It sits in column 3 of the page head, still (`.still` switches the home reveal off), from 48rem only; phones and print leave it out. The privacy notice and the 404 keep their own heads.
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
- **Safari was not tested** (no WebKit on the build machine). Its fail-safe path is verified: without `animation-timeline` support the mark is static and in full colour.
- **Opened from disk** (`file://`) the language link, which points at a folder (`lv/#services`), shows a folder listing. The deployed site is not affected.
- **Phones held sideways** (844 by 390) use the pinned stage; the page there is long and the Latvian H1 is 1.27 times the statement size, just under the 1.3 aim.
- **The Latvian mark** is about a quarter smaller than the English one on landscape screens (the cost of the 2 : 1 split that keeps each H1 sentence on one line).

## Decided after the build (2026-11-07)

- The v2 block "Talk to us / Write to us about the system you run or the one you want to build." (LV: "Sazinieties ar mums") stays removed from Services, Open source and Company. The footer ask "Write to us." with the email replaces it on every page.
- The Services sections keep the v2 order (DevOps and SRE, Software development, Consulting, then how an engagement starts), with the main offer first. The home page's Design / Build / Run order is not mirrored there.
- The site names services in both Rust and Python, and TypeScript for web front ends. JavaScript, Node.js, AWS CDK and CloudFormation are not named, in any version (v1, v2 and v3). The home Build column now reads "Software development: services in Rust and Python, web front ends in TypeScript."
- The Company page has a section "Who we answer to" (LV "Kam mēs esam atbildīgi", `#independence`) between "Our principle" and "Company details", in all three versions: the company is owned by its founder alone, with no investors, subsidies or grants, loans or parent group. The owner confirmed each fact; the text claims nothing about how the company is funded beyond them.
- "Our principle" on the Company page has a fourth item, "We question the plan" (LV "Mēs apšaubām plānu"), in all three versions: we ask awkward questions early, and when a plan looks risky or wrong we say so directly, explain why and propose an alternative. The owner chose the Company principle over a paragraph in the Services engagement section. Four parts fill the two-column grid two by two. The v1 and v2 home pages list it as well, under "Quality, in practice"; the v3 home has no principle list.
