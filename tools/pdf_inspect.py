import sys
from pypdf import PdfReader

path = sys.argv[1]
r = PdfReader(path)
print(f"pages: {len(r.pages)}")
# Outline
def walk(items, depth=0):
    for it in items:
        if isinstance(it, list):
            walk(it, depth+1)
        else:
            try:
                pg = r.get_destination_page_number(it)
            except Exception:
                pg = "?"
            print(f"{'  '*depth}- p{pg}: {it.title}")
try:
    walk(r.outline)
except Exception as e:
    print(f"(no outline: {e})")

# Sample text from first few pages
for i in [0, 1, 2, 10, 50, 100]:
    if i < len(r.pages):
        t = r.pages[i].extract_text() or ""
        print(f"\n--- page {i} ({len(t)} chars) ---")
        print(t[:400])
