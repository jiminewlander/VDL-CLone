#!/usr/bin/env python3
"""Snapshot the public VDL site (www.vdl.afrl.af.mil) for migration.

Crawls every public page reachable from the portal and the program sub-sites,
saves raw HTML under capture/raw/, and writes capture/inventory.json listing
pages, files (HEAD only: size/type) and outbound links.

Uses curl rather than urllib because the site is signed by DoD PKI, which the
macOS keychain trusts but Python's bundled CA store does not.

Usage: python3 capture/crawl.py [--out capture]
"""
import argparse, collections, datetime, hashlib, html, json, os, re, subprocess, tempfile, urllib.parse

HOST = "www.vdl.afrl.af.mil"
BASE = f"https://{HOST}"
SEEDS = [
    "/", "/index.php?r=public%2Frequest_account", "/index.php?r=public%2Fpassword_instruct",
    "/index.php?r=public%2Fprograms", "/index.php?r=public%2Fpage&view=contact",
    "/index.php?r=public%2Fpage&view=privacy", "/index.php?r=public%2Fpage&view=hyperlink",
    "/index.php?r=public%2Fpage&view=accessibility",
    "/programs/ae9ap9/", "/programs/arsenl/", "/programs/oam/", "/atrwg/", "/tap/",
    # Linked only from behind forms/redirects, so seed them explicitly.
    "/programs/ae9ap9/public-login.php", "/programs/ae9ap9/vdl-login.php",
    "/programs/ae9ap9/register.php", "/programs/ae9ap9/reset-password.php",
    "/programs/arsenl/gra.php",
]
CRAWL_PREFIXES = ("/programs/", "/atrwg/", "/tap/", "/index.php")
# Dynamic endpoints that stream binaries or redirect; record them, never GET them as pages.
HEAD_ONLY = ("get-video.php", "data_download", "handle-", "add-user.php", "_request.php")


def curl(url, head=False):
    hf, bf = tempfile.mktemp(), tempfile.mktemp()
    args = ["curl", "-sS", "-m", "90", "-A", "Mozilla/5.0 (VDL migration snapshot)", "-D", hf, "-o", bf, "-w", "%{http_code}"]
    if head:
        args.append("-I")
    r = subprocess.run(args + [url], capture_output=True, text=True)
    status = int(r.stdout.strip()) if r.stdout.strip().isdigit() else -1
    headers = {}
    if os.path.exists(hf):
        for line in open(hf, errors="ignore"):
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        os.remove(hf)
    body = b""
    if os.path.exists(bf):
        body = open(bf, "rb").read() if not head else b""
        os.remove(bf)
    return status, headers, body


def is_page(path):
    last = path.rsplit("/", 1)[-1]
    return path.endswith("/") or last.endswith((".php", ".html", ".htm")) or "." not in last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)

    queue = collections.deque(BASE + s for s in SEEDS)
    seen, pages, files = set(), {}, {}
    outbound = collections.defaultdict(set)
    while queue:
        url = queue.popleft().split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        path = urllib.parse.urlparse(url).path
        if not is_page(path) or any(h in url for h in HEAD_ONLY):
            st, h, _ = curl(url, head=True)
            files[url] = {"status": st, "type": h.get("content-type"), "bytes": h.get("content-length"),
                          "location": h.get("location")}
            continue
        st, h, body = curl(url)
        text = body.decode("utf-8", "ignore")
        name = hashlib.sha1(url.encode()).hexdigest()[:12] + ".html"
        open(os.path.join(raw, name), "wb").write(body)
        title = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
        asof = re.search(r"Current as of ([^<]+)", text)
        pages[url] = {
            "status": st, "raw": name, "bytes": len(body), "location": h.get("location"),
            "title": html.unescape(title.group(1).strip()) if title else "",
            "current_as_of": asof.group(1).strip() if asof else None,
            "forms": re.findall(r"<form[^>]*>", text, re.I),
        }
        if st in (301, 302) and h.get("location"):
            queue.append(urllib.parse.urljoin(url, h["location"]))
        for ref in re.findall(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', text, re.I):
            ref = html.unescape(ref).strip()
            if ref.startswith(("mailto:", "tel:", "javascript:")):
                outbound[ref].add(url)
                continue
            absu = urllib.parse.urljoin(url, ref)
            p = urllib.parse.urlparse(absu)
            if p.netloc != HOST:
                outbound[absu].add(url)
            elif p.path.startswith(CRAWL_PREFIXES) or p.path in ("", "/") or not is_page(p.path):
                queue.append(urllib.parse.quote(absu, safe=":/?&=%#~+"))
        print(f"{st} {url}")

    inv = {
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "pages": pages, "files": files, "outbound": {k: sorted(v) for k, v in sorted(outbound.items())},
    }
    json.dump(inv, open(os.path.join(a.out, "inventory.json"), "w"), indent=1)
    print(f"{len(pages)} pages, {len(files)} files, {len(outbound)} outbound links")


if __name__ == "__main__":
    main()
