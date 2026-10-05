"""Convert the prompt Markdown files in supporting/transcripts/ into LaTeX fragments in prompts/.

Each line becomes a paragraph; '## ' headings become bold; '- ' lines become bullets;
`code` becomes \\texttt{}; LaTeX specials are escaped. Run from the folder root:
    python supporting/code/md_prompts_to_tex.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "supporting" / "transcripts"
OUT = ROOT / "prompts"
OUT.mkdir(exist_ok=True)

UNI = {
    "–": "--", "—": "---", "−": "-", "≥": r"$\geq$", "≤": r"$\leq$",
    "±": r"$\pm$", "×": r"$\times$", "α": r"$\alpha$", "β": r"$\beta$",
    "λ": r"$\lambda$", "π": r"$\pi$", "Δ": r"$\Delta$", "≈": r"$\approx$",
    "’": "'", "‘": "`", "“": "``", "”": "''", "…": r"\ldots{}",
    " ": "~",
}
ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
       "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
       "<": r"\textless{}", ">": r"\textgreater{}"}


def esc(s: str) -> str:
    s = s.replace("R^2", "\x00RSQ\x00")
    s = "".join(ESC.get(c, c) for c in s)
    s = s.replace("\x00RSQ\x00", "$R^2$")
    for k, v in UNI.items():
        s = s.replace(k, v)
    # straight double quotes -> LaTeX quotes, toggling within the line
    out, open_q = [], True
    for c in s:
        if c == '"':
            out.append("``" if open_q else "''")
            open_q = not open_q
        else:
            out.append(c)
    return "".join(out)


def inline(s: str) -> str:
    parts = re.split(r"(`[^`]*`|\*\*[^*]+\*\*)", s)
    res = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            res.append(r"\texttt{" + esc(p[1:-1]) + "}")
        elif p.startswith("**") and p.endswith("**") and len(p) > 3:
            res.append(r"\textbf{" + esc(p[2:-2]) + "}")
        else:
            res.append(esc(p))
    return "".join(res)


def convert(md: str) -> str:
    lines = []
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            lines.append(r"\begin{ttfamily}\small" if in_code else r"\end{ttfamily}")
            continue
        if in_code:
            lines.append(esc(line) + r"\\")
            continue
        if not line.strip():
            lines.append(r"\medskip")
        elif line.startswith("## "):
            lines.append(r"\par\textbf{" + inline(line[3:]) + "}")
        elif line.startswith("- "):
            lines.append(r"\par\hangindent=1.2em\hangafter=1\noindent\textbullet~" + inline(line[2:]))
        elif line.startswith("> "):
            lines.append(r"\par\hangindent=1.2em\hangafter=0\noindent" + inline(line[2:]))
        else:
            lines.append(r"\par\noindent " + inline(line))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    n = 0
    for md in sorted(SRC.glob("D*/prompt*.md")):
        tag = md.parent.name.split("_")[0] + "_" + md.stem  # e.g. D1_prompt_1
        (OUT / f"{tag}.tex").write_text(convert(md.read_text(encoding="utf-8")), encoding="utf-8")
        n += 1
    print(f"wrote {n} fragments to {OUT}")
