"""Build Appendix A (Claude interactions) from the exchange folders.

Run:  cd /home/hashim/projects/GA/project/research && uv run python report/build_transcripts.py

For every exchange folder exchange/NN_* it reads prompt.md, claude_response.md, followup_prompt.md,
claude_followup_response.md, factcheck.md and evaluation.md (whichever exist) and writes
report/appendix_transcripts.tex:
  - prompts and replies go verbatim into lstlisting environments (line breaking on), after a disclosed
    non-ASCII to ASCII character map, so nothing is silently dropped by the T1 fonts;
  - the fact-check is excerpted verbatim (named sections only), plus a condensed verdict count for exchange 01;
  - the evaluation, which is my own prose, is typeset (a small Markdown subset converted to LaTeX).
Each file is read from the exchange folder or from report/transcripts_src/NN_<stem>.txt, whichever is newer (the .txt
copies carry texts saved before their .md files, or corrections to them); if neither exists a
visible "pending" line is written. Exchange 04 ran two rounds: transcripts_src/04_<stem>.txt keep round 1 verbatim,
and round 2 comes from the exchange folder or transcripts_src/04b_<stem>.txt (a folder file identical to its round-1
copy is still round 1 and is skipped).
Provenance: the replies come from chat sessions with Claude (Anthropic); the appendix states the session setup once
at the top.
"""
from __future__ import annotations

import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCH = ROOT / "exchange"
OUT = ROOT / "report" / "appendix_transcripts.tex"
SRC = ROOT / "report" / "transcripts_src"

# ----------------------------------------------------------------------------- character maps
SUPERSCRIPT = {"\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3", "\u2074": "4", "\u2075": "5",
               "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9", "\u207b": "-", "\u207a": "+"}
ASCII_MAP = {
    "\u2212": "-",      # minus sign
    "\u2013": "-",      # en dash
    "\u2014": "--",     # em dash (Claude text only)
    "\u2011": "-",      # non-breaking hyphen
    "\u0394": "Delta",  # capital delta
    "\u03c0": "pi", "\u03b1": "alpha", "\u03b2": "beta", "\u03b3": "gamma", "\u03c4": "tau",
    "\u03b5": "eps", "\u03a3": "Sigma", "\u03bb": "lambda", "\u03c3": "sigma", "\u03bc": "mu", "\u03c1": "rho",
    "\u00b7": "*",      # middle dot used as multiplication
    "\u00d7": "x",      # multiplication sign
    "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
    "\u2265": ">=", "\u2264": "<=", "\u2248": "~", "\u2260": "!=", "\u00b1": "+/-",
    "\u221a": "sqrt", "\u2026": "...", "\u2032": "'", "\u2033": "''",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u00a0": " ", "\u2009": " ", "\u202f": " ",
    "\u2022": "*", "\u2713": "[ok]", "\u2717": "[x]", "\u00e1": "a",
    "\u03a6": "Phi", "\u0302": "^", "\u2099": "n", "\u00f3": "o",
    **{chr(0x2080 + i): str(i) for i in range(10)},
}
LATEX_MAP = {
    "\u2212": "$-$", "\u2013": "--", "\u2014": "--", "\u2011": "-",
    "\u0394": r"$\Delta$", "\u03c0": r"$\pi$", "\u03b1": r"$\alpha$", "\u03b2": r"$\beta$", "\u03b3": r"$\gamma$",
    "\u03c4": r"$\tau$", "\u03b5": r"$\varepsilon$", "\u03a3": r"$\Sigma$", "\u03bb": r"$\lambda$",
    "\u03c3": r"$\sigma$", "\u03bc": r"$\mu$", "\u03c1": r"$\rho$",
    "\u00b7": r"$\cdot$", "\u00d7": r"$\times$", "\u2192": r"$\rightarrow$", "\u2190": r"$\leftarrow$",
    "\u2265": r"$\geq$", "\u2264": r"$\leq$", "\u2248": r"$\approx$", "\u2260": r"$\neq$", "\u00b1": r"$\pm$",
    "\u221a": r"$\surd$", "\u2026": r"\ldots{}", "\u2032": "'", "\u2018": "`", "\u2019": "'", "\u201c": "``",
    "\u201d": "''", "\u00a0": "~", "\u00e1": r"\'a", "\u2022": r"$\bullet$",
    "\u03a6": r"$\Phi$", "\u0302": r"\^{}", "\u2099": r"$_n$", "\u00f3": r"\'o",
    **{chr(0x2080 + i): f"$_{i}$" for i in range(10)},
}
UNMAPPED: dict[str, int] = {}


