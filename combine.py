import json

def key_prefix(full_name: str) -> str:
    """Return the first two whitespace-separated tokens (≈ first + last)."""
    return " ".join(full_name.split()[:2])

# ------------------------------------------------------------------
# 1.  Load the three source files
# ------------------------------------------------------------------
with open("all_scholars.json", encoding="utf-8") as f:
    scholars = json.load(f)        # { full name → publications-text }

with open("CV.json", encoding="utf-8") as f:
    cvs = json.load(f)             # { full name → cv-text }

with open("web_data.json", encoding="utf-8") as f:
    web_pages = json.load(f)       # { full name → scraped-web-text }

# ------------------------------------------------------------------
# 2.  Start the merged dict with everything from all_scholars.json
# ------------------------------------------------------------------
merged = {name: pubs for name, pubs in scholars.items()}

# keep a lookup from “first two words” → canonical full name in `merged`
def build_prefix_map(d):
    return {key_prefix(n): n for n in d}

prefix_to_name = build_prefix_map(merged)

# ------------------------------------------------------------------
# 3.  Helper to merge any *additional* source (CVs, web pages, …)
# ------------------------------------------------------------------
def merge_source(source_dict: dict[str, str], label: str) -> None:
    """
    Append `source_dict` text into the correct entry in `merged`
    (matched by first+last name).  If the person is new, just add them.
    `label` is only for console feedback.
    """
    global prefix_to_name

    for src_name, src_txt in source_dict.items():
        p = key_prefix(src_name)

        if p in prefix_to_name:
            canon = prefix_to_name[p]
            merged[canon] = f"{merged[canon]}\n\n{src_txt}".strip()
        else:
            # brand-new person → add & update lookup table
            merged[src_name] = src_txt.strip()
            prefix_to_name[p] = src_name

    print(f"✓ merged {len(source_dict):>4} entries from {label}")

# ------------------------------------------------------------------
# 4.  Merge CVs, then web data
# ------------------------------------------------------------------
merge_source(cvs,       "CV.json")
merge_source(web_pages, "web_data.json")

# ------------------------------------------------------------------
# 5.  Write out the combined result
# ------------------------------------------------------------------
with open("combined.json", "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=4)

print(f"Final combined.json contains {len(merged)} people.")
