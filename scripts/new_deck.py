#!/usr/bin/env python3
"""Scaffold a new enablement deck, or check an existing one.

Scaffold:
    new_deck.py interactive-tables \\
        --title "Interactive Tables: Sub-Second Serving" \\
        --short "Interactive Tables" \\
        --repo-url https://github.com/owner/repo \\
        --sections "The Problem,Architecture,Setup,Limits,Takeaways"

Check (run before every push):
    new_deck.py --check path/to/deck.html

The check exists because the sidebar and the sections are two hand-maintained
lists that must agree. When they drift, scroll-spy silently stops highlighting
and a nav link scrolls nowhere -- a failure that looks like a CSS bug and wastes
time to trace. It also greps for the leak patterns that recur in generated
content (LLM trace envelopes, Python/JS sentinel tokens).
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "deck.html"
NOTES_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "speaker-notes.md"

# Void elements never take a closing tag, so they must not be pushed on the stack.
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _TagBalance(HTMLParser):
    """Report unclosed and mismatched tags.

    A deck is one hand-edited HTML file with no build step and no framework, so
    nothing else will catch a dropped </div>. The symptom is brutal and
    non-obvious: the browser auto-closes the element, every following section
    nests inside it, and the page renders with sections progressively indented
    or swallowed entirely. Cheap to detect here, expensive to debug visually.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        top, line = self.stack[-1]
        if top != tag:
            self.errors.append(
                f"line {self.getpos()[0]}: </{tag}> closes but innermost open "
                f"element is <{top}> from line {line}"
            )
        else:
            self.stack.pop()

# Substrings that should never reach a published deck. The trace markers come
# from Glean/agent responses; the sentinels come from Python/JS formatting bugs.
LEAK_MARKERS = [
    "chatId:", "agentTraceInfo:", "traceId:", "workflowRunId:",
    "workflowTraceId:", "startTimeMillis:", "messages[",
    "None%", "$None", "$NaN", "NaN%", ">None<", ">null<", ">undefined<",
    "If you want, I can", "Would you like me to",
]


def slug_to_id(name: str) -> str:
    """Turn a section title into a stable anchor id."""
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def scaffold(args: argparse.Namespace) -> int:
    # A deck repo may vendor this script purely as its CI guard (--check) without
    # carrying the templates. Fail with a pointer rather than a traceback.
    if not TEMPLATE.exists():
        print(
            f"cannot scaffold: template not found at {TEMPLATE}\n"
            "This copy of the script is the validator only. Scaffold a new deck from\n"
            "the enablement-html-deck skill, which owns templates/deck.html.",
            file=sys.stderr,
        )
        return 2

    root = Path(args.outdir) / args.slug / "presentations"
    root.mkdir(parents=True, exist_ok=True)

    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    if not sections:
        print("need at least one section", file=sys.stderr)
        return 2

    nav_links = "\n".join(
        f'      <a href="#{slug_to_id(s)}">{s}</a>' for s in sections
    )
    nav = (
        '    <div class="nav-section">\n'
        f'      <div class="nav-section-title">Contents</div>\n'
        f'      <a href="#hero">Overview</a>\n{nav_links}\n'
        "    </div>"
    )

    hero = f"""    <section class="slide hero" id="hero">
      <h1>{args.title}</h1>
      <p class="subtitle">One sentence a reader can repeat back.</p>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Metric</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Metric</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Metric</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Metric</div></div>
      </div>
    </section>"""

    body = [hero]
    for s in sections:
        body.append(
            f"""    <section class="slide" id="{slug_to_id(s)}">
      <h2>{s}</h2>
      <p style="margin-bottom: 1.5rem;">Framing line.</p>
      <div class="card-grid anim-fade">
        <div class="card"><h4>Point</h4><p>Detail.</p></div>
      </div>
    </section>"""
        )

    html = (
        TEMPLATE.read_text()
        .replace("{{TITLE}}", args.title)
        .replace("{{SHORT_TITLE}}", args.short or args.title)
        .replace("{{REPO_URL}}", args.repo_url)
        .replace("{{NAV}}", nav)
        .replace("{{SECTIONS}}", "\n\n".join(body))
    )

    deck = root / f"{args.slug}.html"
    deck.write_text(html)

    notes = root / f"{args.slug}-speaker-notes.md"
    if not notes.exists():
        notes.write_text(NOTES_TEMPLATE.read_text().replace("{{TITLE}}", args.title))

    print(f"created {deck}")
    print(f"created {notes}")
    print(f"\nnext: open {deck}")
    return 0


