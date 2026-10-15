#!/usr/bin/env python3
"""Verify every internal href/src in site/ resolves to a file. Documents skipped by
a no-docs build are reported separately, not as failures."""
import os, re, sys, urllib.parse
SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
DOC_EXT = (".pdf", ".zip", ".mp4", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")
# Referenced by the original CSS but also 404 on the live site; not regressions.
KNOWN_LIVE_BROKEN = {"icn_kill.png", "grid.png"}
broken, docs = [], set()
for dp, _, fs in os.walk(SITE):
    for f in fs:
        if not f.endswith((".html", ".css")):
            continue
        p = os.path.join(dp, f)
        s = re.sub(r"<!--.*?-->", "", open(p, encoding="utf-8", errors="ignore").read(), flags=re.S)
        refs = re.findall(r'(?:href|src)="([^"]+)"', s) + re.findall(r'url\("([^"]+)"\)', s)
        for r in refs:
            if re.match(r"^(https?:|mailto:|tel:|javascript:|data:|#)", r):
                continue
            t = urllib.parse.unquote(r.split("#")[0].split("?")[0])
            if not t:
                continue
            target = os.path.normpath(os.path.join(dp, t))
            if os.path.isdir(target):
                target = os.path.join(target, "index.html")
            name = os.path.basename(target)
            if name in KNOWN_LIVE_BROKEN or name.startswith(("ui-bg_", "ui-icons_")):
                continue
            if not os.path.exists(target):
                (docs.add(target) if target.lower().endswith(DOC_EXT) else broken.append((os.path.relpath(p, SITE), r)))
print(f"broken: {len(broken)}  documents not in this build: {len(docs)}")
for b in sorted(set(broken)):
    print("  ", *b)
sys.exit(1 if broken else 0)
