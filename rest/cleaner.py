import json
import re

with open("wema_enhanced.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned = []

junk_phrases = [
    "Wema Bank. All Rights Reserved",
    "Get ALAT app on",
    "Useful Links",
    "Policies",
    "Help & Security",
    "Rates",
    "Contact",
    "©",
    "purpleconnect@wemabank.com",
    "Marina, Lagos",
    "Downloads",
    "Videos",
    "FAQ",
    "Our Products",
    "Career Opportunities",
]

for entry in data:
    text = entry.get("text", "")
    # remove junk sections
    for junk in junk_phrases:
        text = text.replace(junk, "")

    # remove excessive whitespace
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    # merge paragraphs for a more readable form
    paragraphs = [p.strip() for p in entry.get("paragraphs", []) if len(p.strip()) > 30]
    merged_text = "\n\n".join(paragraphs) if paragraphs else text

    cleaned.append({
        "url": entry["url"],
        "title": entry.get("title", ""),
        "meta_description": entry.get("meta_description", ""),
        "text": merged_text
    })

with open("wema_cleaned.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"✅ Cleaned {len(cleaned)} pages and saved to wema_cleaned.json")
