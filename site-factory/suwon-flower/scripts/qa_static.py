#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import sys

DIST = Path("dist")
EXPECTED_ORIGIN = os.environ.get("SITE_URL", "https://suwon.fwith.kr").rstrip("/")
PRIMARY_LANDING_SLUG = os.environ.get("PRIMARY_LANDING_SLUG", "").strip("/")
HERO_PATH = os.environ.get("HERO_PATH", "images/suwon/hero-B-original.png").strip("/")
INDEXABLE_ENV = os.environ.get("SITE_INDEXABLE")
PRODUCTION_MARKER = Path("production-indexing.enabled").exists()
INDEXABLE = (
    INDEXABLE_ENV.lower() == "true"
    if INDEXABLE_ENV is not None
    else PRODUCTION_MARKER
)
errors = []

REQUIRED_OG = [
    "og:type", "og:site_name", "og:title", "og:description",
    "og:url", "og:image", "og:image:alt",
]
REQUIRED_TWITTER = [
    "twitter:card", "twitter:title", "twitter:description",
    "twitter:image", "twitter:image:alt",
]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_depth = 0
        self.title_text = []
        self.meta_description = None
        self.meta_robots = None
        self.meta_names = {}
        self.meta_props = {}
        self.canonical = None
        self.h1_count = 0
        self.hrefs = []
        self.images = []
        self.json_ld_depth = 0
        self.json_ld_parts = []
        self.json_ld = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.title_depth += 1
        elif tag == "meta":
            name = a.get("name")
            prop = a.get("property")
            content = a.get("content", "").strip()
            if name:
                self.meta_names[name.lower()] = content
            if prop:
                self.meta_props[prop.lower()] = content
            if name == "description":
                self.meta_description = content
            elif name == "robots":
                self.meta_robots = content.lower()
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        elif tag == "img":
            self.images.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.json_ld_depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        elif tag == "script" and self.json_ld_depth:
            raw = "".join(self.json_ld_parts).strip()
            if raw:
                self.json_ld.append(raw)
            self.json_ld_parts = []
            self.json_ld_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title_text.append(data)
        if self.json_ld_depth:
            self.json_ld_parts.append(data)

def target_exists(href: str) -> bool:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return True
    path = parsed.path
    if not path.startswith("/"):
        return True
    if path == "/":
        return (DIST / "index.html").exists()
    rel = path.lstrip("/")
    direct = DIST / rel
    if direct.is_file():
        return True
    if path.endswith("/"):
        return (direct / "index.html").exists()
    return (DIST / rel / "index.html").exists() or (DIST / f"{rel}.html").exists()

html_files = sorted(DIST.rglob("*.html"))
if not html_files:
    errors.append("No HTML files generated.")

for file in html_files:
    parser = PageParser()
    text = file.read_text(encoding="utf-8")
    parser.feed(text)

    title = "".join(parser.title_text).strip()
    if not title:
        errors.append(f"{file}: missing <title>")
    if not parser.meta_description:
        errors.append(f"{file}: missing meta description")
    if parser.h1_count != 1:
        errors.append(f"{file}: expected exactly 1 H1, found {parser.h1_count}")
    if not parser.canonical:
        errors.append(f"{file}: missing canonical")
    elif not parser.canonical.startswith(EXPECTED_ORIGIN):
        errors.append(f"{file}: unexpected canonical {parser.canonical}")
    if "localhost" in text or "127.0.0.1" in text:
        errors.append(f"{file}: localhost reference remains in output")

    revision = parser.meta_names.get("site-factory-revision", "")
    if not revision:
        errors.append(f"{file}: missing site-factory-revision meta")

    for key in REQUIRED_OG:
        if not parser.meta_props.get(key):
            errors.append(f"{file}: missing {key}")
    for key in REQUIRED_TWITTER:
        if not parser.meta_names.get(key):
            errors.append(f"{file}: missing {key}")

    og_image = parser.meta_props.get("og:image", "")
    if og_image and not og_image.startswith(EXPECTED_ORIGIN):
        errors.append(f"{file}: og:image must use canonical origin: {og_image}")

    rel_file = file.relative_to(DIST).as_posix()
    is_404 = rel_file in ("404.html", "404/index.html")
    if is_404:
        if not parser.meta_robots or "noindex" not in parser.meta_robots:
            errors.append(f"{file}: 404 page must remain noindex")
    elif INDEXABLE:
        if not parser.meta_robots or "index,follow" not in parser.meta_robots:
            errors.append(f"{file}: production page must be index,follow")
        if parser.meta_robots and "noindex" in parser.meta_robots:
            errors.append(f"{file}: production page unexpectedly has noindex")
    else:
        if not parser.meta_robots or "noindex" not in parser.meta_robots:
            errors.append(f"{file}: test page must include robots noindex")

    for img in parser.images:
        if "alt" not in img or not img.get("alt", "").strip():
            errors.append(f"{file}: meaningful image missing non-empty alt: {img.get('src','')}")

    for raw in parser.json_ld:
        try:
            json.loads(raw)
        except json.JSONDecodeError as e:
            errors.append(f"{file}: invalid JSON-LD: {e}")
    if not parser.json_ld:
        errors.append(f"{file}: missing JSON-LD")

    for href in parser.hrefs:
        if not target_exists(href):
            errors.append(f"{file}: broken internal href {href}")

