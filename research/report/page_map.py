"""Page map of report.pdf: where the Executive Summary, Section 1 and Section 2 start and end, and how full their last pages are.

Usage (pypdf is not in the project env): cd research && uv run --with pypdf python report/page_map.py [--pages 1-12]
The brief's limits: Executive Summary one paragraph (page 1); Section 1 "What Did I Try?" 2 to 5 pages; Section 2
"What Did I Learn?" 1 to 4 pages. Section 1 starts on p. 2, so it must end on p. 6 (floats included); Section 2 starts
after a \\clearpage and must end within 4 pages of its start.
"""
import pathlib, re, sys

import pypdf

PDF = pathlib.Path(__file__).resolve().parent / "report.pdf"
r = pypdf.PdfReader(str(PDF))
n = len(r.pages)
lo, hi = 1, min(n, 14)
if "--pages" in sys.argv:
    a, b = sys.argv[sys.argv.index("--pages") + 1].split("-")
    lo, hi = int(a), min(n, int(b))

def lines(i):
    return [l for l in r.pages[i].extract_text().splitlines() if l.strip()]

def header(ls):
    h = ls[0] if ls else ""
    m = re.search(r"(Executive Summary|\d What Did I (?:Try|Learn)\?|References|[A-E] [A-Z][^\n]*)$", h)
    return m.group(1) if m else h[-40:]

print(f"{PDF.name}: {n} pages")
first = {}
for i in range(lo - 1, hi):
    ls = lines(i)
    body = [l for l in ls[1:] if not re.fullmatch(r"\d+", l.strip())]
    h = header(ls)
    first.setdefault(h, i + 1)
    print(f"p.{i+1:>3} [{h}] {len(body):>3} text lines | first: {body[0][:70] if body else ''!r}")
    print(f"       last: {body[-1][:90] if body else ''!r}")
s1 = [p for p in range(1, n + 1) if "What Did I Try?" in (lines(p - 1)[0] if lines(p - 1) else "")]
s2 = [p for p in range(1, n + 1) if "What Did I Learn?" in (lines(p - 1)[0] if lines(p - 1) else "")]
s2 = [p for p in s2 if p <= 20]
s1 = [p for p in s1 if p <= 20]
if s1:
    k = max(s1) - min(s1) + 1
    print(f"Section 1 pages (running head 'What Did I Try?'): {min(s1)}-{max(s1)} = {k} pages; limit 5 (must end on p. 6) -> {'OK' if k <= 5 else 'OVER'}")
if s2:
    k = max(s2) - min(s2) + 1
    print(f"Section 2 pages (running head 'What Did I Learn?'): {min(s2)}-{max(s2)} = {k} pages; limit 4 -> {'OK' if k <= 4 else 'OVER'}")
