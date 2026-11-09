# Version 2: research notes

Source: the Awwwards technology category and the latest Sites of the Day,
reviewed on 2026-11-06/07. For each site the live page was opened in Firefox,
scrolled with real wheel events, and captured as seven viewport frames
(1440×900). The fonts each site loads were read from its HTML and CSS.

## Sites reviewed

**Award winners (Site of the Day and Developer Award), as benchmarks for craft.**
Grail, DeepBook, MECHA, Heron AI, Neutomni, Grids (Obys), FORMAT (Obys),
Signal-A, twks, Emotion Agency, ViV.

**Technology companies close to Bixority.** These cover security, infrastructure,
developer tools, engineering studios and deep tech.

- Ethiack, Ultra Red, Maze, Darkmoon, Orizon
- IEQ Technology, Vanguard Initiative, Nualt, Potadot, MacMillan Studio, Crox
- NODDAL, Dalco, Seas Geosciences, Endurosat, Idealworks
- Superscript, Zeropact, Motorq, Zenarate, GrowthBook, Key, Giga
- Krea 3, Mosaic, Pulse Bridge, The Content Architecture, Polpharma Biologics,
  premotio

## What recurs

**Typography.**

- Neo-grotesque sans plus a monospace companion is the norm:
  - Neue Haas Grotesk with GT America Mono (Signal-A);
  - Suisse Intl with Suisse Mono (Krea);
  - Geist with Geist Mono (Vanguard, Nualt, Mosaic, Content Architecture);
  - Neue Montreal with IBM Plex Mono (Emotion);
  - GT Standard (twks), Saans (Maze), Belfast Grotesk (NODDAL).
- Pixel or raster faces appear as accents on security and developer sites:
  Ethiack, Ultra Red, Nualt, Mosaic.
- Serif display faces are used for editorial weight: MECHA, Grail, Signal-A,
  Key and Zenarate.
- Monospace carries metadata, such as coordinates, local time, version
  numbers, file names and section indices.

**Structure.**

- Hairline-ruled grids and frames, with crosshair or registration marks at the
  intersections: Heron AI, Ethiack, Superscript and Vanguard.
- Spec-sheet tables instead of marketing copy:
  - DeepBook: custody model, settlement, audits, live since;
  - MECHA: investment metrics;
  - IEQ: service coverage, with ACTIVE status rows.
- Numbered indices with a progress line that tracks the reader (MECHA), and
  chapter labels in the corners (Grail).
- The process shown as a real sequence:
  - Neutomni: a staircase of rising columns;
  - Nualt: boxes joined by connector lines;
  - Motorq: "Connect. Understand. Act.";
  - IEQ: an orbit of four services around the logo.
- Open source shown as code, not as cards. Nualt draws its GitHub organisation
  as a tree, with every repository branching off the trunk.
- A giant wordmark closes the footer: Signal-A, ViV, twks.
- Small "live" details in the header: local time and city (Neutomni,
  Signal-A), or an "open for work" status.

**Motion.**

- Scroll-pinned statements that change in place: Ethiack, Grail.
- Numbers that scramble or count into place, and a typing caret on headings:
  DeepBook.
- A floating pill bar at the bottom for navigation or the call to action:
  Grail, Krea, Ethiack.
- Each site has one signature animation. The rest of the page stays still.

**Colour.**

- One saturated brand colour on a neutral ground: DeepBook blue, Neutomni red,
  Nualt blue, Ultra Red pink, Heron's single orange sun.
- Dark "infrastructure" sites use navy rather than black: Vanguard, Maze,
  Darkmoon, Seas.

## What does not fit Bixority

- Cinematic 3D and WebGL scenes (NODDAL, Seas, Darkmoon). They would need
  assets we don't have, and they put the spectacle before the facts. They
  also add weight that a small, careful engineering company shouldn't carry.
- Pixel and dot-matrix motifs. They are fashionable, but they aren't part of
  our brand: the logo is built from straight strokes and circular arcs, not
  pixels.
- Numbers we can't back up. Several sites lead with a row of statistics
  (Ultra Red, Motorq, Krea); our rule is no unverified numbers.
- Gated intros ("enter with audio"), custom cursors and scroll-jacking that
  takes over the scroll bar.

## Direction for version 2: the drawing set

**Concept.** The site reads as an engineering drawing package. This is grounded
in something only Bixority has: the logo is an exact geometric construction.
The chevrons have a 60° apex, outer edges at 15° and 75°, a band thickness
*t*, and a cyan copy offset by 2*t* along the 45° axis. Precision is the
message ("because quality matters"), so the design shows the construction
instead of claiming precision.

**Signature moment (the only decorative animation).** In the home page hero
the mark's real construction drawing draws itself in, in this order:

1. the 45° axis;
2. the extended 15° and 75° edges;
3. the cut line;
4. the 60° angle arc;
5. the *t* and 2*t* dimensions.

Then the cyan and lime chevrons fill in, and the construction lines fade to a
faint blueprint. With reduced motion, the finished drawing is shown at once.

**Borrowed, adapted.**

- A visible column grid with crosshair registration marks (Crox, Heron,
  Superscript).
- A bordered-cell header with the full logo, the navigation, local time in
  Rīga and the language switch (Crox, Neutomni).
- Facts used as ornament: Rīga coordinates and "est. 2010" (Crox, Signal-A).
- How we work as a scroll-synced sequence (Giga, Zenarate). Design → build →
  run stays in view, and a pinned panel shows what each step produces: a
  design note with its risks, a pipeline with tests, review and a signed
  release, and a run log. It shows our practice, not invented metrics.
- Open source as a repository tree branching off `bixority` (Nualt).
- Company details as a spec sheet (DeepBook, MECHA).
- The footer as a drawing title block, one compact band: the full logo with
  its tagline, the company and address, registration and VAT numbers, and
  contact.
- A sticky section index with progress on long pages (Orizon, MECHA).

**Type.** Geist and Geist Mono, self-hosted with Latin Extended for Latvian.
Monospace only carries real data: coordinates, time, sheet numbers,
dimensions, repository names.

**Colour.**

- The header, hero and footer are navy blueprint (`#001b35`), as in version 1.
  The logo keeps its dark variant on its own colour.
- Content follows the visitor's light or dark preference: drafting paper with
  navy ink, or deep navy.
- Cyan is for construction lines and links. Lime stays rare: the mark,
  "approved" ticks and the primary button fill.

**Kept from version 1.**

- All copy, both languages and every page.
- The static build with fingerprinting, the relative URLs that let `dist/`
  open from disk, the absence of cookies and third-party requests, and WCAG
  AA contrast.
- The rule that the logo is always shown in full with its tagline.
