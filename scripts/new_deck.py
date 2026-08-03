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


def _split_repo_url(repo_url: str) -> tuple[str, str]:
    """Pull (owner, repo) out of a GitHub URL. Returns ("", "") if it isn't one."""
    m = re.match(
        r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", repo_url.rstrip("/")
    )
    if not m:
        return "", ""
    return m.group(1), m.group(2).removesuffix(".git")


def derive_home_url(repo_url: str) -> str:
    """github.com/OWNER/REPO -> OWNER.github.io/REPO/ (the Pages catalog root).

    Absolute rather than relative on purpose. A deck's whole value is being a
    single shareable file, and a relative '../../' resolves to a bare directory
    listing when the file is opened locally, where Jekyll isn't rendering the
    README into an index.
    """
    owner, repo = _split_repo_url(repo_url)
    if not owner:
        return "#"
    return f"https://{owner}.github.io/{repo}/"


def derive_home_label(repo_url: str) -> str:
    """snowflake-feature-decks -> Snowflake Feature Decks."""
    _, repo = _split_repo_url(repo_url)
    if not repo:
        return "All decks"
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", repo) if w)


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

    home_url = args.home_url or derive_home_url(args.repo_url)
    home_label = args.home_label or derive_home_label(args.repo_url)

    hero = f"""    <section class="slide hero" id="hero">
      <a class="breadcrumb" href="{home_url}">{home_label} &rsaquo;</a>
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
        .replace("{{HOME_URL}}", home_url)
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


def _check_home_links(html: str) -> list[str]:
    """Require both exits back to the catalog, and require them to agree.

    Two independent failure modes this catches. A deck retrofitted by hand can
    pick up the breadcrumb and miss the sidebar link (or vice versa). And a deck
    copied from a sibling can carry the *other* repo's catalog URL, which looks
    fine until a reader clicks it and lands in the wrong library.
    """
    problems: list[str] = []

    crumb = re.search(r'<a[^>]*class="breadcrumb"[^>]*href="([^"]+)"', html)
    sidebar = re.search(
        r'<a[^>]*class="github-link home-link"[^>]*href="([^"]+)"', html
    )

    if not crumb:
        problems.append('no hero breadcrumb (<a class="breadcrumb" href="...">)')
    if not sidebar:
        problems.append(
            'no sidebar catalog link (<a class="github-link home-link" href="...">)'
        )

    for label, m in (("breadcrumb", crumb), ("sidebar catalog link", sidebar)):
        if m and (m.group(1).startswith("#") or m.group(1) in ("", "{{HOME_URL}}")):
            problems.append(f"{label} href is not a real URL: {m.group(1)!r}")

    if crumb and sidebar and crumb.group(1) != sidebar.group(1):
        problems.append(
            f"breadcrumb and sidebar catalog link disagree: "
            f"{crumb.group(1)!r} vs {sidebar.group(1)!r}"
        )

    return problems


def _check_notes(deck: Path, slide_count: int) -> list[str]:
    """Validate the companion speaker-notes file, if one is present.

    Catches the failure mode where a scaffolded notes file is committed with the
    template prose intact, and where the notes drift out of sync with the deck's
    section count (which makes them useless mid-presentation).
    """
    notes = deck.with_name(f"{deck.stem}-speaker-notes.md")
    if not notes.exists():
        return [f"no speaker notes alongside deck (expected {notes.name})"]

    text = notes.read_text()
    problems: list[str] = []

    # Verbatim prose from templates/speaker-notes.md. Presence means the author
    # scaffolded the file and never replaced that block.
    boilerplate = [
        "Who this is for, what they should be able to do afterwards",
        "One bullet per point you'd actually say out loud.",
        "The one idea that makes the rest of the deck obvious",
        "Why this section exists in the arc.",
        "## Slide N: <Section Name>",
        "Keep one `## Slide N` block per",
        "https://docs.snowflake.com/en/...",
        "- *Q: ...*",
    ]
    for phrase in boilerplate:
        if phrase in text:
            problems.append(f"speaker notes still contain template text: {phrase[:48]!r}")

    for marker in LEAK_MARKERS:
        if marker in text:
            problems.append(f"speaker notes leaked content marker: {marker!r}")

    n_blocks = len(re.findall(r"^## Slide \d+", text, flags=re.M))
    if n_blocks and slide_count and n_blocks != slide_count:
        problems.append(
            f"speaker notes have {n_blocks} '## Slide N' blocks but the deck has "
            f"{slide_count} slides (notes and deck must stay in step)"
        )

    return problems


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

    # The companion speaker notes ship in the same commit and are just as public,
    # but nothing used to validate them. A scaffolded notes file with the template
    # prose still in it reached a public repo in Aug 2026 because --check only ever
    # looked at the HTML. Validate the pair, not just the deck.
    problems.extend(_check_notes(path, len(slide_ids)))

    # A deck gets shared as a bare URL, so it has to be self-locating: a reader who
    # lands mid-library needs a way back to the catalog to find the other decks.
    # Both exits are required -- the breadcrumb for readers who start at the top,
    # the sidebar link for readers who look for nav where nav lives.
    problems.extend(_check_home_links(html))

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
    ap.add_argument(
        "--home-url",
        default="",
        help="catalog/base URL for the 'All decks' link "
        "(default: derived from --repo-url as the GitHub Pages root)",
    )
    ap.add_argument(
        "--home-label",
        default="",
        help="breadcrumb text for the catalog link "
        "(default: derived from the repo name)",
    )
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
