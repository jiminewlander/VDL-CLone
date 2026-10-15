# VDL Public Site — Analysis and Migration Plan

Snapshot taken 14 Oct 2026 from `https://www.vdl.afrl.af.mil/` (public, unauthenticated pages only).
Machine-readable inventory: [`capture/inventory.json`](../capture/inventory.json).

## 1. Bottom line

`www.vdl.afrl.af.mil` is **two different things**, and only one of them can move to GitHub:

| | What it is | Moves to GitHub? |
|---|---|---|
| **Public site** (this repo) | A thin portal (8 pages) plus 5 program sub-sites (~40 pages, ~150 documents, ~400 MB). Almost entirely static content. | **Yes** — as a static GitHub Pages site. Done in this repo. |
| **Restricted VDL** (`restricted.vdl.afrl.af.mil`) | The real "capability": user accounts with sponsor approval, CAC/YubiKey/ECA 2FA, annual recertification, "community" areas holding Distribution-limited, ITAR and CUI material. | **No.** GitHub.com / GitHub Pages is not authorized for CUI or ITAR data and has no CAC auth. Needs a DoD-accredited host (see §7). |

The public site's server-side features (account request, logins, mailing-list sign-ups, contact form) are all *front doors* to the restricted system or to e-mail. Each is replaced with a static equivalent below, but the account workflow itself must land somewhere that has an ATO.

## 2. Technology of the current site

- **Portal:** PHP **Yii2** app (`index.php?r=public/...` routes), Bootstrap, jQuery 3.6 + jQuery UI 1.12, CSRF tokens, session cookies, F5/BIG-IP cookie (`TS01…`), HSTS, `X-Frame-Options: deny`.
- **Program sub-sites:** hand-written PHP pages with shared header/footer includes and per-site CSS (`/programs/<name>/css/…`), plus a few PHP handlers (logins, forms, a video streamer, a gated download).
- **Consent banner:** USG Information System notice in a modal jQuery-UI dialog, sets `usgid_notice` cookie for 4 hours.
- `robots.txt` is empty; no sitemap.
- **Existing defects found:** ARSENL home (`/programs/arsenl/`, `index.php`) and `gra.php` return **HTTP 500** although they render content; IE7/IE8 CSS shims 404; jQuery-UI theme images and two icons 404. The clone fixes the 500s by being static; the 404 images are cosmetic and reproduced as-is.

## 3. Full site map

### 3.1 Portal (`/`)
| Page | Live URL | Clone path | Dynamic behavior → replacement |
|---|---|---|---|
| Home | `/` | `index.html` | Consent modal → configurable (`show_usg_consent_banner`) |
| Request Account (Rules of Behavior) | `index.php?r=public/request_account` | `public/request_account.html` | Agree/Disagree POST → link to `account_request_url` or help desk |
| Reset Password | `…public/password_instruct` (alias `passwordInstruct`) | `public/password_instruct.html` | static already |
| Public Programs | `…public/programs` | `public/programs.html` | Yii ListView (7 items) → static list |
| Contact Us | `…public/page&view=contact` | `public/contact.html` | static |
| Privacy & Security Notice | `…view=privacy` | `public/privacy.html` | static |
| External Link Disclaimer | `…view=hyperlink` | `public/hyperlink.html` | static |
| Accessibility & Contact Notice | `…view=accessibility` | `public/accessibility.html` | static |
| Restricted VDL | `https://restricted.vdl.afrl.af.mil/` | external link | **out of scope — see §7** |

### 3.2 Public Programs (7 listed)
| Program | Hosted on VDL? | Pages | Docs | Notes |
|---|---|---|---|---|
| **AE9/AP9/SPM** (IRENE radiation belt models, AFRL/RV) | Yes `/programs/ae9ap9/` | 25 | 138 PDFs, 387 MB | Largest by far. Software download gated by login (see §4). |
| **ARSENL** (Architectures, Standards & Engineering Library, AFMC) | Yes `/programs/arsenl/` | 4 | 5 PDFs, ~31 MB | 4 of 5 PDFs are third-party copyrighted standards (§5). |
| **ATRWG** (Automatic Target Recognition Working Group) | Yes `/atrwg/` | 1 | — | Mailing-list registration form; restricted area on `dle.afrl.af.mil`. |
| **OAM** (Open Architecture Mgmt — OMS / UCI) | Yes `/programs/oam/` | 5 | 2 PDFs + 110 MB MP4 | Contact form; video streamed via `php/get-video.php`. |
| **TAP** (Timed Attestation Process, RYWA) | Yes `/tap/` | 1 | — | Mailing-list registration form. |
| COMPASE | No — links to afrl.af.mil fact sheet | — | — | keep as external link |
| SDMS | No — separate site `sdms.afrl.af.mil` | — | — | keep as external link; separate migration if also contractor-run |