sitemap = DIST / "sitemap-index.xml"
if not sitemap.exists():
    errors.append("Missing sitemap-index.xml")
else:
    sm = sitemap.read_text(encoding="utf-8")
    if EXPECTED_ORIGIN not in sm:
        errors.append("Sitemap does not use expected production origin")

if PRIMARY_LANDING_SLUG:
    article = DIST / PRIMARY_LANDING_SLUG / "index.html"
    if not article.exists():
        errors.append(f"Approved top-level article output is missing: /{PRIMARY_LANDING_SLUG}/")

robots = DIST / "robots.txt"
if not robots.exists():
    errors.append("Missing robots.txt")
else:
    rt = robots.read_text(encoding="utf-8")
    if INDEXABLE:
        if "Allow: /" not in rt:
            errors.append("Production robots.txt must allow crawling")
        if "Disallow: /" in rt:
            errors.append("Production robots.txt must not disallow the entire site")
        if f"Sitemap: {EXPECTED_ORIGIN}/sitemap-index.xml" not in rt:
            errors.append("Production robots.txt sitemap URL mismatch")
    else:
        if "Disallow: /" not in rt:
            errors.append("Test robots.txt must disallow crawling")

if not (DIST / "favicon.svg").exists():
    errors.append("Missing favicon.svg")

required_product_images = [
    "funeral-basic.webp", "funeral-premium.webp", "funeral-large.webp", "funeral-xl.webp",
    "congrats-basic.jpg", "congrats-premium.jpg", "congrats-large.jpg", "congrats-xl.jpg",
]
for name in required_product_images:
    if not (DIST / "images" / "products" / name).exists():
        errors.append(f"Missing product image: {name}")

hero = DIST / HERO_PATH
if not hero.exists():
    errors.append(f"Missing original B hero image: /{HERO_PATH}")
else:
    size = hero.stat().st_size
    if size < 1_000_000:
        errors.append(f"Hero image appears over-compressed: {size} bytes")
    try:
        import struct
        with hero.open("rb") as fh:
            sig = fh.read(24)
        if sig[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append("Hero asset is not the expected PNG original")
        else:
            width, height = struct.unpack(">II", sig[16:24])
            if width < 1900 or height < 800:
                errors.append(f"Hero image resolution too small: {width}x{height}")
    except Exception as exc:
        errors.append(f"Could not validate hero image dimensions: {exc}")

if errors:
    print("\nSTATIC QA FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

mode = "INDEXABLE" if INDEXABLE else "NOINDEX TEST"
print(f"STATIC QA PASSED ({mode}): {len(html_files)} HTML files checked")
print("Canonical, title, description, H1, OG, Twitter, image ALT, JSON-LD, internal links, sitemap, robots, favicon, product assets and original-resolution hero verified.")
