# IRENE-AE9/AP9/SPM site — GitHub Pages migration (`ae9ap9-only` branch)

Static, self-contained clone of the **AE9/AP9/SPM** sub-site of the Virtual Distributed Laboratory
(`https://www.vdl.afrl.af.mil/programs/ae9ap9/`). It no longer depends on the contractor-run PHP server.

This branch contains **only** AE9/AP9 material. The AE9/AP9 home page is the site root. The only
other pages kept are the four footer notices every page links to (Contact, Privacy & Security,
External Link Disclaimer, Accessibility). The full VDL public-site clone, with all five programs,
is on `main`. Background and risks: [docs/ANALYSIS.md](docs/ANALYSIS.md).

## What changed from the live AE9/AP9 pages
- URLs are flattened: `/programs/ae9ap9/factsheet.php` → `/factsheet.html`.
- The header no longer links to VDL-wide items (Request Account, Reset Password, Public Programs, Restricted VDL).
- Downloading the software no longer needs a login. The Downloads page tells users to e-mail the AE9/AP9 team
  (`AFRL.RVBXR.AE9.AP9.Org.Mbx@us.af.mil`) for the V1.58.001 package. To serve it directly instead,
  upload the zip as a GitHub Release asset and list it under `release_assets` in `config.json`.
- The old login/registration/reset pages redirect to Downloads.

## Layout
```
capture/raw/, capture/inventory.json   snapshot of the AE9/AP9 pages (captured 14 Oct 2026)
capture/assets/                        the PDFs, CSS, JS and images those pages use
build/build.py                         snapshot → site/ (scope set in config.json "scope")
build/check_links.py                   fails on any broken internal link
.github/workflows/pages.yml            build + deploy to GitHub Pages
```

## Usage
```bash
make check   # build offline + link check
make serve   # http://localhost:8000
```