def _superscripts(text: str, latex: bool) -> str:
    pat = "[" + "".join(SUPERSCRIPT) + "]+"
    return re.sub(pat, lambda m: ("$^{" if latex else "^") + "".join(SUPERSCRIPT[c] for c in m.group(0))
                  + ("}$" if latex else ""), text)


def to_ascii(text: str) -> str:
    text = _superscripts(text, latex=False)
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in ASCII_MAP:
            out.append(ASCII_MAP[ch])
        else:
            base = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            UNMAPPED[ch] = UNMAPPED.get(ch, 0) + 1
            out.append(base if base else "?")
    return "".join(out).replace("\t", "    ")


LATEX_SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                 "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def latex_escape(text: str) -> str:
    return "".join(LATEX_SPECIAL.get(c, c) for c in text)


def to_latex_prose(text: str) -> str:
    """Escape, then map non-ASCII characters to LaTeX (used only for typeset prose)."""
    text = latex_escape(text)
    text = _superscripts(text, latex=True)
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in LATEX_MAP:
            out.append(LATEX_MAP[ch])
        else:
            UNMAPPED[ch] = UNMAPPED.get(ch, 0) + 1
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode() or "?")
    return "".join(out)


def inline_md(text: str) -> str:
    """Markdown inline subset -> LaTeX: `code`, **bold**, *italic*."""
    codes: list[str] = []

    def keep(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = to_latex_prose(text)
    text = re.sub(r'"([^"\n]+)"', r"``\1''", text)  # straight double quotes -> TeX quotes in typeset prose
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: r"\texttt{" + to_latex_prose(codes[int(m.group(1))]) + "}", text)
    return text


def md_to_latex(md: str, drop_title: bool = True) -> str:
    """Paragraphs, #-headings, '- ' bullets (one nesting level) and '1. ' lists."""
    lines = md.splitlines()
    if drop_title and lines and lines[0].startswith("# "):
        lines = lines[1:]
    out, para, stack = [], [], []

    def flush_para():
        if para:
            out.append(inline_md(" ".join(s.strip() for s in para)) + "\n")
            para.clear()

    def close_lists(to_depth=0):
        while len(stack) > to_depth:
            out.append(r"\end{" + stack.pop() + "}")

    for raw in lines:
        line = raw.rstrip()
        m_b = re.match(r"^(\s*)[-*] (.*)$", line)
        m_n = re.match(r"^(\s*)\d+\. (.*)$", line)
        if not line.strip():
            flush_para()
            continue
        if line.startswith("#"):
            flush_para()
            close_lists()
            title = line.lstrip("#").strip()
            out.append(r"\paragraph{" + inline_md(title) + "}")
            continue
        if m_b or m_n:
            flush_para()
            m = m_b or m_n
            depth = 1 + len(m.group(1)) // 2
            env = "itemize" if m_b else "enumerate"
            if len(stack) < depth:
                while len(stack) < depth:
                    stack.append(env)
                    out.append(r"\begin{" + env + "}")
            else:
                close_lists(depth)
                if stack and stack[-1] != env:
                    out.append(r"\end{" + stack.pop() + "}")
                    stack.append(env)
                    out.append(r"\begin{" + env + "}")
            out.append(r"\item " + inline_md(m.group(2)))
            continue
        if stack:
            # continuation of the last item
            out[-1] += " " + inline_md(line.strip())
            continue
        para.append(line)
    flush_para()
    close_lists()
    return "\n".join(out) + "\n"


def listing(text: str, style: str) -> str:
    body = to_ascii(text).rstrip("\n")
    assert "\\end{lstlisting}" not in body
    return "\\begin{lstlisting}[style=" + style + "]\n" + body + "\n\\end{lstlisting}\n"


def md_sections(md: str, wanted: list[str]) -> str:
    """Return the verbatim text of the '## ' sections whose headings start with any string in `wanted`."""
    parts = re.split(r"(?m)^(?=## )", md)
    keep = [p for p in parts if any(p.startswith("## " + w) for w in wanted)]
    return "\n".join(p.rstrip() + "\n" for p in keep)


