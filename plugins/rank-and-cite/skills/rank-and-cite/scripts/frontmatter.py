"""Minimal YAML-subset frontmatter reader (stdlib only, so the skill installs anywhere).

Supports: `key: value`, quoted strings, `key:` followed by an indented mapping,
`key:` followed by `- item` lists (scalars or `- name: x` mappings), and inline
`[a, b]` lists. That covers the article frontmatter documented in references/output.md.
Anything fancier should be JSON in a `frontmatter.json` sidecar instead.
"""
import json
import re


def _scalar(v):
    v = v.strip()
    if v == "":
        return None
    if (v[0] == v[-1]) and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in v[1:-1].split(",") if x.strip()]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def parse(text):
    lines = [l.rstrip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    root, i = {}, 0

    def block(i, indent):
        # returns (value, next_i) for the block of lines indented > indent
        if i < len(lines) and lines[i].lstrip().startswith("- "):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith("- ") and _ind(lines[i]) > indent:
                item_ind = _ind(lines[i])
                content = lines[i].lstrip()[2:]
                if re.match(r"^[\w@.-]+:\s", content + " ") and not content.startswith("http"):
                    k, _, v = content.partition(":")
                    d = {k.strip(): _scalar(v)}
                    i += 1
                    while i < len(lines) and _ind(lines[i]) > item_ind and not lines[i].lstrip().startswith("- "):
                        k2, _, v2 = lines[i].strip().partition(":")
                        d[k2.strip()] = _scalar(v2)
                        i += 1
                    items.append(d)
                else:
                    items.append(_scalar(content))
                    i += 1
            return items, i
        d = {}
        while i < len(lines) and _ind(lines[i]) > indent:
            k, _, v = lines[i].strip().partition(":")
            cur = _ind(lines[i])
            i += 1
            if v.strip() == "" and i < len(lines) and _ind(lines[i]) > cur:
                d[k.strip()], i = block(i, cur)
            else:
                d[k.strip()] = _scalar(v)
        return d, i

    while i < len(lines):
        k, _, v = lines[i].partition(":")
        i += 1
        if v.strip() == "" and i < len(lines) and _ind(lines[i]) > 0:
            root[k.strip()], i = block(i, 0)
        else:
            root[k.strip()] = _scalar(v)
    return root


def _ind(line):
    return len(line) - len(line.lstrip())


def read_article(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if not m:
        return {}, raw
    fm_text, body = m.groups()
    try:
        fm = json.loads(fm_text)
    except json.JSONDecodeError:
        fm = parse(fm_text)
    return fm, body