AE9/AP9 sub-pages: home, news, factsheet, quick reference, energy & spatial coverage, architecture, data sets, modes, time sampling, known issues, versions, future plans, best practices, radiation-belt missions factsheet, documents, technical documentation, tech doc report, validations, independent validations, downloads, team, DSX, DSX publications (+ 4 login/registration pages).

### 3.3 Server-side features inventory
| Feature | Where | Collects | Static replacement in clone |
|---|---|---|---|
| Account request (ROB acceptance → form) | portal | identity + sponsor | link to new account system (config) |
| AE9/AP9 public account login / register / reset | `ae9ap9/*.php` | name, company, address, country, phone, e-mail | **removed**; direct download of the Dist A release (config) |
| AE9/AP9 VDL-account login | `vdl-login.php` | VDL credentials | removed (same) |
| Gated download | `data_download/?file=IRENE_V1.58.001.zip` | — | **Not migrated.** E-mail request to the AE9/AP9 team |
| ATRWG / TAP mailing-list sign-up | `atrwg_request.php`, TAP form | name, address, phone, fax, e-mail | pre-filled `mailto:` to the list webmaster |
| OAM contact form | `oam_request.php` | name, org, phone, sponsor, comments | pre-filled `mailto:` |
| Video streaming | `oam/php/get-video.php` | — | **Not migrated (decision 14 Oct 2026).** Player removed; transcript and PDF brochure remain. Can be re-added as a Release asset. |
| Consent banner | all portal pages | cookie | optional, off by default |

## 4. Capture approach (what this repo does)

1. **`capture/crawl.py`** — breadth-first crawl from the portal and every sub-site, saving raw HTML (`capture/raw/`) and an inventory with HTTP status, title, "Current as of" date, forms, file sizes (HEAD only) and every outbound link. Login/handler endpoints are HEAD-only so nothing is submitted.
2. **`build/build.py`** — deterministic transform of the snapshot into `site/`:
   - maps `index.php?r=…` and `*.php` URLs to `.html` paths and rewrites all links to **relative** paths (works on `*.github.io/repo/`, a custom domain, or locally);
   - vendors CSS/JS/images (and with `--with-docs`, all documents) into `capture/assets/`, which is **committed**, so the site rebuilds after the old server is gone;
   - strips CSRF tokens, session IDs and IE shims; replaces every form per §3.3 using `config.json`.
3. **`build/check_links.py`** — fails CI on any broken internal link (current result: 0 broken).
4. **`.github/workflows/pages.yml`** — on push to `main`, builds offline and deploys to GitHub Pages.

Why a transform rather than `wget --mirror` or a rewrite into Jekyll/Hugo: it keeps the pages byte-for-byte faithful (lowest risk of altering approved, publicly released content), it is re-runnable if the live site changes before shutdown, and every deviation from the original is a reviewable line of code. Converting to a static-site generator for easier editing is a sensible **phase 2** once the archive is safe.

## 5. Risks and issues to resolve before publishing

