#!/usr/bin/env python3
"""Extract GKE release notes for a date window into reviewable markdown.

Downloads the official GKE release notes page (full history; the Atom feeds are
capped at 30 entries and can end before a 3-month window starts), keeps notes
whose date falls in the window, and drops cluster/node version-availability and
COS "Security updates" boilerplate, summarising version availability instead.

Read-only: one HTTPS GET to docs.cloud.google.com, files written only to --out.
The downloaded page is untrusted data; run with `python3 -I` and never execute
or import anything from --out.

Usage:
  python3 -I extract_release_notes.py --out DIR [--months 3 | --since YYYY-MM-DD]
                                      [--until YYYY-MM-DD] [--input page.html]
"""

import argparse
import calendar
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

PAGE_URL = "https://docs.cloud.google.com/kubernetes-engine/docs/release-notes"
MAX_BYTES = 32 * 1024 * 1024
LABEL_RE = re.compile(r"devsite-label-release-([a-z]+)")
H2_RE = re.compile(r'<h2 id="([A-Z][a-z]+_\d{2}_\d{4})"')
NOTE_SPLIT = '<div class="devsite-release-note">'
NOISE_TITLE_RE = re.compile(r"\b(version updates|security updates)\b", re.I)
VERSION_RE = re.compile(r"\b(1\.\d+)\.\d+-gke\.\d+(\+preview)?")


def months_back(day: dt.date, months: int) -> dt.date:
    idx = day.year * 12 + day.month - 1 - months
    year, month = divmod(idx, 12)
    month += 1
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


class TextConverter(HTMLParser):
    """Minimal HTML -> markdown: headings, lists, links, code, tables."""

    SKIP = {"script", "style"}

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.out: list[str] = []
        self.skip = 0
        self.list_depth = 0
        self.href: list[str | None] = []
        self.pre = False

    def _w(self, s: str):
        self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("h3", "h4", "h5"):
            self._w("\n\n" + "#" * (int(tag[1]) + 1) + " ")
        elif tag == "p":
            self._w("\n\n")
        elif tag in ("ul", "ol"):
            self.list_depth += 1
        elif tag == "li":
            self._w("\n" + "  " * (self.list_depth - 1) + "- ")
        elif tag == "br":
            self._w("\n")
        elif tag == "tr":
            self._w("\n| ")
        elif tag in ("td", "th"):
            pass
        elif tag == "code":
            self._w("`")
        elif tag in ("strong", "b"):
            self._w("**")
        elif tag == "a":
            href = a.get("href")
            if href and href.startswith("/"):
                href = "https://docs.cloud.google.com" + href
            self.href.append(href)
            self._w("[")
        elif tag == "pre":
            self.pre = True
            self._w("\n```\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in ("ul", "ol"):
            self.list_depth = max(0, self.list_depth - 1)
        elif tag in ("td", "th"):
            self._w(" | ")
        elif tag == "code":
            self._w("`")
        elif tag in ("strong", "b"):
            self._w("**")
        elif tag == "a":
            href = self.href.pop() if self.href else None
            self._w(f"]({href})" if href else "]")
        elif tag == "pre":
            self.pre = False
            self._w("\n```\n")

    def handle_data(self, data):
        if not self.skip:
            self._w(data if self.pre else re.sub(r"\s+", " ", data))

    def text(self) -> str:
        s = "".join(self.out)
        s = re.sub(r"\[\]\([^)]*\)", "", s)
        s = re.sub(r"[ \t]+\n", "\n", s)
        return re.sub(r"\n{3,}", "\n\n", s).strip()


def to_markdown(fragment: str) -> str:
    conv = TextConverter(PAGE_URL)
    conv.feed(fragment)
    conv.close()
    return conv.text()


def first_title(fragment: str, body_md: str) -> str:
    m = re.search(r"<h4[^>]*>(.*?)</h4>", fragment, re.S)
    if m:
        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
    flat = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body_md.split("\n", 1)[0])
    flat = re.sub(r"[#*`]", "", flat)
    return (flat[:117] + "...") if len(flat) > 120 else flat


def first_anchor(fragment: str, date_id: str) -> str:
    m = re.search(r'<h4 id="([^"]+)"', fragment)
    return f"{PAGE_URL}#{m.group(1) if m else date_id}"


