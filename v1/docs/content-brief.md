# Bixority website: content brief and structure

Status: approved on 2026-11-06; all pages are built in English and Latvian.

Decided on 2026-11-06:

- **Structure:** several pages, with English at `/` and Latvian under `/lv/`.
- **Build:** a tiny build script, with plain static output.
- **Address:** `www.bixority.com`; the bare domain redirects to it.
- **Development stacks named on the site:** services in Rust and Python,
  web front ends in TypeScript. JavaScript, Node.js, AWS CDK and
  CloudFormation are not named (owner decision, 2026-11-07).

## 1. Goal

A brand-presence site for Bixority SIA. It has no sales funnel, no tracking and
no forms. A visitor should be able to answer three questions within a few
seconds of landing:

- What does Bixority do?
- How does it work with clients?
- How do I reach it, and is it a real, registered company?

Readers:

- **Enterprise buyers and CTOs.** They want scope, working method and company
  details.
- **Developers.** They want to see the code: the open-source tools and their
  licences.

## 2. Positioning

**Core message: full-cycle ownership.** One small, senior team designs, builds
and runs the system, and stays accountable for it in production.

**Slogan: "Because quality matters."** This is the founder's lifelong
principle, and it applies to every layer of IT: code, infrastructure,
operations and communication. It is the site's through-line, not decoration.

Pillars, taken from the interview:

| Pillar                | What it means in practice                                              |
|-----------------------|------------------------------------------------------------------------|
| Engineering quality   | Every change is tested and reviewed before it ships.                   |
| Openness              | We publish our tools as open source; the docs say what they do and don't do. |
| Reliability           | Systems are built to recover cleanly; production should be uneventful. |
| Full-cycle ownership  | Design, build, run: one team, no hand-offs between vendors.            |

Home page hero (draft, English):

> **H1:** Software and infrastructure, designed, built and run by one team.
> **Sub:** Bixority has been an engineering company in Riga since 2010, working
> across DevOps, SRE and software development. Because quality matters.

Alternative H1s:

- "We build it. We run it. We answer for it."
- "Full-cycle engineering, from architecture to on-call."

## 3. Voice and content rules

- **Tone:** technical and direct. Use short sentences and concrete nouns, such
  as Kubernetes, Terraform or PostgreSQL, instead of adjectives.
- **Never:** client names, numbers we cannot verify (uptime, savings, speed-ups),
  certifications we do not hold, or AI and hype wording ("cutting-edge",
  "world-class", "passionate", "AI-powered", "synergy").
- **No people section yet.** Use "we" for the team.
- **Contact:** email only, olegs.korsaks@bixority.com. No phone number.

## 4. Sitemap

English lives at `/` and Latvian mirrors it under `/lv/`. Every page links to
its counterpart in the other language.

| Page        | Path            | Contents |
|-------------|-----------------|----------|
| Home        | `/`             | Hero; *What we do* (three cards: DevOps & SRE, software development, open-source tools); *How we work* (design → build → run, and what the client gets at each step); *Principles* (quality, openness, reliability); contact strip with the email |
| Services    | `/services/`    | **DevOps & SRE:** Kubernetes (on-prem, EKS, AKS, GKE), infrastructure as code, CI/CD and release engineering, observability and incident response, database operations (PostgreSQL migrations, backups, maintenance). **Software development:** architecture, implementation, tests and reviews, delivery, maintenance; services in Rust and Python, web front ends in TypeScript. **How an engagement starts:** email → review of the current state → written proposal |
| Open source | `/open-source/` | A card for each public repository (name, purpose, licence, GitHub and Codeberg links). object-storage-client is featured and links to its own product page |
| Company     | `/company/`     | About (founded 2010 in Riga, small senior team, what "because quality matters" means, as four principles: tested and reviewed, open by default, built to recover, and "We question the plan", added by the owner on 2026-11-07: we ask awkward questions early and say plainly when a plan looks risky or wrong, with an alternative); company details (SIA "Bixority", reg. no. 40103335376, VAT LV40103335376, Ropažu iela 14A - 27, Rīga, LV-1039); "Who we answer to" (owned by the founder alone; no investors, subsidies or grants, loans or parent group, confirmed by the owner on 2026-11-07); contact email |
| Privacy     | `/privacy/`     | Short notice: no cookies, no analytics, no forms. It explains what the hosting logs (CloudFront request logs) and why, names the controller and lists GDPR rights |
| Not found   | `/404.html`     | A short message with links to the main pages |

