#!/usr/bin/env python3
"""Generate the JSON-LD @graph for an article from its frontmatter.

Emits BlogPosting (or Article/NewsArticle via `schema_type`), a Person per author,
the publisher Organization, a WebPage and a BreadcrumbList. It never emits FAQPage
or HowTo: Google retired FAQ rich results in 2026 and HowTo before that, so the
markup earns nothing and adds a maintenance surface.

Usage: build_jsonld.py article.md > article.jsonld
"""
import json
import sys
import urllib.parse

sys.path.insert(0, __import__("os").path.dirname(__file__))
from frontmatter import read_article  # noqa: E402


def person(a):
    p = {"@type": "Person", "name": a.get("name")}
    for k in ("url", "jobTitle", "description"):
        if a.get(k):
            p[k] = a[k]
    if a.get("sameAs"):
        p["sameAs"] = a["sameAs"] if isinstance(a["sameAs"], list) else [a["sameAs"]]
    return p


def main():
    fm, body = read_article(sys.argv[1])
    url = fm.get("canonical_url") or ""
    pub = fm.get("publisher") or {}
    authors = fm.get("author")
    authors = authors if isinstance(authors, list) else [authors] if authors else []
    images = fm.get("images") or ([fm["image"]] if fm.get("image") else [])

    article = {
        "@type": fm.get("schema_type", "BlogPosting"),
        "@id": f"{url}#article",
        "headline": fm.get("title"),
        "description": fm.get("meta_description"),
        "datePublished": fm.get("date_published"),
        "dateModified": fm.get("date_modified") or fm.get("date_published"),
        "author": [person(a) for a in authors if isinstance(a, dict)],
        "publisher": {"@id": f"{pub.get('url', '')}#organization"} if pub else None,
        "mainEntityOfPage": {"@id": url},
        "image": images or None,
        "keywords": ", ".join([fm.get("primary_keyword", "")] + list(fm.get("secondary_keywords") or [])).strip(", ") or None,
        "inLanguage": fm.get("language", "en"),
    }
    if fm.get("reviewed_by"):
        article["reviewedBy"] = person(fm["reviewed_by"]) if isinstance(fm["reviewed_by"], dict) else fm["reviewed_by"]
    article = {k: v for k, v in article.items() if v not in (None, [], "")}

    graph = [article, {"@type": "WebPage", "@id": url, "url": url, "name": fm.get("title")}]
    if pub:
        org = {"@type": "Organization", "@id": f"{pub.get('url', '')}#organization", "name": pub.get("name"), "url": pub.get("url")}
        if pub.get("logo"):
            org["logo"] = {"@type": "ImageObject", "url": pub["logo"]}
        graph.append(org)

    crumbs = fm.get("breadcrumbs")
    if not crumbs and url:
        u = urllib.parse.urlparse(url)
        root = f"{u.scheme}://{u.netloc}"
        parts = [p for p in u.path.split("/") if p]
        crumbs = [{"name": "Home", "url": root + "/"}]
        acc = root
        for i, p in enumerate(parts):
            acc += "/" + p
            crumbs.append({"name": fm.get("title") if i == len(parts) - 1 else p.replace("-", " ").title(), "url": acc + ("/" if u.path.endswith("/") else "")})
    if crumbs:
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": c["name"], "item": c["url"]} for i, c in enumerate(crumbs)]})

    print(json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
