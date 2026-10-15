.PHONY: capture vendor-docs build check serve

capture:        ## Re-crawl the live site into capture/raw + inventory.json
	python3 capture/crawl.py

vendor-docs:    ## Download every PDF/document into capture/assets (~390 MB, one-time)
	python3 build/build.py --with-docs

build:          ## Build site/ from the committed snapshot only (what CI runs)
	python3 build/build.py --offline --with-docs

check: build    ## Fail on any broken internal link
	python3 build/check_links.py

serve: build
	python3 -m http.server 8000 -d site