def verdict_counts(md: str) -> str:
    """Condensed claims table for exchange 01: verdict counts by claims-table subsection."""
    sec = md_sections(md, ["Claims table"])
    rows, cur = [], None
    counts: dict[str, dict[str, int]] = {}
    for line in sec.splitlines():
        if line.startswith("### "):
            cur = line[4:].strip()
            counts[cur] = {"C": 0, "P": 0, "W": 0, "U": 0}
        elif cur and re.match(r"^\|\s*\d+\s*\|", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            v = cells[2] if len(cells) > 2 else ""
            if v in counts[cur]:
                counts[cur][v] += 1
    tot = {k: sum(c[k] for c in counts.values()) for k in "CPWU"}
    for name, c in counts.items():
        rows.append(f"{to_latex_prose(name)} & {c['C']} & {c['P']} & {c['W']} & {c['U']} & {sum(c.values())} \\\\")
    rows.append(r"\midrule")
    rows.append(f"All claims & {tot['C']} & {tot['P']} & {tot['W']} & {tot['U']} & {sum(tot.values())} \\\\")
    return ("\\begin{table}[H]\\centering\\small\n\\caption{Exchange 01 fact-check, verdict counts by section of the "
            "reply (C correct, P partly correct, W wrong, U unverifiable). Counted from the fact-check's claims "
            "table.}\\label{tab:a1counts}\n"
            "\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nSection of the reply & C & P & W & U & Total \\\\\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}\n")


# ----------------------------------------------------------------------------- per-exchange content
BOXES = {
    "01": [
        ("Asked", "A skeptical design review of the halfway strategy: at most six problems ranked by impact on the "
                  "verdict, a ranking of the seven teammate proposals (A to G), exactly five falsifiable new ideas, a "
                  "plan, and the three assumptions it was least sure of."),
        ("Came back", "A 1,609-word review (cap 1,800); after I sent five corrections and a data fact, a 675-word follow-up (cap 600) with "
                      "one frozen rule for 1993--2009, a four-part pass bar and an attribution specification."),
        ("Verified", "52 checkable claims scored against the data (26 correct, 15 partly correct, 6 wrong, 5 "
                     "unverifiable); its proposed tests were run on seen data (checks c01 to c11), except idea 1 (kept for the frozen test), idea 4 (left to M4), idea 5 and proposal F."),
        ("Kept", "The always-short benchmark for every timing claim, the pre-registered test on 1994-03 to 2009-12 "
                 "(M8), and Aero and Ships as suspect Brown members (M4)."),
    ],
    "02": [
        ("Asked", "A pandas and statsmodels implementation of the frozen 1993--2009 test, one function per step with "
                  "docstrings, a fixed seed, every silent reading as a parameter, and pre-run checks with stop rules."),
        ("Came back", "A 985-line script with 25 numbered assumptions and 13 pre-run checks with stop rules; after a follow-up "
                      "naming six problems, six replaced functions, each with a unit test."),
        ("Verified", "Both versions run on the real data against my own implementation; with the two readings my prompt left open set to mine, "
                     "all 15 coefficients and all 5,000 shuffle draws agree to 3.3e-13; mutation tests of its "
                     "look-ahead audit."),
        ("Kept", "A second implementation that confirms the M8 verdict, and its null-seed harness, which showed that "
                 "the pre-registered NW(6) t over-rejects (13 of 100 seeds) while the shuffle is correctly sized."),
    ],
    "03": [
        ("Asked", "A robustness and multiple-testing framework that decides the final verdict: which test families to "
                  "correct and how, a deflated Sharpe specification with every input, at most two candidates with exact "
                  "pass bars, the one check most likely to overturn ``Do not implement'', a committee's remaining "
                  "objections, and a checklist of at most ten items."),
        ("Came back", "A framework of 1,716 words with its two tables (1,481 without them; cap 1,500), with a hand-computed deflated Sharpe table, two "
                      "candidates (the momentum optimizer book and the EPA-ranked spread) and a frozen pre-1970 run of "
                      "the book as the one decisive check."),
        ("Verified", "93 checkable claims scored against the module outputs (67 correct, 15 partly correct, 11 wrong); "
                     "all ten cells of its deflated Sharpe table reproduced to within 0.005; its power, holdout and "
                     "multiple-testing arithmetic rerun (checks fc03 and fc03b)."),
        ("Kept", "Families defined by the decision a test could change, the deflated appraisal ratio, Romano--Wolf "
                 "and superior predictive ability (SPA) tests over the searched strategies, a one-sided holdout reading against a worthwhile alpha, "
                 "and the frozen 1931--1969 run of the book, all implemented in M7; not its 155-row family, its post hoc "
                 "composite, its $\\pm$2\\% margin, its MCCC pass test, exchange-traded fund (ETF) proxies or its crash budget."),
    ],
    "04": [
        ("Asked", "Round 1: a red team of the draft summary and its claims (five weakest claims, at most four "
                  "alternatives with separating predictions, the case against ``Do not implement'' and its reversing "
                  "result, three edits, two least certain assumptions). Round 2: the same on the revised summary, now "
                  "with the best evidence against the verdict, at most three alternatives, and edits no longer than "
                  "the text they replace."),
        ("Came back", "Round 1: 1,340 words (cap 1,200) with a reversal test on the untimed EPA-ranked short. Round 2: "
                      "1,091 words (cap 1,000) arguing ``not proven'' rather than ``disproven'', with three alternatives "
                      "(wrong legs, direction-free regulation news, a crisis hedge) and three replacement texts."),
        ("Verified", "Every criticism checked against the module outputs, and the missing tests run (checks fc04 and "
                     "fc04b): holdout paths, intervals and timing, frozen-test power, a COVID bootstrap, the rules "
                     "rebuilt without each Brown industry, MCCC and CPU on EPA-ranked legs, a direction split of the "
                     "holdout entries, a crisis split of the timing gain, and our team's signal on both windows it was "
                     "not designed on."),
        ("Kept", "Thirteen summary rewordings, the holdout interval and timing loss, and three alternatives tested "
                 "and retired; not its edits as written, its cost comparison (the timing alpha is already net), its "
                 "one-industry reading of the holdout, or its case for capital in the momentum book."),
    ],
}
TITLES = {
    "01": "Exchange 01: idea generation (a design review of the halfway strategy)",
    "02": "Exchange 02: coding support (a second implementation of the frozen test)",
    "03": "Exchange 03: robustness design (the multiple-testing framework behind M7)",
    "04": "Exchange 04: red team of the draft report (two rounds)",
}
META = {  # used when an exchange has no interaction.md
    "03": "Date: 2026-09-26. Purpose: robustness design.",
    "04": "Date: 2026-09-26. Purpose: red team of the draft.",
}
SINGLE_ROUND = {"03", "04"}  # one prompt and one reply; no follow-up was sent
EARLIER_ROUNDS = {"04": "04"}  # exchange -> transcripts_src prefix of its round-1 files (kept verbatim)
SRC_TAG = {"04": "04b"}  # transcripts_src prefix of the current round's files, where it differs from the exchange number
FACTCHECK_SECTIONS = {
    "01": ["Summary", "Proposed tests that I ran", "What Claude missed"],
    "03": ["Summary"],
    "02": ["Summary", "6. Bug and issue list", "R2 Summary", "R2.9"],
}
ROLE = "Claude"
PARTS = [
    ("prompt.md", "Prompt (verbatim)", "prompt"),
    ("claude_response.md", f"Reply (verbatim; {ROLE})", "reply"),
    ("followup_prompt.md", "Follow-up prompt (verbatim)", "prompt"),
    ("claude_followup_response.md", f"Follow-up reply (verbatim; {ROLE})", "reply"),
]
PROVENANCE = (
    "\\paragraph{Provenance of the replies.} The prompts and replies below are verbatim from chat sessions with "
    "Claude (Anthropic). The chats had no file uploads, code execution or web access, so Claude saw only what a prompt "
    "contained (and, for a follow-up, the earlier turns) and could not compute anything on our data; every number it "
    "gave was checked with code. The exchange 02 follow-up was sent in a fresh chat, without the first reply. Two "
    "frozen tests took their design from these replies, the 1994--2009 rule of exchange 01 and the 1931--1969 run of "
    "exchange 03; both were fixed before they ran and cannot be re-drawn, because their windows have been spent.\n"
)


def source(num: str, folder: pathlib.Path | None, fname: str) -> pathlib.Path | None:
    """The newer of the exchange-folder file and report/transcripts_src/<tag>_<stem>.txt, or None if neither exists.

    For an exchange with an earlier round kept in transcripts_src, a folder file byte-identical to its round-1 copy
    is still round 1 (the new round has not been saved yet), so it is skipped."""
    stem = pathlib.Path(fname).stem
    cands = []
    if folder is not None and (folder / fname).exists():
        f = folder / fname
        r1 = SRC / f"{EARLIER_ROUNDS[num]}_{stem}.txt" if num in EARLIER_ROUNDS else None
        if not (r1 is not None and r1.exists() and r1.read_bytes() == f.read_bytes()):
            cands.append(f)
    alt = SRC / f"{SRC_TAG.get(num, num)}_{stem}.txt"
    if alt.exists():
        cands.append(alt)
    return max(cands, key=lambda q: q.stat().st_mtime) if cands else None


def tt(text: str) -> str:
    """Typewriter text that may break after underscores and slashes (long file names)."""
    return "\\texttt{" + latex_escape(text).replace("\\_", "\\_\\allowbreak{}").replace("/", "/\\allowbreak{}") + "}"


def shown(f: pathlib.Path, folder: pathlib.Path | None, fname: str) -> str:
    """Label of a typeset file: its name in the exchange folder, else the folder copy it equals (exchange round 2 is
    saved in round2/), else its own path, so that the label always names a file holding exactly the printed text."""
    if folder is not None:
        if f.parent == folder:
            return fname
        for cand in (folder / fname, folder / "round2" / fname):
            if cand.exists() and cand.read_bytes() == f.read_bytes():
                return cand.relative_to(folder).as_posix()
    return f.relative_to(ROOT).as_posix()


def counts(text: str) -> str:
    wc = len(text.split())
    words = sum(1 for w in text.split() if re.search(r"[A-Za-z0-9]", w))
    return f"{wc:,} words" + (f" ({words:,} excluding Markdown symbols)" if words != wc else "")


def box(items) -> str:
    rows = "\n".join(f"\\textbf{{{k}.}} & {v} \\\\" for k, v in items)
    return ("\\begin{center}\\fbox{\\begin{minipage}{0.95\\linewidth}\\small\n"
            "\\begin{tabularx}{\\linewidth}{@{}lX@{}}\n" + rows + "\n\\end{tabularx}\\end{minipage}}\\end{center}\n")


def meta_line(num: str, folder: pathlib.Path | None) -> str:
    inter = source(num, folder, "interaction.md")
    parts = []
    if inter is not None:
        head = inter.read_text(encoding="utf-8").splitlines()[:6]
        for h in head:
            if h.startswith("Tool:"):
                parts.append(f"Answered by: {ROLE} (see the provenance note).")
            elif h.startswith(("Date:", "Purpose:")):
                parts.append(to_latex_prose(h) + ("" if h.endswith(".") else "."))
    elif num in META:
        parts.append(f"Answered by: {ROLE} (see the provenance note). " + META[num])
    return " ".join(parts)


def exchange_block(num: str, folder: pathlib.Path | None) -> str:
    title = TITLES.get(num, f"Exchange {num}")
    s = [f"\\subsection{{{title}}}\\label{{app:ex{num}}}\n"]
    if source(num, folder, "prompt.md") is None:
        s.append("%% EXCHANGE-" + num + "-PENDING: rerun report/build_transcripts.py once exchange/" + num
                 + "_*/ holds prompt.md, claude_response.md and evaluation.md.\n")
        s.append("\\pending{this exchange had not been completed when this draft was built; rerunning the "
                 "transcript builder fills this subsection from the exchange folder.}\n")
        return "\n".join(s)
    rel = (folder.relative_to(ROOT).as_posix() if folder is not None else f"exchange/{num}_*")
    s.append(f"Files: {tt(rel + '/')}. " + meta_line(num, folder) + "\n")
    if num in BOXES:
        s.append(box(BOXES[num]))
    rnd = ""
    if num in EARLIER_ROUNDS:  # round 1, kept verbatim in report/transcripts_src/NN_*.txt
        tag = EARLIER_ROUNDS[num]
        s.append("\\paragraph{Round 1, on the first draft} Kept verbatim in " + tt("report/transcripts_src/") + ".\n")
        ev1 = SRC / f"{tag}_evaluation.txt"
        s.append("\\paragraph{My evaluation of round 1}\n")
        s.append("\\begin{quote}\\small\n" + md_to_latex(ev1.read_text(encoding="utf-8")) + "\\end{quote}\n")
        for stem, label, style in (("prompt", "Round 1 prompt (verbatim)", "transcript"),
                                   ("claude_response", f"Round 1 reply (verbatim; {ROLE})", "transcriptsmall")):
            text = (SRC / f"{tag}_{stem}.txt").read_text(encoding="utf-8")
            s.append(f"{{\\raggedright\\paragraph{{{label}}} {tt(tag + '_' + stem + '.txt')}, {counts(text)}.\\par}}\n")
            s.append(listing(text, style))
        s.append("\\paragraph{Round 2, on the revised draft} The prompt sent the revised summary and the best evidence "
                 "against it.\n")
        rnd = "Round 2 "
    ev = source(num, folder, "evaluation.md")
    if ev is not None:
        s.append("\\paragraph{My evaluation" + (" of round 2" if rnd else "") + "}\n")
        s.append("\\begin{quote}\\small\n" + md_to_latex(ev.read_text(encoding="utf-8")) + "\\end{quote}\n")
    for fname, label, style in PARTS:
        if rnd:
            label = rnd + label[0].lower() + label[1:]
        f = source(num, folder, fname)
        if f is None:
            if num in SINGLE_ROUND and "followup" in fname:
                continue
            s.append(f"\\paragraph{{{label}}} \\pending{{File \\texttt{{{latex_escape(fname)}}} not present yet.}}\n")
            continue
        text = f.read_text(encoding="utf-8")
        s.append(f"{{\\raggedright\\paragraph{{{label}}} {tt(shown(f, folder, fname))}, {counts(text)}.\\par}}\n")
        s.append(listing(text, "transcript" if style == "prompt" else "transcriptsmall"))
    if num in SINGLE_ROUND and source(num, folder, "followup_prompt.md") is None:
        s.append("Each round was one prompt and one reply; no follow-up was sent.\n" if num in EARLIER_ROUNDS
                 else "This exchange had one round: no follow-up prompt was sent.\n")
    fc = source(num, folder, "factcheck.md")
    if fc is not None:
        md = fc.read_text(encoding="utf-8")
        wanted = FACTCHECK_SECTIONS.get(num, ["Summary"])
        s.append("\\paragraph{Fact-check (verbatim excerpt)} " + ("Sections " if len(wanted) > 1 else "Section ")
                 + ", ".join("``" + to_latex_prose(w) + "''" for w in wanted)
                 + f" of {tt(shown(fc, folder, 'factcheck.md'))} ({len(md.split()):,} words in full).\n")
        if num == "01":
            s.append(verdict_counts(md))
        s.append(listing(md_sections(md, wanted), "transcriptsmall"))
    elif folder is not None and (folder / "checks").is_dir():
        scripts = sorted(p.name for p in (folder / "checks").glob("*.py"))
        s.append("{\\raggedright\\paragraph{Fact-check} The check scripts are in " + tt(rel + "/checks/") + " ("
                 + ", ".join(tt(n) for n in scripts) + "), with their outputs in \\texttt{checks/out/}.\\par}\n")
    return "\n".join(s)


def main() -> None:
    folders = {p.name[:2]: p for p in sorted(EXCH.glob("[0-9][0-9]_*")) if p.is_dir()}
    nums = sorted(set(folders) | {"01", "02", "03", "04"})
    parts = [
        "% Generated by report/build_transcripts.py. Do not edit by hand; rerun the script instead.\n",
        PROVENANCE,
        "\\paragraph{Layout.} Each exchange opens with a four-line box and my evaluation, followed by the prompts and "
        "replies and the fact-check. Non-ASCII characters in the transcripts are mapped to ASCII so that no glyph is "
        "lost, and line breaks inside a listing are marked with an arrow. Word counts are \\texttt{wc}-style counts of "
        "the source file; where Markdown symbols (table bars, bullets) inflate that count, the count without them "
        "follows, and that is the count compared with a word cap.\n",
    ]
    for n in nums:
        parts.append(exchange_block(n, folders.get(n)))
    OUT.write_text("\n".join(parts), encoding="ascii", errors="strict")
    print("wrote", OUT, f"({OUT.stat().st_size:,} bytes)")
    if UNMAPPED:
        print("unmapped characters (NFKD fallback used):", UNMAPPED)


if __name__ == "__main__":
    main()