1. **Public release review.** Content on the live site is already public, but re-publishing it under a new host/owner should go through your Public Affairs / OPSEC review. Most pages are stamped "Current as of" 2024–2025.
2. **Third-party copyrighted standards (ARSENL).** FACE 3.1 and SOSA 2.0 (The Open Group), the CoPaIS standard (IEEE-ISTO) and the REDHAWK SCA spec are not U.S. Government works. **Decision (14 Oct 2026): excluded.** Links point to the publishers (`third_party_overrides`; verify those URLs). The DoD SCA 4.1 spec stays.
3. **Non-government presentations (AE9/AP9).** Some conference decks are by non-USG authors (for example the ESA SAPPHIRE2S Industry Day deck). They are included only with `--with-docs`; have the AE9/AP9 team confirm redistribution rights before committing them.
4. **AE9/AP9 software licensing.** The Windows binary is Distribution A, but the page notes the source is © Atmospheric and Environmental Research, Inc. and may not be redistributed. Publish only the official release package as distributed today, with its license, and never source code. **Decision (14 Oct 2026):** the `.zip` (behind a login) is not migrated. The downloads page tells users to e-mail the AE9/AP9 team mailbox instead. To publish it later, add it to `release_assets` in `config.json`.
5. **Dropping AE9/AP9 registration** removes the download-usage statistics the team collected. Options: accept GitHub's release download counts (no PII, simpler) or keep an external registration form. Recommendation: download counts. Registration collected PII the old system held; that database's disposition is a records/privacy question for the contractor turnover.
6. **E-mail addresses on `@vdl.afrl.af.mil`** (help desk, ATRWG/TAP webmasters) will likely stop working when the contractor leaves. Point them at org mailboxes (`config.json → contacts`).
7. **USG consent banner.** It is required on DoD information systems. A public github.io page is not a DoD IS, and showing the banner there is misleading, so it is off by default. A `.mil` custom domain may change that — ask your ISSM.
8. **Domain.** To keep `www.vdl.afrl.af.mil` working, AFRL DNS needs a CNAME to GitHub Pages, which needs approval and isn't always permitted for `.mil`. Otherwise, add a redirect on the old host before shutdown so bookmarks and the many citations of AE9/AP9 URLs don't break.
9. **Size limits.** GitHub Pages: 1 GB site, 100 MB per file in git, soft 100 GB/month bandwidth. With the PDFs the site is about 400 MB, which fits. The MP4 and software zip go in Releases (2 GB per file).

## 6. Decisions needed (all are values in `config.json`)

| Key | Decision | Default |
|---|---|---|
| repo / `release_base` | GitHub org/repo name | placeholder `OWNER/REPO` |
| `account_request_url` | Where restricted-VDL account requests go after transition | help-desk e-mail |
| `help_email`, `help_phone`, `contacts.*` | Successor mailboxes and phone | current values |
| `show_usg_consent_banner` | Show the DoD notice? | `false` |
| `site_notice` | Optional "this site has moved / is archived" banner | none |
| `third_party_overrides` | Confirm publisher links | Open Group / IEEE-ISTO / REDHAWK |

## 7. Restricted VDL — the part GitHub cannot host

What the ROB page implies the restricted system does: per-person accounts with Government sponsor verification, U.S. citizenship gate, CAC/YubiKey/ECA 2FA, annual recertification, community/program areas (ATRWG's restricted site, ARSENL CUI/ITAR content, AE9/AP9 VDL-account downloads), "no PII" policy, separate classification domains.

Hosting options for an accredited successor:
- **Platform One / Party Bus** or **AFRL's own DoD cloud enclave** (IL4/IL5) for a custom app.
- **GitHub Enterprise Cloud with data residency / GitHub in an IL-authorized environment** for *code* collaboration only. Ask your ISSM which instance your organization is authorized to use for CUI.
- **DoD SAFE / DoD365 SharePoint (IL5)** as a quick stop-gap for document libraries per program.

Before the contractor leaves, get from them: the account database (with recertification dates and sponsors), a content export per community area with distribution markings, the ATRWG/TAP/OAM mailing lists, the AE9/AP9 registrant list and download logs, the IRENE release zip, and the server's ATO/security documentation.

## 8. Recommended sequence

1. ~~Capture all documents~~ **Done 14 Oct 2026:** 141 PDFs (391 MB) are in `capture/assets/`. Next, commit to a **private** repo.
2. Resolve the §5 items, fill in `config.json`.
3. Switch the repo to Pages.
4. Point the domain or set redirects; update the citations the AE9/AP9 team controls.
5. Separately, stand up the restricted-VDL successor (§7).
6. Phase 2: move content into Markdown with a static-site generator so program teams can edit pages through pull requests.
