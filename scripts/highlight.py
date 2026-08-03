#!/usr/bin/env python3
"""Emit deck-compatible syntax-highlight markup for a fenced code block.

The deck CSS styles five token classes: keyword, string, comment, number,
function. Writing those spans by hand is the dominant authoring cost (the
reference repo carries ~1,500 of them, all typed manually), and hand-editing
is where escaping bugs creep in.

Usage:
    highlight.py sql   < query.sql
    highlight.py json  < payload.json
    highlight.py python < producer.py
    echo 'SELECT 1' | highlight.py sql --pre

Design note: tokenising happens in ONE pass over a single alternation regex,
ordered comment -> string -> number -> keyword -> function. A single pass is
what keeps a keyword inside a string literal from being wrapped -- the naive
approach (a str.replace per keyword) corrupts any code whose strings or
comments contain keywords, which is most real code.
"""

from __future__ import annotations

import argparse
import html
import re
import sys

# Keywords are matched case-insensitively but emitted verbatim, so a deck can
# show lowercase SQL if the author prefers it.
KEYWORDS = {
    "sql": """
        select from where group by order having limit offset as on join inner
        left right full outer cross union all distinct create replace table
        view or and not null is in exists between like ilike case when then
        else end insert into values update set delete merge using matched
        cluster interactive warehouse target_lag initialization_warehouse
        alter add drop tables pipe copy data_source type match_by_column_name
        with recursive over partition row_number rank qualify cast try_cast
        primary key foreign references default comment if grant to role
        returns boolean varchar string number timestamp_ntz timestamp variant
        array object procedure function language execute immutable secure
        row access policy masking aggregation join_policy show describe
        current_timestamp current_date dateadd datediff sysdate coalesce
        greatest least sum count avg min max array_construct
    """,
    "json": "true false null",
    "python": """
        def class return if elif else for while in not and or is None True
        False import from as with try except finally raise yield lambda pass
        break continue global nonlocal assert async await del self
    """,
    "bash": """
        if then else elif fi for while do done case esac function return
        export local readonly source echo set unset trap exit
    """,
    "typescript": """
        const let var function return if else for while class extends
        implements interface type enum import export from as default new
        await async try catch finally throw typeof instanceof null undefined
        true false this super public private protected readonly static
    """,
    # YAML scalars only. Keys are matched structurally (identifier before a
    # colon), not by keyword list -- see the yamlkey group in build_pattern.
    "yaml": "true false null yes no on off",
}
KEYWORDS["js"] = KEYWORDS["typescript"]
KEYWORDS["ts"] = KEYWORDS["typescript"]
KEYWORDS["sh"] = KEYWORDS["bash"]
KEYWORDS["py"] = KEYWORDS["python"]
KEYWORDS["yml"] = KEYWORDS["yaml"]

# Per-language comment syntax. SQL also permits /* */, handled below.
LINE_COMMENT = {
    "sql": r"--[^\n]*",
    "python": r"#[^\n]*",
    "py": r"#[^\n]*",
    "bash": r"#[^\n]*",
    "sh": r"#[^\n]*",
    "typescript": r"//[^\n]*",
    "ts": r"//[^\n]*",
    "js": r"//[^\n]*",
    "yaml": r"#[^\n]*",
    "yml": r"#[^\n]*",
}
BLOCK_COMMENT = {
    "sql": r"/\*.*?\*/",
    "typescript": r"/\*.*?\*/",
    "ts": r"/\*.*?\*/",
    "js": r"/\*.*?\*/",
}