- **Header:** logo, navigation (Services, Open source, Company), EN/LV switch.
- **Footer:** company details on one line, email, privacy link, © year.

### Public repositories (all on GitHub and Codeberg)

| Repository                 | Language | Licence   | Purpose (to be rewritten from each README) |
|----------------------------|----------|-----------|----------------------------------------------|
| object-storage-client      | Rust     | GPL-3.0   | One client and CLI/GUI for S3, GCS, Azure Blob and local storage |
| object-storage-maintenance | Rust     | GPL-3.0   | Object storage maintenance tool |
| pg-migrate                 | Rust     | GPL-3.0   | PostgreSQL migration tool |
| pg-maintenance             | Rust     | GPL-3.0   | PostgreSQL maintenance tool |
| amqp-bridge                | Rust     | AGPL-3.0  | Re-transmits AMQP messages between servers |
| email-sender               | Rust     | GPL-3.0   | Sends email over SMTP from RabbitMQ messages |
| api-client                 | Rust     | GPL-3.0   | API client |
| esteria-api-client         | Rust     | GPL-3.0   | Client for the Esteria API |

## 5. Technical approach

- **Static by design.** Use HTML5, one CSS file and a small amount of JS that
  only enhances the page (mobile menu, copy-email button). Every page works
  without JS.
- **Tiny build step.**
  - Each page is written once as a template, with its English and Latvian
    text kept separately.
  - A dependency-free Python script (standard library only) combines them into
    the published files. It adds the shared header, footer, language switch
    and the head tags each page needs.
  - The output in `dist/` is plain static HTML, CSS and JS, ready to upload.
- **Address.** The site lives at `https://www.bixority.com/`, and
  `bixority.com` redirects there. Canonical, Open Graph and sitemap URLs all
  use the www address.
- **Two themes.** Follow the system light/dark preference. A `<picture>`
  element swaps between the light and dark logo SVGs, which share one size.
- **Accessibility: WCAG 2.2 AA.**
  - Use semantic landmarks, a skip link and visible focus styles, and respect
    `prefers-reduced-motion`.
  - Brand lime (`#ccff00`) is only for dark backgrounds or decoration, never
    text on white, because the contrast is too low.
- **No third-party requests.** Fonts and every other asset are self-hosted.
  This keeps visitor data from reaching other companies, which supports the
  no-cookie privacy promise.
- **SEO.**
  - Give every page a unique title and description, plus Open Graph tags with
    absolute URLs.
  - Add `hreflang` links (en, lv, x-default), `sitemap.xml` and `robots.txt`.
  - Add Organization JSON-LD with the legal name, VAT number, address, logo,
    email and founding date.
- **Security.**
  - Add a CloudFront response-headers policy with a strict CSP (`default-src
    'self'`, no inline script), HSTS, `nosniff`, a referrer policy and a
    permissions policy.
  - Keep the S3 bucket private and serve it only through CloudFront (origin
    access control).
- **Performance.** No frameworks, images as SVG where possible, and a small
  payload per page so it loads fast on mobile.
- **Languages.** Each language has its own page; nothing is translated by JS.
  Claude drafts the Latvian copy, and a native speaker reviews it before launch.
- **Deployment** to S3 and CloudFront, and its infrastructure as code, is a
  later phase.

## 6. Brand assets

Ready in `brand/`:

- `bixority-logo-dark.svg` and `bixority-logo-light.svg`: the full logo for
  dark and light backgrounds.
- `bixority-logo-greyscale-dark.svg` and `bixority-logo-greyscale-light.svg`:
  the same pair in greyscale. Each colour is replaced by the grey of equal
  luminance.
- `bixority-logo-dark-tight.svg`: the same dark logo without padding, used in
  the site header and footer. The logo always keeps its tagline in the
  original proportion and position; it is never stripped or re-set as
  separate text.
- `bixority-mark.svg`: the two chevrons on their own, for the favicon and app
  icon.

Logo colours: lime `#ccff00` → `#9ec600`, cyan `#00ccff` → `#00a9cf`, navy
`#001b35`. The site's text palette and typefaces are still to be agreed, and
will be proposed with the first page design.