def check(path: Path) -> int:
    html = path.read_text()

    # Slides are nav targets; part dividers are visual breaks between arcs and are
    # intentionally not linked from the sidebar (the scroll-spy still tracks them,
    # via querySelectorAll('.slide, .part-divider')). Distinguish the two so a
    # divider is not reported as an unreachable section.
    slide_ids = set(
        re.findall(r'<section[^>]*\bclass="[^"]*\bslide\b[^"]*"[^>]*\sid="([^"]+)"', html)
    )
    divider_ids = set(
        re.findall(r'<section[^>]*\bclass="[^"]*\bpart-divider\b[^"]*"[^>]*\sid="([^"]+)"', html)
    )
    section_ids = slide_ids | divider_ids
    nav_hrefs = [h for h in re.findall(r'<a[^>]*href="#([^"]+)"', html) if h]

    problems: list[str] = []

    # Tag balance first: a dropped closing tag makes every other finding
    # unreliable, because sections end up nested inside each other.
    balance = _TagBalance()
    balance.feed(html)
    problems.extend(balance.errors[:10])
    for tag, line in balance.stack[:10]:
        problems.append(f"line {line}: <{tag}> is never closed")

    for href in nav_hrefs:
        if href not in section_ids:
            problems.append(f"nav link #{href} has no matching section id")

    linked = set(nav_hrefs)
    for sid in sorted(slide_ids - linked):
        problems.append(f"slide #{sid} is not reachable from the sidebar")

    # A divider with no id cannot be tracked by the scroll-spy, which is a real
    # (if cosmetic) defect worth surfacing.
    anon_dividers = html.count('<section class="part-divider"') - len(divider_ids)
    if anon_dividers > 0:
        problems.append(f"{anon_dividers} part-divider(s) missing an id (scroll-spy cannot track them)")

    if "{{" in html:
        leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", html)))
        if leftover:
            problems.append(f"unfilled placeholders: {', '.join(leftover)}")

    for marker in LEAK_MARKERS:
        if marker in html:
            problems.append(f"leaked content marker present: {marker!r}")

    # A deck with no fade classes renders, but nothing animates -- usually a
    # sign the author hand-wrote sections without copying from components.md.
    if "anim-fade" not in html:
        problems.append("no anim-fade elements found (scroll animation inert)")

    if problems:
        print(f"FAIL {path}")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(
        f"OK {path}  ({len(slide_ids)} slides, {len(divider_ids)} dividers, "
        f"{len(nav_hrefs)} nav links)"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", nargs="?", help="topic slug, e.g. interactive-tables")
    ap.add_argument("--title", default="", help="full deck title")
    ap.add_argument("--short", default="", help="sidebar heading")
    ap.add_argument("--repo-url", default="#", help="source link for the sidebar")
    ap.add_argument("--sections", default="", help="comma-separated section titles")
    ap.add_argument("--outdir", default=".", help="repo root (default: cwd)")
    ap.add_argument("--check", metavar="HTML", help="validate an existing deck")
    args = ap.parse_args()

    if args.check:
        return check(Path(args.check))

    if not args.slug or not args.title:
        ap.error("scaffolding needs a slug and --title (or use --check)")
    return scaffold(args)


if __name__ == "__main__":
    sys.exit(main())
