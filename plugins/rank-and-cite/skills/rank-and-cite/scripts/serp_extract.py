#!/usr/bin/env python3
"""Extract the structure of one competitor page so ten of them can be compared.

The agent fetches each top-10 URL with whatever it has (Firecrawl, TinyFish, a
WebFetch tool, curl) and saves raw HTML or Markdown. This script turns that file
into a compact JSON record. Parsing is local and stdlib-only, so the comparison
does not depend on which fetcher was available.

Usage:
  serp_extract.py <file.html|file.md> --url <source url> [--position N] > extract.json
  serp_extract.py --fetch <url> [--position N] > extract.json   # urllib fallback, may be blocked

Record: url, position, title, meta_description, h1, headings[{level,text}], questions,
word_count, tables, lists, images, images_missing_alt, numbers (stat density),
outbound_domains, schema_types, date_published, date_modified, author.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form", "template"}
STAT_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?\s?%|\$\s?\d[\d,.]*|\d[\d,.]*\s?(?:million|billion|k\b))", re.I)


class Extractor(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.stack = []
        self.skip_depth = 0
        self.text = []
        self.title = ""
        self.meta = ""
        self.headings = []
        self._h = None
        self.tables = self.lists = self.images = self.missing_alt = 0
        self.links = []
        self.ld = []
        self._ld = None
        self._in_title = False
        self.meta_dates = {}
        self.meta_author = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP:
            self.skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name in ("description", "og:description") and not self.meta:
                self.meta = a.get("content") or ""
            if name in ("article:published_time", "datepublished"):
                self.meta_dates["published"] = a.get("content")
            if name in ("article:modified_time", "og:updated_time", "datemodified"):
                self.meta_dates["modified"] = a.get("content")
            if name == "author":
                self.meta_author = a.get("content")
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._ld = []
        if re.fullmatch(r"h[1-6]", tag) and not self.skip_depth:
            self._h = [int(tag[1]), []]
        if self.skip_depth:
            return
        if tag == "table":
            self.tables += 1
        if tag in ("ul", "ol"):
            self.lists += 1
        if tag == "img":
            self.images += 1
            if not (a.get("alt") or "").strip():
                self.missing_alt += 1
        if tag == "a" and a.get("href"):
            self.links.append(urllib.parse.urljoin(self.base, a["href"]))
        if tag in ("p", "li", "br", "div", "td", "tr"):
            self.text.append(" ")

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.ld.append("".join(self._ld))
            self._ld = None
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if self._h and tag == f"h{self._h[0]}":
            t = re.sub(r"\s+", " ", "".join(self._h[1])).strip()
            if t:
                self.headings.append({"level": self._h[0], "text": t})
            self._h = None

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
            return
        if self._in_title:
            self.title += data
        if self._h:
            self._h[1].append(data)
        if not self.skip_depth:
            self.text.append(data)


def walk_ld(node, out):
    if isinstance(node, list):
        for n in node:
            walk_ld(n, out)
    elif isinstance(node, dict):
        t = node.get("@type")
        if t:
            out["types"].extend(t if isinstance(t, list) else [t])
        for k in ("datePublished", "dateModified"):
            if k in node and k not in out:
                out[k] = node[k]
        au = node.get("author")
        if au and "author" not in out:
            if isinstance(au, list):
                au = au[0] if au else None
            out["author"] = au.get("name") if isinstance(au, dict) else au
        for v in node.values():
            if isinstance(v, (list, dict)):
                walk_ld(v, out)


def from_html(raw, url):
    p = Extractor(url)
    p.feed(raw)
    text = re.sub(r"\s+", " ", "".join(p.text)).strip()
    ld = {"types": []}
    for block in p.ld:
        try:
            walk_ld(json.loads(block), ld)
        except json.JSONDecodeError:
            ld["types"].append("INVALID_JSON_LD")
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    out_domains = sorted({urllib.parse.urlparse(l).netloc.lower().removeprefix("www.") for l in p.links
                          if l.startswith("http") and urllib.parse.urlparse(l).netloc.lower().removeprefix("www.") != host})
    h1 = [h["text"] for h in p.headings if h["level"] == 1]
    return {
        "title": re.sub(r"\s+", " ", p.title).strip(), "meta_description": p.meta.strip(),
        "h1": h1[0] if h1 else None, "headings": [h for h in p.headings if h["level"] <= 3],
        "word_count": len(text.split()), "tables": p.tables, "lists": p.lists,
        "images": p.images, "images_missing_alt": p.missing_alt,
        "numbers": len(STAT_RE.findall(text)), "outbound_domains": out_domains,
        "schema_types": sorted(set(ld["types"])),
        "date_published": ld.get("datePublished") or p.meta_dates.get("published"),
        "date_modified": ld.get("dateModified") or p.meta_dates.get("modified"),
        "author": ld.get("author") or p.meta_author,
    }


def from_markdown(raw, url):
    headings, body = [], []
    tables = 0
    for line in raw.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            headings.append({"level": len(m.group(1)), "text": m.group(2).strip().strip("#").strip()})
        else:
            body.append(line)
            if re.match(r"^\s*\|?\s*:?-{3,}", line):
                tables += 1
    text = " ".join(body)
    links = re.findall(r"\]\((https?://[^)\s]+)", raw)
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    out_domains = sorted({urllib.parse.urlparse(l).netloc.lower().removeprefix("www.") for l in links} - {host})
    h1 = [h["text"] for h in headings if h["level"] == 1]
    images = re.findall(r"!\[([^\]]*)\]\(", raw)
    return {
        "title": h1[0] if h1 else None, "meta_description": None, "h1": h1[0] if h1 else None,
        "headings": [h for h in headings if h["level"] <= 3],
        "word_count": len(re.sub(r"[#*_>`|\-\[\]()]", " ", text).split()),
        "tables": tables, "lists": len(re.findall(r"^\s*(?:[-*]|\d+\.)\s", raw, re.M)),
        "images": len(images), "images_missing_alt": sum(1 for a in images if not a.strip()),
        "numbers": len(STAT_RE.findall(text)), "outbound_domains": out_domains,
        "schema_types": [], "date_published": None, "date_modified": None, "author": None,
        "note": "markdown input: schema, dates and meta are not visible; fetch HTML for those if they matter.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--url")
    ap.add_argument("--fetch")
    ap.add_argument("--position", type=int)
    a = ap.parse_args()
    url = a.fetch or a.url or ""
    if a.fetch:
        req = urllib.request.Request(a.fetch, headers={"User-Agent": "Mozilla/5.0 (compatible; rank-and-cite/0.1)"})
        try:
            raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        except Exception as e:  # make the failure legible instead of producing an empty record
            print(json.dumps({"url": url, "position": a.position, "error": f"fetch failed: {e}"}))
            sys.exit(1)
        is_html = True
    else:
        if not a.file:
            ap.error("give a file or --fetch <url>")
        raw = open(a.file, encoding="utf-8", errors="replace").read()
        is_html = bool(re.search(r"<html|<body|<h1|<p[\s>]", raw[:5000], re.I))
    rec = from_html(raw, url) if is_html else from_markdown(raw, url)
    if rec["word_count"] < 150:
        rec["warning"] = "under 150 words extracted: likely a blocked or JS-rendered page. Refetch with a rendering fetcher."
    rec["questions"] = [h["text"] for h in rec["headings"] if h["text"].rstrip().endswith("?")]
    print(json.dumps({"url": url, "position": a.position, **rec}, indent=2))


if __name__ == "__main__":
    main()
