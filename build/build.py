#!/usr/bin/env python3
"""Turn the capture/ snapshot into a static site under site/ for GitHub Pages.

- Maps dynamic URLs (index.php?r=public/..., *.php) to static .html paths and
  rewrites every internal link to a relative path, so the site works at any
  base URL (user.github.io/repo/, a custom domain, or a local file server).
- Downloads the CSS/JS/images the pages reference (and, with --with-docs, the
  PDFs) from the live site into site/.
- Replaces server-side features (forms, logins, CSRF tokens, the consent dialog)
  with static equivalents driven by config.json.

Usage: python3 build/build.py [--with-docs] [--offline]
"""
import argparse, html, json, os, posixpath, re, shutil, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "www.vdl.afrl.af.mil"
BASE = f"https://{HOST}"
DOC_EXT = (".pdf", ".zip", ".mp4", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")
# Portal routes (Yii2 index.php?r=...) and their legacy camelCase aliases.
PORTAL_ROUTES = {
    "public/request_account": "public/request_account.html",
    "public/password_instruct": "public/password_instruct.html",
    "public/passwordInstruct": "public/password_instruct.html",
    "public/programs": "public/programs.html",
}
# Pages that only exist to serve a login/registration flow; they become redirects.
REDIRECT_PAGES = {
    "/programs/ae9ap9/public-login.php": "/programs/ae9ap9/downloads.php",
    "/programs/ae9ap9/vdl-login.php": "/programs/ae9ap9/downloads.php",
    "/programs/ae9ap9/register.php": "/programs/ae9ap9/downloads.php",
    "/programs/ae9ap9/reset-password.php": "/programs/ae9ap9/downloads.php",
    "/programs/oam": "/programs/oam/",
}


def page_out(url):
    """Static output path (relative to site/) for an internal page URL, or None."""
    p = urllib.parse.urlparse(url)
    if p.path == "/index.php" or (p.path == "/" and p.query):
        q = urllib.parse.parse_qs(p.query)
        route = q.get("r", [""])[0]
        if route == "public/page":
            return f"public/{q.get('view', ['index'])[0]}.html"
        return PORTAL_ROUTES.get(route)
    path = urllib.parse.unquote(p.path)
    if path.endswith("/"):
        return path.lstrip("/") + "index.html"
    if path.endswith(".php"):
        return path.lstrip("/")[:-4] + ".html"
    if "." not in path.rsplit("/", 1)[-1]:
        return path.lstrip("/") + "/index.html"
    return None


def asset_out(url):
    return urllib.parse.unquote(urllib.parse.urlparse(url).path).lstrip("/")


def rel(from_out, to_out):
    r = posixpath.relpath(to_out, posixpath.dirname(from_out) or ".")
    if r.endswith("index.html"):
        r = r[: -len("index.html")] or "./"
    return urllib.parse.quote(r, safe="/.#?=&-_~")


def curl_get(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sS", "-f", "-m", "300", "-A", "Mozilla/5.0 (VDL migration build)",
                        "-o", dest, urllib.parse.quote(url, safe=":/?&=%~+")], capture_output=True, text=True)
    return r.returncode == 0


