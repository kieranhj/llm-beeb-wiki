import sys
from pypdf import PdfReader

pdf, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
r = PdfReader(pdf)
with open(out, "w", encoding="utf-8") as f:
    for i in range(start, min(end + 1, len(r.pages))):
        t = r.pages[i].extract_text() or ""
        f.write(f"\n===== PDF PAGE {i} =====\n")
        f.write(t)
print(f"wrote pages {start}-{end} -> {out} ({len(r.pages)} total in pdf)")
