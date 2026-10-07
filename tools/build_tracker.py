"""Builds tracking/test-tracker.xlsx (questions, run scores, summary, prompt change log)."""
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
qs = json.loads((ROOT / "test" / "test_questions.json").read_text())

F = "Arial"
base = Font(name=F, size=10)
bold = Font(name=F, size=10, bold=True)
hdr_font = Font(name=F, size=10, bold=True, color="FFFFFF")
hdr_fill = PatternFill("solid", start_color="1F3864")
input_font = Font(name=F, size=10, color="0000FF")
link_font = Font(name=F, size=10, color="008000")
input_fill = PatternFill("solid", start_color="FFF9DB")
thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")

def header(ws, row, labels):
    for i, t in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=t)
        c.font, c.fill, c.border = hdr_font, hdr_fill, box
        c.alignment = Alignment(wrap_text=True, vertical="center")

def style_range(ws, rng, font=base, fill=None, fmt=None, align=wrap):
    for row in ws[rng]:
        for c in row:
            c.font, c.border, c.alignment = font, box, align
            if fill: c.fill = fill
            if fmt: c.number_format = fmt

wb = Workbook()

# ---------- Instructions ----------
ws = wb.active; ws.title = "Instructions"
lines = [
    ("Maintenance Knowledge Agent: test tracker", bold),
    ("", base),
    ("How to use", bold),
    ("1. Questions sheet: the 20 fixed test questions with expected answers. Do not edit them between runs.", base),
    ("2. Summary sheet: type a name for each run in the yellow cells (column A). The Runs sheet picks those names up.", base),
    ("3. Runs sheet: for each run and question, type 1 (yes) or 0 (no) in the three yellow score columns.", base),
    ("4. Summary updates by itself. Only runs you have fully scored show percentages.", base),
    ("5. Prompt Change Log sheet: log ONE change per version, then re-run all 20 questions.", base),
    ("", base),
    ("Scoring rules", bold),
    ("Answer correct = 1 if the answer matches the expected answer with no wrong or invented facts. For out-of-scope questions, 1 only if nothing was invented.", base),
    ("Source correct = 1 if it names the right document (and section if shown). For out-of-scope questions, 1 only if it cites NO source.", base),
    ("Refusal correct = 1 if it refused when it should (out-of-scope) AND did not refuse when the answer was in the documents.", base),
    ("Pass = all three are 1. Vague questions: a good clarifying question or safe pointer to the right document counts as correct.", base),
    ("", base),
    ("Colour legend", bold),
    ("Blue text on yellow = you type here.  Black = formula.  Green = pulled from another sheet.", base),
    ("", base),
    ("Rule: only quote numbers that came from a scored run in this file. Empty cells are not zeros.", bold),
]
for i, (t, f) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t); c.font = f
ws.column_dimensions["A"].width = 130

# ---------- Questions ----------
wq = wb.create_sheet("Questions")
header(wq, 1, ["ID", "Category", "Question", "Expected answer", "Expected source(s)", "Should refuse?"])
for r, q in enumerate(qs, 2):
    vals = [q["id"], q["category"], q["question"], q["expected_answer"],
            "; ".join(q["expected_sources"]) or "none", "Yes" if q["should_refuse"] else "No"]
    for c, v in enumerate(vals, 1):
        wq.cell(row=r, column=c, value=v)
style_range(wq, f"A2:F{len(qs)+1}")
for col, w in zip("ABCDEF", [7, 14, 50, 70, 24, 10]):
    wq.column_dimensions[col].width = w
wq.freeze_panes = "A2"

# ---------- Summary ----------
wsu = wb.create_sheet("Summary")
wsu["A1"] = "Results by run"; wsu["A1"].font = Font(name=F, size=12, bold=True)
wsu["A2"] = "Type run names in the yellow cells. Percentages appear once a run has fully scored questions."
wsu["A2"].font = base
header(wsu, 4, ["Run name", "What changed", "Questions scored", "Answer correct", "Source correct", "Refusal correct", "Overall pass"])
run_names = [("Baseline (Copilot v1)", "Instructions from agent-instructions-v1-baseline.md, unchanged"),
             ("Copilot v2", ""), ("Copilot v3", ""), ("Copilot v4", ""),
             ("Python prototype", "TF-IDF top 3 + Claude, python-prototype/")]
N_RUNS, NQ = len(run_names), len(qs)
last = 1 + N_RUNS * NQ
R = lambda col: f"Runs!${col}$2:${col}${last}"
for i, (n, d) in enumerate(run_names):
    r = 5 + i
    wsu.cell(row=r, column=1, value=n); wsu.cell(row=r, column=2, value=d)
    wsu.cell(row=r, column=3, value=f'=COUNTIFS({R("A")},$A{r},{R("G")},">=0")')
    for col, src in zip("DEF", "DEF"):
        wsu[f"{col}{r}"] = f'=IF($C{r}=0,"",COUNTIFS({R("A")},$A{r},{R(src)},1)/$C{r})'
    wsu[f"G{r}"] = f'=IF($C{r}=0,"",COUNTIFS({R("A")},$A{r},{R("G")},1)/$C{r})'