class Builder:
    def __init__(self, args):
        self.args = args
        self.cfg = json.load(open(os.path.join(ROOT, "config.json")))
        self.inv = json.load(open(os.path.join(ROOT, "capture", "inventory.json")))
        self.out = os.path.join(ROOT, "site")
        self.cache = os.path.join(ROOT, "capture", "assets")  # committed: the build must not depend on the old server
        self.assets = set()
        self.out_of_scope = set()
        self.release = {BASE + k: self.cfg["release_base"] + v for k, v in self.cfg["release_assets"].items()}
        self.third_party = {BASE + k: v for k, v in self.cfg["third_party_overrides"].items()}
        self.missing = []
        # Optional: publish a single sub-site as the whole site (see config.json "scope").
        self.scope = self.cfg.get("scope") or {}
        self.root = self.scope.get("root", "").lstrip("/")

    def in_scope(self, url):
        if not self.root:
            return True
        p = urllib.parse.urlparse(url)
        if p.path.lstrip("/").startswith(self.root):
            return True
        q = urllib.parse.parse_qs(p.query)
        return q.get("r", [""])[0] == "public/page" and q.get("view", [""])[0] in self.scope.get("portal_pages", [])

    def scoped(self, out):
        if out and self.root and out.startswith(self.root):
            return out[len(self.root):]
        return out

    def page_out(self, url):
        p = urllib.parse.urlparse(url)
        if self.root and p.path in ("", "/") and not p.query:
            return "index.html"  # the portal home becomes the sub-site home
        return self.scoped(page_out(url)) if self.in_scope(url) else None

    # ---- link rewriting -------------------------------------------------
    def resolve(self, ref, base_url, from_out):
        raw = html.unescape(ref).strip()
        if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            return ref
        absu = urllib.parse.urljoin(base_url, raw)
        p = urllib.parse.urlparse(absu)
        if p.netloc != HOST:
            return ref
        frag = "#" + p.fragment if p.fragment else ""
        key = absu.split("#")[0]
        norm = urllib.parse.unquote(key)
        for table in (self.release, self.third_party):
            for k, v in table.items():
                if urllib.parse.unquote(k) == norm:
                    return html.escape(v)
        target = REDIRECT_PAGES.get(p.path, None)
        if target and not p.query:
            key = BASE + target
        if page_out(key):
            out = self.page_out(key)
            if out:
                return rel(from_out, out) + frag
            self.out_of_scope.add(key)
            return html.escape(key)
        a = self.scoped(asset_out(key))
        self.assets.add((key.split("?")[0], a))
        return rel(from_out, a) + frag

    def rewrite_attrs(self, text, base_url, from_out):
        def sub(m):
            return f'{m.group(1)}="{self.resolve(m.group(3), base_url, from_out)}"'
        return re.sub(r'\b(href|src|action)\s*=\s*(["\'])(.*?)\2', sub, text, flags=re.I | re.S)

    def rewrite_css(self, css, css_url, css_out):
        def sub(m):
            ref = m.group(2)
            if ref.startswith("data:"):
                return m.group(0)
            return f'url("{self.resolve(ref, css_url, css_out)}")'
        return re.sub(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', sub, css)

    # ---- server-side feature replacement --------------------------------
    def mailing_list_block(self, name, email):
        subj = urllib.parse.quote(f"REGISTER FOR {name}")
        body = urllib.parse.quote("Name:\nOrganization:\nAddress:\nTelephone:\nE-mail:\n")
        return (f'<div class="static-form-replacement"><p>To be placed on the mailing list, e-mail '
                f'<a href="mailto:{email}?subject={subj}&amp;body={body}">{email}</a> with the subject '
                f'<strong>REGISTER FOR {name}</strong> and include your name, organization, mailing address, '
                f'telephone number and e-mail address.</p></div>')

    def replace_forms(self, text, url):
        path = urllib.parse.urlparse(url).path
        c = self.cfg
        def form(repl):
            return re.sub(r"<form\b.*?</form>", repl, text, count=1, flags=re.S | re.I)
        if path == "/atrwg/":
            return form(self.mailing_list_block("ATRWG", c["contacts"]["atrwg"]))
        if path == "/tap/":
            return form(self.mailing_list_block("TAP", c["contacts"]["tap"]))
        if path.endswith("/oam/contact_us.php"):
            e = c["contacts"]["oam"]
            body = urllib.parse.quote("Name:\nOrganization:\nPhone:\nGovernment sponsor (name, e-mail, phone):\nQuestion/comments:\n")
            return form(f'<div class="static-form-replacement"><p>E-mail <a href="mailto:{e}?subject=OAM%20inquiry&amp;body={body}">{e}</a> '
                        f'with your name, organization, phone, your Government sponsor\'s contact information, and your question.</p></div>')
        if "request_account" in url:
            target = c.get("account_request_url")
            link = (f'<a class="btn btn-primary" href="{html.escape(target)}">Continue to account request</a>' if target
                    else f'To request an account, contact <a href="mailto:{c["help_email"]}">{c["help_email"]}</a> or {c["help_phone"]}.')
            return form(f'<p class="buttonblock">{link}</p>')
        return text

    def ae9_downloads(self, text):
        if "IRENE_V1.58.001.zip" in self.cfg["release_assets"].values():
            zip_url = self.cfg["release_base"] + "IRENE_V1.58.001.zip"
            block = (f'<div class="static-form-replacement"><p><a class="btn btn-primary" href="{zip_url}">'
                     f'Download IRENE-AE9/AP9/SPM V1.58.001 (Windows, .zip)</a></p></div>')
        else:
            e = self.cfg["contacts"]["ae9ap9"]
            block = (f'<div class="static-form-replacement"><p>To obtain the V1.58.001 distribution package, e-mail '
                     f'<a href="mailto:{e}?subject=IRENE-AE9%2FAP9%2FSPM%20V1.58.001%20download%20request">{e}</a>.</p></div>')
        # The live page offers three login paths; a Distribution A release needs none of them.
        return re.sub(r"<p><strong>Login options:</strong></p>\s*<div class=\"loginBlock\">.*?(?=</dd>)", block,
                      text, count=1, flags=re.S)

    def clean(self, text, url):
        text = re.sub(r'<meta name="csrf-(param|token)"[^>]*>\s*', "", text)
        text = re.sub(r'<input type="hidden" name="_csrf"[^>]*>', "", text)
        text = re.sub(r"<!--\s*<div class=\"publicFooterId\">.*?-->", "", text, flags=re.S)
        text = re.sub(r"<!--\[if[^\]]*\]>.*?<!\[endif\]-->", "", text, flags=re.S)  # IE7/8 shims (404 on live)
        if not self.cfg["show_usg_consent_banner"]:
            text = re.sub(r'<div id="dialogNotice">.*?</div></div>', "", text, flags=re.S)
            text = re.sub(r"jQuery\('#dialogNotice'\)\.dialog\(.*?\}\}\);", "", text, flags=re.S)
        if self.cfg.get("site_notice"):
            text = text.replace('<div id="content">',
                                f'<div id="content"><div class="site-notice">{self.cfg["site_notice"]}</div>', 1)
        if self.root:
            text = re.sub(r'\s*<li>\s*<a href="[^"]*(?:r=public(?:%2F|/)(?:request_account|password_instruct|passwordInstruct|programs)'
                          r'|restricted\.vdl\.afrl\.af\.mil)[^"]*">.*?</a>\s*</li>', "", text, flags=re.S)
        text = self.replace_forms(text, url)
        if urllib.parse.urlparse(url).path.endswith("/ae9ap9/downloads.php"):
            text = self.ae9_downloads(text)
        if urllib.parse.urlparse(url).path.endswith("/oam/brochure.php") and \
                "oam-brochure.mp4" not in self.cfg["release_assets"].values():
            # Video not migrated; the transcript and PDF brochure on the same page carry the content.
            text = re.sub(r"<video\b.*?</video>", "", text, count=1, flags=re.S)
        return text

    # ---- build ----------------------------------------------------------
    def write(self, out, content, mode="w"):
        dest = os.path.join(self.out, out)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, mode) as f:
            f.write(content)

    def redirect_html(self, from_out, to_out):
        r = rel(from_out, to_out)
        return (f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={r}">'
                f'<link rel="canonical" href="{r}"><title>Redirecting…</title><a href="{r}">Continue</a>')

    def run(self):
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        built = {}
        for url, meta in self.inv["pages"].items():
            path = urllib.parse.urlparse(url).path
            if self.root and path in ("", "/"):
                continue  # portal home: only a link alias for the sub-site home
            out = self.page_out(url)
            if not out or out in built:
                continue
            if path in REDIRECT_PAGES:
                self.write(out, self.redirect_html(out, self.page_out(BASE + REDIRECT_PAGES[path])))
                built[out] = url
                continue
            text = open(os.path.join(ROOT, "capture", "raw", meta["raw"]), encoding="utf-8", errors="ignore").read()
            text = self.clean(text, url)
            text = self.rewrite_attrs(text, url, out)
            self.write(out, text)
            built[out] = url
        self.fetch_assets()
        self.write(".nojekyll", "")
        self.write("404.html", self.redirect_html("404.html", "index.html").replace("Redirecting…", "Page not found"))
        outs = [o for _, o in self.assets]
        assert len(outs) == len(set(outs)), "two assets map to the same output path"
        print(f"pages: {len(built)}  assets: {len(self.assets)}  missing: {len(self.missing)}")
        for u in sorted(self.out_of_scope):
            print("  links out of scope (left pointing at the live site):", u)
        for m in self.missing:
            print("  missing:", m)

    def fetch_assets(self):
        done = set()
        while True:
            todo = sorted(a for a in self.assets if a not in done)
            if not todo:
                break
            for url, out in todo:
                done.add((url, out))
                if out.lower().endswith(DOC_EXT) and not self.args.with_docs:
                    continue
                cached = os.path.join(self.cache, asset_out(url))
                if not os.path.exists(cached):
                    if self.args.offline or not curl_get(url, cached):
                        self.missing.append(url)
                        continue
                dest = os.path.join(self.out, out)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if out.endswith(".css"):
                    css = open(cached, encoding="utf-8", errors="ignore").read()
                    self.write(out, self.rewrite_css(css, url, out))  # may add more assets
                else:
                    shutil.copyfile(cached, dest)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-docs", action="store_true", help="also download PDFs and other documents (~400 MB)")
    ap.add_argument("--offline", action="store_true", help="use only capture/assets/, no network")
    Builder(ap.parse_args()).run()
