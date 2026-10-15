# VDL Public Site — GitHub Pages migration

Static, self-contained clone of the public **Virtual Distributed Laboratory** site
(`https://www.vdl.afrl.af.mil/`), built so it no longer depends on the contractor-run PHP server.

**Start here:** [docs/ANALYSIS.md](docs/ANALYSIS.md) covers the site map, what changes and why, the risks, and the decisions still open.

## Layout
```
capture/crawl.py       re-crawl the live site → capture/raw/*.html + capture/inventory.json
capture/assets/        vendored CSS/JS/images/PDFs (committed; the build never hits the old server)
build/build.py         snapshot → site/ (URL mapping, link rewriting, form replacement)
build/check_links.py   fails on any broken internal link
config.json            contacts, release URLs, banner and other program-office decisions
.github/workflows/     build + deploy to GitHub Pages on push to main
```

## Usage
```bash
make check         # build offline + link check
make serve         # http://localhost:8000
```

## Not in this repo
- The **restricted VDL** (accounts, CAC 2FA, CUI/ITAR community areas). GitHub.com is not authorized for it; see ANALYSIS §7.
- The IRENE-AE9/AP9/SPM release `.zip` (users request it by e-mail) and the 110 MB OAM video (the transcript and PDF remain). To add either later, upload it as a GitHub Release asset and list it in `config.json → release_assets`.
- Third-party copyrighted standards from ARSENL. These link to their publishers instead.