def build_pattern(lang: str) -> re.Pattern[str]:
    """Compose the single-pass alternation for a language.

    Order matters: whatever matches first wins, so comments and strings must
    precede keywords or a keyword inside them would be captured instead.
    """
    parts: list[str] = []

    if lang in BLOCK_COMMENT:
        parts.append(f"(?P<blockcomment>{BLOCK_COMMENT[lang]})")
    if lang in LINE_COMMENT:
        parts.append(f"(?P<comment>{LINE_COMMENT[lang]})")

    # Triple-quoted Python strings before the single-quote forms.
    if lang in ("python", "py"):
        parts.append(r"(?P<tripstring>'''.*?'''|\"\"\".*?\"\"\")")

    # Double- and single-quoted, honouring backslash escapes.
    parts.append(r"(?P<string>\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*')")

    # YAML keys are structural, not lexical: an identifier immediately followed
    # by a colon and then whitespace or end-of-line. This must precede the
    # keyword group, or a workflow's `on:` trigger would style as the boolean
    # `on` instead of a key. Requiring whitespace/EOL after the colon is what
    # keeps a URL like https://example.com from matching on its scheme.
    if lang in ("yaml", "yml"):
        parts.append(r"(?P<yamlkey>\b[A-Za-z_][A-Za-z0-9_.-]*(?=[ \t]*:(?:[ \t]|$)))")

    # Numbers, including decimals and negatives.
    parts.append(r"(?P<number>\b-?\d+(?:\.\d+)?\b)")

    words = KEYWORDS.get(lang, "").split()
    if words:
        alt = "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))
        parts.append(rf"(?P<keyword>\b(?:{alt})\b)")

    # A bare identifier immediately followed by '(' reads as a call.
    parts.append(r"(?P<function>\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\())")

    # MULTILINE so the YAML key lookahead's `$` means end-of-line, letting a key
    # with nothing after the colon (for example `steps:`) still match.
    return re.compile("|".join(parts), re.IGNORECASE | re.DOTALL | re.MULTILINE)


def highlight(code: str, lang: str) -> str:
    """Wrap tokens in deck span classes, HTML-escaping everything else."""
    pattern = build_pattern(lang)
    out: list[str] = []
    pos = 0

    # In SQL an identifier followed by '(' is usually a call -- but not when it
    # is the object being named. "CREATE TABLE foo (" would otherwise render the
    # table as a function, which is wrong on exactly the DDL slides that matter
    # most. Suppress the call styling when one of these precedes the identifier.
    NOT_CALLABLE_AFTER = {
        "table", "into", "from", "join", "update", "view", "warehouse",
        "pipe", "database", "schema", "stage", "policy", "procedure",
    }

    for match in pattern.finditer(code):
        kind = match.lastgroup
        if kind is None:
            continue
        # Escape the untouched run before this token. quote=False keeps literal
        # " and ' in the output: inside <pre> they need no entity, and raw
        # quotes match the reference markup and stay diff-friendly.
        out.append(html.escape(code[pos : match.start()], quote=False))
        text = html.escape(match.group(), quote=False)

        if kind == "function" and lang == "sql":
            preceding = code[: match.start()].rstrip().rsplit(None, 1)
            if preceding and preceding[-1].lower() in NOT_CALLABLE_AFTER:
                out.append(text)
                pos = match.end()
                continue

        # blockcomment and tripstring reuse the comment/string CSS classes.
        # yamlkey borrows the function class so keys read distinctly from the
        # scalar values beside them.
        css = {
            "blockcomment": "comment",
            "tripstring": "string",
            "yamlkey": "function",
        }.get(kind, kind)
        out.append(f'<span class="{css}">{text}</span>')
        pos = match.end()

    out.append(html.escape(code[pos:], quote=False))
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lang", help="sql | json | yaml | python | bash | typescript")
    ap.add_argument(
        "--pre",
        action="store_true",
        help='wrap output in <pre class="anim-fade">, ready to paste into a slide',
    )
    args = ap.parse_args()

    lang = args.lang.lower()
    if lang not in KEYWORDS:
        print(
            f"unknown language {lang!r}; known: {', '.join(sorted(KEYWORDS))}",
            file=sys.stderr,
        )
        return 2

    body = highlight(sys.stdin.read().rstrip("\n"), lang)
    print(f'<pre class="anim-fade">{body}</pre>' if args.pre else body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
