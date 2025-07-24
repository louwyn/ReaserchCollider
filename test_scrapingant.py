import json
import re
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import ScrapingAntLoader

# ------------------------------------------------------------------
# config
# ------------------------------------------------------------------
CSV_PATH  = "Data.csv"
OUT_PATH  = "web_data.json"
API_KEY   = "cd2d9aca82fc4ce08088958e5ddefa1b"   # ScrapingAnt key

URL_RE = re.compile(
    r"""(?xi)
      (https?://[^\s,)]+)                     # full URL
      | (//[^\s,)]+)                          # scheme-less //
      | ((?<!@)(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s,)]*)?)   # bare domain
    """
)

def extract_urls(text: str) -> list[str]:
    hits = [next(s for s in tup if s) for tup in URL_RE.findall(text)]
    fixed = []
    for u in hits:
        u = u.rstrip(").,];")
        if u.startswith("//"):
            u = "https:" + u
        elif not u.startswith("http"):
            u = "https://" + u
        fixed.append(u)
    return list(dict.fromkeys(fixed))          # dedupe, keep order

# ------------------------------------------------------------------
# read CSV & scrape row-by-row
# ------------------------------------------------------------------
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip().str.lower().str.replace(":", "", regex=False)

first_col = next(c for c in df.columns if "first name" in c)
last_col  = next(c for c in df.columns if "last name"  in c)
url_cols  = [c for c in df.columns if any(k in c for k in ("webpage", "other"))]

output = {}

for _, row in df.iterrows():
    fullname = f"{row.get(first_col, '')} {row.get(last_col, '')}".strip()
    if not fullname:
        continue

    urls = extract_urls(" ".join(str(row.get(c, "")) for c in url_cols))
    if not urls:
        output[fullname] = ""
        continue

    loader     = ScrapingAntLoader(urls, api_key=API_KEY, continue_on_failure=True)
    documents  = loader.load()
    page_texts = [doc.page_content for doc in documents]

    output[fullname] = "\n\n".join(page_texts)

# ------------------------------------------------------------------
# save to JSON
# ------------------------------------------------------------------
Path(OUT_PATH).write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
print(f"Saved scraped data → {OUT_PATH}")