def parse(page: str):
    heads = list(H2_RE.finditer(page))
    for i, h in enumerate(heads):
        date_id = h.group(1)
        day = dt.datetime.strptime(date_id, "%B_%d_%Y").date()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(page)
        section = page[h.end():end]
        for chunk in section.split(NOTE_SPLIT)[1:]:
            lm = LABEL_RE.search(chunk)
            label = lm.group(1) if lm else "unknown"
            body = chunk.split("</span>", 1)[1] if "</span>" in chunk else chunk
            md = to_markdown(body)
            yield {
                "date": day,
                "date_id": date_id,
                "label": label,
                "title": first_title(body, md),
                "url": first_anchor(body, date_id),
                "markdown": md,
            }


def load_page(path: str | None) -> tuple[str, str]:
    if path:
        data = Path(path).read_bytes()
        return data.decode("utf-8", "replace"), f"file:{path}"
    req = urllib.request.Request(PAGE_URL, headers={"User-Agent": "gke-release-notes-review/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https URL
        if resp.geturl().split("/")[2] != "docs.cloud.google.com":
            sys.exit(f"unexpected redirect target: {resp.geturl()}")
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        sys.exit("release notes page exceeds size limit")
    return data.decode("utf-8", "replace"), PAGE_URL


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="new or empty output directory")
    ap.add_argument("--months", type=int, default=3, help="window length in calendar months (default 3)")
    ap.add_argument("--since", help="window start YYYY-MM-DD (overrides --months)")
    ap.add_argument("--until", help="window end YYYY-MM-DD (default today)")
    ap.add_argument("--today", help="override today's date (testing)")
    ap.add_argument("--input", help="parse a saved page instead of downloading")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    until = dt.date.fromisoformat(args.until) if args.until else today
    since = dt.date.fromisoformat(args.since) if args.since else months_back(until, args.months)
    if since > until:
        sys.exit("--since is after --until")

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"--out must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    page, source = load_page(args.input)
    (out / "release-notes.html").write_text(page, encoding="utf-8")

    notes = list(parse(page))
    if not notes:
        sys.exit("no release notes parsed: page structure changed; inspect release-notes.html")
    dates = [n["date"] for n in notes]
    newest, oldest = max(dates), min(dates)
    if oldest > since:
        sys.exit(f"page history starts {oldest}, after window start {since}; coverage incomplete")
    if until - newest > dt.timedelta(days=45):
        print(f"WARNING: newest note is {newest}; page may be stale or truncated", file=sys.stderr)

    in_window = [n for n in notes if since <= n["date"] <= until]
    kept, dropped, versions = [], 0, {}
    for n in in_window:
        if NOISE_TITLE_RE.search(n["title"]):
            dropped += 1
            for m in VERSION_RE.finditer(n["markdown"]):
                v = versions.setdefault(m.group(1), {"first": n["date"], "last": n["date"], "preview": False})
                v["first"], v["last"] = min(v["first"], n["date"]), max(v["last"], n["date"])
                v["preview"] |= bool(m.group(2))
            continue
        kept.append(n)

    kept.sort(key=lambda n: (n["date"], n["label"]), reverse=True)
    labels: dict[str, int] = {}
    for n in kept:
        labels[n["label"]] = labels.get(n["label"], 0) + 1

    lines = [
        f"# GKE release notes {since} .. {until}",
        "",
        f"Source: {PAGE_URL} (fetched {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ})",
        f"Kept {len(kept)} notes; dropped {dropped} version-availability/COS security boilerplate blocks.",
        "",
    ]
    for n in kept:
        lines += [
            f"## {n['date']} [{n['label']}] {n['title']}",
            f"<{n['url']}>",
            "",
            n["markdown"],
            "",
        ]
    (out / "window-notes.md").write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "source": source,
        "sha256": hashlib.sha256(page.encode("utf-8")).hexdigest(),
        "window": {"since": str(since), "until": str(until)},
        "page_history": {"oldest": str(oldest), "newest": str(newest)},
        "notes_in_window": len(in_window),
        "notes_kept": len(kept),
        "boilerplate_dropped": dropped,
        "kept_by_label": dict(sorted(labels.items())),
        "minor_versions_seen_in_version_updates": {
            k: {"first": str(v["first"]), "last": str(v["last"]), "preview_seen": v["preview"]}
            for k, v in sorted(versions.items(), key=lambda kv: tuple(map(int, kv[0].split("."))))
        },
        "files": ["window-notes.md", "release-notes.html", "summary.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