e = 4 + N_RUNS
style_range(wsu, f"A5:B{e}", font=input_font, fill=input_fill)
style_range(wsu, f"C5:C{e}", fmt="0")
style_range(wsu, f"D5:G{e}", fmt="0%")

c0 = e + 3
wsu.cell(row=c0 - 1, column=1, value="Overall pass rate by question category").font = bold
cats = ["direct", "multi_doc", "vague", "out_of_scope"]
header(wsu, c0, ["Run name"] + cats)
for i in range(N_RUNS):
    r = c0 + 1 + i
    wsu.cell(row=r, column=1, value=f"=$A{5+i}")
    for j, cat in enumerate(cats):
        col = "BCDE"[j]
        wsu[f"{col}{r}"] = (f'=IF(COUNTIFS({R("A")},$A{r},{R("C")},{col}${c0},{R("G")},">=0")=0,"",'
                            f'COUNTIFS({R("A")},$A{r},{R("C")},{col}${c0},{R("G")},1)/'
                            f'COUNTIFS({R("A")},$A{r},{R("C")},{col}${c0},{R("G")},">=0"))')
style_range(wsu, f"A{c0+1}:A{c0+N_RUNS}")
style_range(wsu, f"B{c0+1}:E{c0+N_RUNS}", fmt="0%")
for col, w in zip("ABCDEFG", [26, 52, 16, 16, 16, 16, 16]):
    wsu.column_dimensions[col].width = w

# ---------- Runs ----------
wr = wb.create_sheet("Runs")
header(wr, 1, ["Run", "Question ID", "Category", "Answer correct (1/0)", "Source correct (1/0)",
               "Refusal correct (1/0)", "Pass", "Notes (what the agent actually said)"])
row = 2
for i in range(N_RUNS):
    for q in qs:
        wr.cell(row=row, column=1, value=f"=Summary!$A${5+i}")
        wr.cell(row=row, column=2, value=q["id"])
        wr.cell(row=row, column=3, value=f"=INDEX(Questions!$B$2:$B${NQ+1},MATCH($B{row},Questions!$A$2:$A${NQ+1},0))")
        wr.cell(row=row, column=7, value=f'=IF(COUNT(D{row}:F{row})=3,IF(MIN(D{row}:F{row})=1,1,0),"")')
        row += 1
style_range(wr, f"A2:A{last}", font=link_font)
style_range(wr, f"B2:C{last}")
style_range(wr, f"D2:F{last}", font=input_font, fill=input_fill, align=Alignment(horizontal="center"))
style_range(wr, f"G2:G{last}", align=Alignment(horizontal="center"))
style_range(wr, f"H2:H{last}", font=input_font, fill=input_fill)
for r in range(2, last + 1):
    wr[f"C{r}"].font = link_font
dv = DataValidation(type="whole", operator="between", formula1="0", formula2="1", allow_blank=True,
                    showErrorMessage=True, errorTitle="Score", error="Enter 1 or 0")
wr.add_data_validation(dv); dv.add(f"D2:F{last}")
for col, w in zip("ABCDEFGH", [24, 11, 14, 14, 14, 14, 8, 60]):
    wr.column_dimensions[col].width = w
wr.freeze_panes = "D2"
wr.auto_filter.ref = f"A1:H{last}"

# ---------- Prompt Change Log ----------
wl = wb.create_sheet("Prompt Change Log")
header(wl, 1, ["Version", "Date", "Change made (ONE change per version)", "Failures it targets (question IDs)",
               "Overall pass (from Summary)", "What happened / what I learned"])
for i in range(N_RUNS):
    r = 2 + i
    wl.cell(row=r, column=1, value=f"=Summary!$A${5+i}")
    wl[f"E{r}"] = f'=IFERROR(INDEX(Summary!$G$5:$G${e},MATCH($A{r},Summary!$A$5:$A${e},0)),"")'
wl["C2"] = "None. Baseline instructions as written in agent-instructions-v1-baseline.md."
wl["D2"] = "n/a"
style_range(wl, f"A2:A{1+N_RUNS}", font=link_font)
style_range(wl, f"B2:D{1+N_RUNS}", font=input_font, fill=input_fill)
style_range(wl, f"E2:E{1+N_RUNS}", fmt="0%")
style_range(wl, f"F2:F{1+N_RUNS}", font=input_font, fill=input_fill)
ex = 3 + N_RUNS
wl.cell(row=ex, column=1, value="EXAMPLE (delete this row)")
wl.cell(row=ex, column=2, value="2026-10-14")
wl.cell(row=ex, column=3, value="Added the exact refusal sentence and the rule 'never answer from general knowledge'.")
wl.cell(row=ex, column=4, value="Q18, Q19, Q20")
wl.cell(row=ex, column=6, value="Describe which questions changed, and whether anything got worse.")
style_range(wl, f"A{ex}:F{ex}", font=Font(name=F, size=10, italic=True, color="7F7F7F"))
for col, w in zip("ABCDEF", [24, 12, 60, 24, 16, 60]):
    wl.column_dimensions[col].width = w
wl.freeze_panes = "A2"

out = ROOT / "tracking" / "test-tracker.xlsx"
wb.save(out); print("saved", out)
